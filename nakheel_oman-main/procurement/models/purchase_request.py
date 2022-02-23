# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
from docutils.nodes import field
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError

_STATES = [
    ('draft', 'Draft'),
    ('line_approve', 'Waiting Line Manager Approval'),
    ('reject', 'Rejected'),
    ('cancel', 'Cancelled'),
    ('done', 'Done'),
    ('close', 'Closed'),
]


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Material Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    _order = 'name desc'

    name = fields.Char('MR Number', size=32, required=True, track_visibility='onchange', default="/")
    date_start = fields.Date('Request Date', help="Date when the user initiated the request.",
                             default=fields.Date.context_today, track_visibility='onchange')
    end_start = fields.Date('End date', default=fields.Date.context_today, track_visibility='onchange')
    schedule_date = fields.Date('Expected date', default=fields.Date.context_today, track_visibility='onchange')
    requested_by = fields.Many2one('res.users', 'Requested by', track_visibility='onchange',
                                   default=lambda self: self.get_requested_by(), store=True, readonly=True)
    assigned_to = fields.Many2one('res.users', 'Approver', track_visibility='onchange')
    description = fields.Html('Description')
    title = fields.Char()
    line_ids = fields.One2many('purchase.request.line', 'request_id', 'Products to Purchase', readonly=False, copy=True,
                               track_visibility='onchange')
    state = fields.Selection(selection=_STATES, string='Status', index=True, track_visibility='onchange', readonly=True,
                             required=True, copy=False, default='draft')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', domain=[('code', '=', 'internal')])
    picking_count = fields.Integer(string="Count", compute='compute_picking_count')
    service_count = fields.Integer(string="Count", compute='compute_picking_count')
    agreement_count = fields.Integer(string="Count", compute='compute_agreement_count')
    purchase_count = fields.Integer(string="Count", compute='compute_purchase_count')
    item_type = fields.Selection([('material', 'Material'), ('service', 'Service')], default="material",
                                 string='Item Type', required=True)
    department_id = fields.Many2one('hr.department', string='Department',
                                    default=lambda self: self._get_default_department())

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          default=lambda self: self._get_default_analytic_account())
    can_manager_approved = fields.Boolean(string='Can Manager approved')
    can_reject = fields.Boolean(string='Can reject')
    is_editable = fields.Boolean(string="Is editable", compute="_compute_is_editable", readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    amount_total = fields.Monetary('Total', compute='compute_totals', store=False)
    amount_total_purchase = fields.Monetary('Purchase Total', compute="compute_totals", store=False)
    purchase_method = fields.Selection([('deliver', 'Deliver'), ('purchase', 'Purchase'), ('both', 'Both')],
                                       compute="compute_purchase_method")
    budget_line_id = fields.Many2one('crossovered.budget.lines', string="Budget")
    over_budget = fields.Boolean(default=False, copy=False)
    amount_budget_reserved = fields.Monetary("Reserved Budget Amount", compute="compute_budget_reserved_amount")
    priority = fields.Selection([('reqular', 'Regular'), ('urgent', 'Urgent'), ('ex_urgent', 'Extremely Urgent')],
                                string='Priority', required=False)
    reason_reject = fields.Text("Rejection Reason", track_visibility="onchange")
    line_manager_user_id = fields.Many2one('res.users', "Line Manager", copy=False)
    stock_user_id = fields.Many2one('res.users', "Stock Manager", copy=False)
    finance_user_id = fields.Many2one('res.users', "Finance Manager", copy=False)
    emails = fields.Char(compute='compute_approval_emails', store=True)
    # edit_analytic_account = fields.Boolean(compute='compute_edit_cost_center')
    line_manager_id = fields.Many2one('res.users', string="Line Manager", compute='get_line_manager', store=True)
    categ_id = fields.Many2one('product.category', string="Product Category")

    # Special Dates
    inventory_check_date = fields.Date()
    lm_approval_date = fields.Date("LM Approval Date")

    @api.depends('department_id')
    def get_line_manager(self):
        for record in self:
            line_manager = False
            try:
                line_manager = record.requested_by.employee_ids[0].line_manager_id
            except:
                line_manager = False
            record.line_manager_id = line_manager

    def _get_default_department(self):
        department = self.env.user.department_id
        if not department:
            raise UserError("This user is not linked with a department.")
        return department

    def _get_default_analytic_account(self):
        department_id = self.env.user.department_id or False
        analytic_account_id = False

        if department_id and department_id.analytic_account_id:
            analytic_account_id = department_id.analytic_account_id
        else:
            return False
        return analytic_account_id.id

    def get_requested_by(self):
        user = self.env.user.id
        return user

    @api.depends('state')
    def compute_approval_emails(self):
        self.ensure_one()
        to_clean, to_do = self.env['purchase.request'], self.env['purchase.request']
        to_clean |= self

        users = []
        buyers = []
        if self.state == 'line_approve':
            line_manager = False
            try:
                line_manager = self.requested_by.employee_ids[0].line_manager_id
            except:
                line_manager = False
            users.append(line_manager)

        elif self.state == 'finance_approve':
            users = self.env.ref('account.group_account_manager').users
        elif self.state == 'done' and self.purchase_method != 'deliver':
            buyers = self.env.ref('purchase.group_purchase_user').users

        self.activity_unlink(['base_no.mail_act_approval', 'procurement.mail_act_mr_procurement'])

        for user in users:
            self.activity_schedule('base_no.mail_act_approval', user_id=user.id)
            to_do |= self

        for buyer in buyers:
            self.activity_schedule('procurement.mail_act_mr_procurement', user_id=buyer.id)
            # date_deadline = self.schedule_date
            to_do |= self

        self.emails = ""

    def compute_budget_reserved_amount(self):
        for record in self:
            total = 0

            for line in record.line_ids:
                total += (line.qty_purchase - line.purchase_delivered) * line.unit_price
            if record.budget_line_id and record.state in ['done', 'close']:
                record.amount_budget_reserved = total
            else:
                record.amount_budget_reserved = total

    def compute_purchase_method(self):
        self.ensure_one()
        purchase_method = has_delivery = has_purchase = False

        if self.item_type == 'service':
            self.purchase_method = 'purchase'
        else:
            has_delivery = any(line.qty_deliver for line in self.line_ids)
            has_purchase = any(line.qty_purchase for line in self.line_ids)
            if has_delivery and not has_purchase:
                purchase_method = 'deliver'
            elif has_purchase and not has_delivery:
                purchase_method = 'purchase'
            elif has_delivery and has_purchase:
                purchase_method = 'both'

        self.purchase_method = purchase_method

    @api.depends('line_ids.unit_price')
    def compute_totals(self):
        for record in self:
            total = purchase_total = 0.0
            for line in record.line_ids:
                total += line.unit_price * line.product_qty
                purchase_total += line.unit_price * line.qty_purchase

            record.update({
                'amount_total': total,
                'amount_total_purchase': purchase_total
            })

    @api.model
    def get_default_requested_by(self):
        return self.env.user.id

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('purchase.request')

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('purchase.request') or "/"
        vals['name'] = seq

        request = super(PurchaseRequest, self).create(vals)
        if vals.get('assigned_to'):
            request.message_subscribe(partner_ids=[request.assigned_to.partner_id.id])

        if request.requested_by.id != self.env.user.id:
            raise UserError("Sorry you cannot create a request with different user.")
        return request

    @api.model
    def _get_default_picking_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            (
            'warehouse_id.company_id', 'in', [self.env.context.get('company_id', self.env.user.company_id.id), False])],
            limit=1).id

    def compute_agreement_count(self):
        self.ensure_one()
        self.agreement_count = self.env['purchase.requisition'].search_count([('request_ids', 'in', self.id)])

    def compute_purchase_count(self):
        self.ensure_one()
        self.purchase_count = self.env['purchase.order'].search_count([('request_ids', 'in', self.id)])

    def compute_picking_count(self):
        self.ensure_one()
        self.picking_count = self.env['stock.picking'].search_count([('request_ids', 'in', self.id)])
        self.service_count = self.env['service.requisition'].search_count([('request_ids', 'in', self.id)])

    @api.depends('state')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve', 'leader_approved', 'manager_approved', 'reject', 'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    def write(self, vals):
        res = super(PurchaseRequest, self).write(vals)
        for request in self:
            if vals.get('assigned_to'):
                self.message_subscribe(partner_ids=[request.assigned_to.partner_id.id])
        return res

    def unlink(self):
        for rec in self:
            if not rec.state == 'draft':
                raise UserError("Only draft records can be deleted!")

        return super(PurchaseRequest, self).unlink()

    def button_draft(self):
        self.mapped('line_ids').do_uncancel()
        return self.write({'state': 'draft'})

    def button_to_approve(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError('Please add MR lines!')
        if not self.requested_by.id == self.env.user.id:
            raise UserError('Sorry, Only requester can submit this document!')

        line_manager = False
        try:
            line_manager = self.requested_by.employee_ids[0].line_manager_id
        except:
            line_manager = False
        if not line_manager:
            raise UserError("Line manger is not set!")
        return self.write({'state': 'line_approve'})

    def update_available_qtys(self):
        for record in self:
            record.line_ids.update_available_qty()

    def button_leader_approved(self):
        self.ensure_one()
        line_managers = []
        today = fields.Date.today()
        line_manager = False
        try:
            line_manager = self.requested_by.employee_ids[0].line_manager_id
        except:
            line_manager = False
        if not line_manager or not self.env.user.id == line_manager.id:
            raise UserError("Sorry. Your are not authorized to approve this document!")
        self.update_available_qtys()
        self.line_manager_user_id = self.env.user.id
        self.lm_approval_date = today
        self.button_done()


    def button_rejected(self):
        self.ensure_one()
        self.mapped('line_ids').do_cancel()
        return self.write({'state': 'reject'})

    def button_cancel(self):
        for request in self:
            orders = self.env['purchase.order'].search([('request_ids', 'in', request.id)])
            orders.button_cancel()
            pickings = self.env['stock.picking'].search([('request_ids', 'in', request.id)])
            pickings.action_cancel()
            pickings.unlink()
            request.state = 'cancel'
        # request.mapped('line_ids').do_cancel()

    def button_done(self):
        self.ensure_one()

        if self.purchase_method == 'deliver':
            self.state = 'close'
        else:
            self.state = 'done'

        if self.item_type == 'material':
            self.button_serivce_done()

    def button_close(self):
        self.write({'state': 'close'})

    def action_reject(self):
        self.write({'state': 'reject'})

    def button_serivce_done(self):
        if self.item_type == 'service':
            pass
        else:
            self.sudo().action_stock_delivery()
        return self.write({'state': 'done'})

    def action_view_purchase_order(self):
        return {
            'name': "RFQ/ Order",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('request_ids', 'in', self.id)],
        }

    def action_view_picking(self):
        return {
            'name': "Material Delivery",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('request_ids', 'in', self.id)],
        }

    def action_view_service(self):
        return {
            'name': "Service Delivery",
            'type': 'ir.actions.act_window',
            'res_model': 'service.requisition',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('request_ids', 'in', self.id)],
        }

    def action_view_purchase_agreement(self):
        return {
            'name': "Purchase Agreement",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': [('request_ids', 'in', self.id)],
        }

    def action_stock_delivery(self):
        for order in self:
            if not order.line_ids:
                raise UserError(_('Please create Material Request lines.'))
            
            # Default Location and Picking Type
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            pickingType = self.env['stock.picking.type'].sudo().search(
                [('warehouse_id', '=', warehouse.id), ('code', '=', 'internal')], limit=1)
            location_id = self.env.user.location_id
            
            # Check if location and picking type are defined in the prodcut category
            if order.categ_id.mr_location_id:
                location_id = order.categ_id.mr_location_id

            if order.categ_id.mr_operation_type_id:
                pickingType = order.categ_id.mr_operation_type_id 

            location_dest_id = order.department_id.location_id
            
            if not warehouse or not pickingType or not location_id or not location_dest_id:
                raise UserError("Stock locations are not properly set.")

            deliver_pick = {    
                'picking_type_id': pickingType.id,
                'partner_id': False,
                'origin': self.name,
                'request_ids': [self.id],
                'location_dest_id': location_dest_id.id,
                'location_id': location_id.id,
                'analytic_account_id': self.analytic_account_id.id
            }

            purchase_pick = {
                'picking_type_id': pickingType.id,
                'partner_id': False,
                'origin': self.name,
                'location_dest_id': location_dest_id.id,
                'location_id': location_id.id,
                'request_ids': [self.id],
                'analytic_account_id': self.analytic_account_id.id
            }

            deliver_picking = purchase_picking = False
            moves = move_ids = []
            has_mr_transfer = False
            for line in order.line_ids:
                if line.product_id.categ_id.mr_transfer:
                    has_mr_transfer = True
                    break

            if not has_mr_transfer:
                continue

            if order.purchase_method == 'deliver':
                deliver_picking = self.env['stock.picking'].create(deliver_pick)
                moves = order.line_ids.filtered(lambda r: r.qty_deliver)._create_stock_moves_transfer(deliver_picking,
                                                                                                      'deliver')
                move_ids = moves._action_confirm()
                move_ids._action_assign()

            elif order.purchase_method == 'purchase':
                purchase_picking = self.env['stock.picking'].create(purchase_pick)
                moves = order.line_ids.filtered(lambda r: r.qty_purchase)._create_stock_moves_transfer(purchase_picking,
                                                                                                       'purchase')

            elif order.purchase_method == 'both':
                deliver_picking = self.env['stock.picking'].create(deliver_pick)
                moves = order.line_ids.filtered(lambda r: r.qty_deliver)._create_stock_moves_transfer(deliver_picking,
                                                                                                      'deliver')
                move_ids = moves._action_confirm()
                move_ids._action_assign()

                purchase_picking = self.env['stock.picking'].create(purchase_pick)
                moves = order.line_ids.filtered(lambda r: r.qty_purchase)._create_stock_moves_transfer(purchase_picking,
                                                                                                       'purchase')

    def check_auto_reject(self):
        """When all lines are cancelled the purchase request should be
		auto-rejected."""
        for pr in self:
            if not pr.line_ids.filtered(lambda l: l.cancelled is False):
                pr.write({'state': 'reject'})

    def make_purchase_quotation(self):
        view_id = self.env.ref('purchase.purchase_order_form')
        order_line = []

        for line in self.line_ids:
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
            if self.item_type == 'service':
                account_analytic_id = self.analytic_account_id.id if self.analytic_account_id else False

            product_line = (0, 0, {'product_id': line.product_id.id,
                                   'state': 'draft',
                                   'product_uom': line.product_id.uom_po_id.id,
                                   'price_unit': 0,
                                   'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                   'product_qty': line.qty_purchase,
                                   'name': line.name,
                                   'account_analytic_id': account_analytic_id,
                                   'request_line_id': line.id
                                   })
            order_line.append(product_line)

        return {
            'name': _('New Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'context': {
                'default_request_ids': [self.id],
                'default_item_type': self.item_type,
                # 'default_po_priority': self.priority,
                # 'default_order_line': order_line,
            }
        }

    def make_purchase_requisition(self):
        view_id = self.env.ref('purchase_requisition.view_purchase_requisition_form')
        order_line = []
        type = self.env['purchase.requisition.type'].search([('exclusive', '=', 'exclusive')], limit=1)
        for line in self.line_ids:
            product = line.product_id
            if self.env.uid == SUPERUSER_ID:
                company_id = self.env.user.company_id.id
            product_line = (0, 0, {'product_id': line.product_id.id,
                                   'product_uom_id': line.product_id.uom_po_id.id,
                                   'schedule_date': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                   'product_qty': line.qty_purchase,
                                   'qty_ordered': line.qty_purchase,
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
                # 'default_line_ids': order_line,
                'default_request_ids': [self.id],
                'default_item_type': self.item_type,
                # 'default_type_id': type.id if type else False
            }
        }


