from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    request_ids = fields.Many2many('purchase.request', string='Material Request')
    item_type = fields.Selection([('material', 'Material'), ('service', 'Service')], default="material", string='Item Type', required=True)

    PURCHASE_REQUISITION_STATES = [
        ('draft', 'Draft'),
        ('prm', 'Purchase Manager Approval'),
        ('finance', 'Finance Approval'),
        ('ceo', 'CEO Approval'),
        ('ongoing', 'Ongoing'),
        ('in_progress', 'Confirmed'),
        ('open', 'Bid Selection'),
        ('done', 'Closed'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')
    ]

    title = fields.Char()
    period = fields.Char()
    type_id = fields.Many2one('purchase.requisition.type', string="Agreement Type", required=True, default=False)
    tender_id = fields.Many2one('purchase.requisition', string="Tender")
    exclusive = fields.Selection([('exclusive', 'Exclusive'), ('multiple', 'Multiple')], related="type_id.exclusive")
    blanket_order_count = fields.Integer(compute='_compute__blanket_orders_number', string='Number of Blanket Orders')
    amount = fields.Monetary()
    approval_required = fields.Boolean(string="Approvals Required", related='type_id.approval_required')

    @api.onchange('request_ids')
    def _onchange_request_ids(self):
        if not self.request_ids:
            return

        self = self.with_company(self.company_id)
        request_ids = self.request_ids
        line_ids = []
        for request in request_ids:
            
            for line in request.line_ids:
                product = line.product_id
                fpos = self.env['account.fiscal.position']
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                    taxes_id = fpos.map_tax(
                        line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
                else:
                    taxes_id = fpos.map_tax(line.product_id.supplier_taxes_id)
                aacclount_anallytic_id = False
                account_analytic_id = False

                product_line = (0, 0, {'product_id': line.product_id.id,
                                   'product_uom_id': line.product_id.uom_po_id.id,
                                   'schedule_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                   'product_qty': line.qty_purchase,
                                   'qty_ordered': line.qty_purchase,
                                   })
                line_ids.append(product_line)
        self.line_ids.unlink()
        self.line_ids = line_ids

    def _compute__blanket_orders_number(self):
        self.ensure_one()
        blanket_orders = self.env['purchase.requisition'].search([('tender_id', '=', self.id)])
        self.blanket_order_count = len(blanket_orders)

    def make_purchase_requisition(self):
        view_id = self.env.ref('purchase_requisition.view_purchase_requisition_form')
        order_line = []
        type_id = self.env['purchase.requisition.type'].search([('exclusive', '=', 'multiple')], limit=1)

        for line in self.line_ids:
            product = line.product_id
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
            product_line = (0, 0, {'product_id': line.product_id.id,
                                   'product_uom_id': line.product_id.uom_po_id.id,
                                   'schedule_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                   'product_qty': line.product_qty,
                                   'qty_ordered': line.product_qty,
                                   })
            order_line.append(product_line)

        return {
            'name': _('New Purchase Agreement'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'context': {
                'default_line_ids': order_line,
                'default_tender_id': self.id,
                'default_type_id': type_id.id if type_id else False,
                'default_origin': self.name,
                'default_item_type': self.item_type,
                'default_request_ids': [self.request_ids]

            }
        }

    def action_blanket_order_list(self):
        return {
            'name': "Blanket Orders",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('tender_id', '=', self.id)],
        }

    def action_in_progress(self):
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.") % self.name)
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                # if requisition_line.price_unit <= 0.0:
                #     raise UserError(_('You cannot confirm the blanket order without price.'))
                # if requisition_line.product_qty <= 0.0:
                #     raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
            self.write({'state': 'ongoing'})
        else:
            self.write({'state': 'in_progress'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            if self.is_quantity_copy != 'none':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            else:
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')

    state = fields.Selection(PURCHASE_REQUISITION_STATES,
                             'Status', track_visibility='onchange', required=True,
                             copy=False, default='draft')
    state_blanket_order = fields.Selection(PURCHASE_REQUISITION_STATES, compute='_set_state')

    amount_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    reason_reject = fields.Text("Rejection Reason", track_visibility="onchange")

    @api.depends('state')
    def _set_state(self):
        self.ensure_one()
        self.state_blanket_order = self.state

    @api.depends('line_ids')
    def _compute_amount(self):
        total = 0
        for line in self.line_ids:
            total += line.price_unit * line.product_qty
        self.update({
            'amount_total': total
        })


    def action_submit(self):
        self.write({'state': 'prm'})

    def action_prm_approval(self):
        self.write({'state': 'finance'})

    def action_finance_approval(self):
        self.write({'state': 'ceo'})

    def action_ceo_approval(self):
        self.action_in_progress()

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    def action_draft(self):
        self.write({'state': 'draft'})


class PurchaseAgreementLine(models.Model):
    _inherit = "purchase.requisition.line"

    @api.constrains('product_qty', 'qty_ordered')
    def check_ordered_qty(self):
        if self.requisition_id.exclusive == 'exclusive':
            return
        if self.qty_ordered > self.product_qty:
            raise UserError("Ordered quantity should not exceed purchase agreement quantity.")

class PurchaseAggreementType(models.Model):
    _inherit = 'purchase.requisition.type'

    approval_required = fields.Boolean(string="Approvals Required", default=True)


class PurchaseRequisitionRejectionWizard(models.TransientModel):
    _name = "purchase.requisition.rejection.wizard"
    reason_reject = fields.Text("Rejection Reason")

    def action_validate(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        purchase = self.env['purchase.requisition'].browse(active_ids)
        order = self.env['purchase.requisition'].search([['id', '=', active_ids[0]]])
        if self.reason_reject:
            order.state = 'reject'
            order.reason_reject = self.reason_reject

        return {'type': 'ir.actions.act_window_close'}