class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread']

    @api.depends('product_id', 'name', 'product_uom_id', 'product_qty',
                 'date_required', 'specifications')
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                if rec.product_id.seller_ids:
                    rec.supplier_id = rec.product_id.seller_ids[0].name

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)], required=True,
        track_visibility='onchange')
    categ_id = fields.Many2one('product.category', string="Product Category")
    child_categ_ids = fields.Many2many('product.category', string="Child Product Category", compute="get_child_categ_ids", store=True)
    
    name = fields.Char('Description', size=256,
                       track_visibility='onchange')
    item_type = fields.Selection([('material', 'Material'), ('service', 'Service')], default="material",
                                 string='Item Type', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float(string='Quantity', track_visibility='onchange',
                               digits=dp.get_precision('Product Unit of Measure'))
    request_id = fields.Many2one('purchase.request',
                                 'Purchase Request',
                                 ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 store=True, readonly=True)

    requested_by = fields.Many2one('res.users',
                                   related='request_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)
    assigned_to = fields.Many2one('res.users',
                                  related='request_id.assigned_to',
                                  string='Assigned to',
                                  store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start',
                             string='Request Date', readonly=True,
                             store=True)
    end_start = fields.Date(related='request_id.end_start',
                            string='End Date', readonly=True,
                            store=True)
    description = fields.Text(string='Description', readonly=True,
                              store=True)
    date_required = fields.Date(string='Request Date', required=False,
                                track_visibility='onchange',
                                related='request_id.date_start')

    specifications = fields.Text(string='Specifications')
    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)

    supplier_id = fields.Many2one('res.partner',
                                  string='Preferred supplier',
                                  compute="_compute_supplier_id")

    cancelled = fields.Boolean(string="Cancelled", readonly=True, default=False, copy=False)
    qty_available = fields.Float("Available Qty", readonly=True, store=True, copy=False)
    qty_deliver = fields.Float("To Deliver", compute='compute_quantities', store=True)
    qty_purchase = fields.Float("To Purchase", compute='compute_quantities', store=True)
    unit_price = fields.Monetary(string="Estimated Cost")
    currency_id = fields.Many2one('res.currency', related='request_id.currency_id')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          related='request_id.analytic_account_id')

    purchase_delivered = fields.Float(compute="compute_purchase_delivered")
    remarks = fields.Char()
    total = fields.Monetary(compute="compute_total")

    @api.depends('categ_id')
    def get_child_categ_ids(self):
        for line in self:
            if line.categ_id:
                child_categs = self.env['product.category'].search([('id', 'child_of', line.categ_id.id)])
                line.child_categ_ids = child_categs
                continue
            line.child_categ_ids = False

    def update_available_qty(self):
        for line in self:
            location_id = False
            if line.categ_id.mr_location_id:
                location_id = line.categ_id.mr_location_id.id
            elif self.env.user.location_id:
                location_id = self.env.user.location_id.id
            warehouse_quantity = line.product_id.with_context(location=location_id).warehouse_quantity
            line.qty_available = warehouse_quantity if warehouse_quantity > 0 else 0

    @api.model
    def create(self, vals):
        product_id = self.env['product.product'].browse(vals.get('product_id'))
        
        return super(PurchaseRequestLine, self).create(vals)

    @api.constrains('product_qty')
    def check_non_zero(self):
        if self.product_qty == 0:
            raise UserError("Quantity should be greater than Zero.\n %s" % self.product_id.display_name)

    @api.depends('product_qty', 'unit_price')
    def compute_total(self):
        for record in self:
            record.total = record.product_qty * record.unit_price

    def compute_purchase_delivered(self):
        for record in self:
            lines = []
            delivered = False

            if record.request_id.item_type == 'material':
                lines = record.env['stock.move'].search([
                    ('mr_line_id', '=', record.id),
                    ('mr_purchase_line', '=', True),
                    ('state', '=', 'done'),
                    ('origin_returned_move_id', '=', False),
                ])

                delivered = sum(line.quantity_done for line in lines)
                record.purchase_delivered = delivered

            else:
                lines = record.env['purchase.order.line'].search([
                    ('request_line_id', '=', record.id),
                ])

                delivered = sum(line.qty_invoiced for line in lines)
                record.purchase_delivered = delivered

    @api.depends('qty_available', 'product_qty')
    def compute_quantities(self):
        for line in self:
            if line.qty_available > line.product_qty:
                line.qty_deliver = line.product_qty
            else:
                line.qty_deliver = line.qty_available if line.qty_available > 0 else 0.0

            line.qty_purchase = line.product_qty - line.qty_deliver

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name
            self.update_available_qty()
            self.unit_price = self.product_id.standard_price

    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({'cancelled': True})

    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({'cancelled': False})

    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve', 'leader_approved', 'manager_approved', 'reject',
                                        'done'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    is_editable = fields.Boolean(string='Is editable',
                                 compute="_compute_is_editable",
                                 readonly=True)

    def write(self, vals):
        res = super(PurchaseRequestLine, self).write(vals)
        if vals.get('cancelled'):
            requests = self.mapped('request_id')
            requests.check_auto_reject()
        return res

    def _create_stock_moves_transfer(self, picking, qty):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self.filtered(lambda l: l.product_id.categ_id.mr_transfer):

            diff_quantity = 0.0
            mr_line = False
            if qty == 'deliver':
                diff_quantity = line.qty_deliver
            elif qty == 'purchase':
                diff_quantity = line.qty_purchase
                mr_line = True

            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_po_id.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'picking_id': picking.id,
                'state': 'draft',
                'company_id': picking.company_id.id,
                # 'price_unit': price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                'product_uom_qty': diff_quantity,
                'mr_purchase_line': mr_line,
                'mr_line_id': line.id,
            }

            done += moves.create(template)
        return done


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    request_id = fields.Many2one('purchase.request', 'Material Request')
