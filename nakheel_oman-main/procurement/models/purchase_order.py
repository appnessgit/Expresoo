from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('prm', 'Purhase Manager Approval'),
        ('finance', 'Finance Approval'),
        ('ceo', 'CEO Approval'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    picking_type_id = fields.Many2one('stock.picking.type', default=False)
    request_ids = fields.Many2many('purchase.request', string='Material Requests')
    po_priority = fields.Selection([('reqular', 'Regular'), ('urgent', 'Urgent'), ('ex_urgent', 'Extremely Urgent')],
                                   string='Priority', required=False)
    ship_to_address = fields.Char('Ship To address')

    reason_reject = fields.Text("Rejection Reason", track_visibility="onchange")
    over_budget = fields.Boolean()
    can_invoice = fields.Boolean(compute="compute_can_invoice")
    amount_total_default_currency = fields.Monetary(compute='compute_amount_total_company_currency')
    company_currency = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    rfq_ref = fields.Char('RFQ Reference')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        super(PurchaseOrder, self)._onchange_company_id()
        self.picking_type_id = False

    @api.onchange('request_ids')
    def _onchange_request_ids(self):
        if not self.request_ids:
            return

        self = self.with_company(self.company_id)
        request_ids = self.request_ids
        order_line = []
        for request in request_ids:
            
            type = self.env['purchase.requisition.type'].search([('exclusive', '=', 'exclusive')], limit=1)
            for line in request.line_ids:
                product = line.product_id
                if self.env.uid == SUPERUSER_ID:
                    company_id = self.env.user.company_id.id
                product_line = (0, 0, {'product_id': line.product_id.id,
                                        'state': 'draft',
                                        'product_uom': line.product_id.uom_po_id.id,
                                        'price_unit': 0,
                                        'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        'product_qty': line.qty_purchase,
                                        'name': line.name,
                                        'request_line_id': line.id
                                        })
                order_line.append(product_line)
        self.order_line.unlink()
        self.order_line = order_line

    def button_cancel(self):
        super(PurchaseOrder, self).button_cancel()
        for rec in self:
            services = self.env['service.requisition'].search([('purchase_id', '=', rec.id)])
            services.button_cancel()


    @api.depends('state')
    def compute_approval_emails(self):
        to_clean, to_do = self.env['purchase.order'], self.env['purchase.order']
        to_clean |= self
        # self.message_subscribe(partner_ids=self.user_id.partner_id.ids)
        for order in self:
            users = []

            if order.state == 'finance':
                users = self.env.ref('account.group_account_manager').users
            elif order.state == 'prm':
                users = self.env.ref('purchase.group_purchase_manager').users
            elif order.state == 'ceo':
                users = self.env.ref('base_no.group_ceo').users

            order.activity_unlink(['base_no.mail_act_approval'])

            for user in users:
                order.activity_schedule(
                    'base_no.mail_act_approval',
                    user_id=user.id)
                to_do |= self
            order.emails = ""

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id
        self.company_id = requisition.company_id.id
        self.currency_id = requisition.currency_id.id
        self.item_type = requisition.item_type
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(
                    lambda tax: tax.company_id == requisition.company_id)).ids
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(
                    lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_line = self.order_line.filtered(lambda l: l.product_id.id == order_line_values.get('product_id'))
            if order_line:
                order_line.update({'price_unit': order_line_values.get('price_unit')})
            else:
                order_lines.append((0, 0, order_line_values))
        if not self.order_line:
            self.order_line = order_lines

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('date_planned'):
            for order in self:
                order.order_line.update({
                    'date_planned': order.date_planned
                })

    @api.depends('amount_total', 'currency_id')
    def compute_amount_total_company_currency(self):
        self.ensure_one()
        if not self.currency_id:
            return
        currency = self.currency_id
        company_currency = self.company_id.currency_id

        amount = currency.compute(self.amount_total, company_currency)
        self.amount_total_default_currency = amount

    @api.depends('order_line')
    def compute_can_invoice(self):
        self.ensure_one()
        if any(line.qty_invoiced < line.qty_received for line in self.order_line) \
                and self.state in ['purchase', 'done']:
            self.can_invoice = True

    def check_budget(self):
        for rec in self:
            rec.order_line.write({'over_budget': False})
            combinations = []
            for line in rec.order_line:
                vals = {
                    'account': line.expense_account_id.id,
                    'analytic': line.account_analytic_id.id if line.account_analytic_id else False
                }
                
                combinations.append(vals)
            combinations = [dict(t) for t in {tuple(d.items()) for d in combinations}]
            for combination in combinations:
                c_lines = rec.order_line.filtered(lambda l: l.expense_account_id.id == combination['account'] and l.account_analytic_id.id == combination['analytic'])
                combination['lines'] = c_lines
                combination['amount'] = sum(l.price_subtotal_default_currency for l in c_lines)
            
            for combination in combinations:
                today = datetime.today()
                analytic_account_id = combination['analytic']
                budget_lines = self.env['crossovered.budget.lines'].search([
                    ('account_id', '=', combination['account']),
                    ('analytic_account_id', 'in', [analytic_account_id, False]),
                    ('date_from', '<=', today),
                    ('date_to', '>=', today),
                    ('allow_over_budget', '=', False),
                    ('crossovered_budget_id.type', '=', 'expense'),
                    ('crossovered_budget_id.state', 'in', ('validate', 'done'))
                ])
                if not budget_lines:
                    continue

                cost_center_budget = budget_lines.filtered(lambda x: x.analytic_account_id.id == analytic_account_id)
                cost_center_general = budget_lines.filtered(lambda x: not x.analytic_account_id)
                if cost_center_budget:
                    budget_line_id = cost_center_budget[0]
                elif cost_center_general:
                    budget_line_id = cost_center_general[0]

                if not budget_line_id:
                    continue

                combination.get('lines').write({'budget_line_id': budget_line_id.id})
                remaining = budget_line_id.remaining_amount - budget_line_id.po_reserved
                amount = combination['amount']
                if amount > remaining:
                    if combination.get('lines'):
                        combination.get('lines').write({'over_budget': True})


    #   Action Submit
    def action_submit(self):
        self.ensure_one()
        self.write({'state': 'prm'})

    #   Procurement Manager Approval
    def action_prm(self):
        self.sudo().check_budget()
        self.write({'state': 'finance'})

    #   Action Finance
    def action_finance(self):

        self.ensure_one()
        self.check_budget()
        if any(line.over_budget for line in self.order_line):
            raise UserError(_("Some lines are exceeding the budget."))
        company = self.company_id
        attachment_limit = company.po_committee_limit
        amount = self.amount_total_default_currency
        if amount > attachment_limit and not self.po_commitee_attachment:
            raise UserError(_("Please add PO Commitee attachment."))

        if not company.po_double_validation:
            self.button_confirm()
        else:
            limit = company.po_double_validation_amount
            if amount > limit:
                self.write({'state': 'ceo'})
            else:
                self.button_confirm()

    # CEO Approval
    def action_ceo(self):
        self.button_confirm()  


    def action_reject(self):
        self.state = 'reject'

    def button_confirm(self):
        for order in self:
            old_name = order.name
            name = ""
            if not order.rfq_ref:
                name = self.env['ir.sequence'].next_by_code('purchase.order.order') or False
                if name:
                    order.name = name
                    order.rfq_ref = old_name
        super(PurchaseOrder, self).button_confirm()


class PurchaseOrderRejectionWizard(models.TransientModel):
    _name = "purchase.order.rejection.wizard"

    reason_reject = fields.Text("Rejection Reason")

    def action_validate(self):
        self.ensure_one()
        context = dict(self._context or {})
        active_model = self.env.context.get('active_model')
        active_id = self.env.context['active_ids']

        order = self.env[active_model].browse(active_id)

        if self.reason_reject:
            order.state = 'reject'
            order.reason_reject = self.reason_reject
            message = """
            This document was rejected by: %s <br/>
            <b>Rejection Reason:</b> %s 
            """ % (self.env.user.name, self.reason_reject)
            order.message_post(body=message)

        return {'type': 'ir.actions.act_window_close'}


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    request_line_id = fields.Many2one('purchase.request.line', 'requsition', ondelete='set null', index=True,
                                      readonly=True)
    request_id = fields.Many2one('purchase.request', related='request_line_id.request_id', string='Purchase Request')
    budget_line_id = fields.Many2one('crossovered.budget.lines', string="Budget Line")
    over_budget = fields.Boolean(string="Over Budget")
    expense_account_id = fields.Many2one('account.account', string="Expense Account", compute="get_expense_account", store=True)
    price_subtotal_default_currency = fields.Float(compute='compute_price_subtotal_company_currency', store=True)

    @api.depends('product_id')
    def get_expense_account(self):
        for record in self:
            if not record.product_id:
                record.expense_account_id = False
                continue
            product = record.product_id
            accounts = product.product_tmpl_id.get_product_accounts()
            account_id = accounts['expense'].id
            record.expense_account_id = account_id

    @api.depends('price_subtotal', 'currency_id')
    def compute_price_subtotal_company_currency(self):
        for record in self:
            if not record.currency_id:
                record.price_subtotal_default_currency = 0
                continue
            currency = record.currency_id
            company_currency = record.order_id.company_id.currency_id

            amount = currency.compute(record.price_subtotal, company_currency)
            record.price_subtotal_default_currency = amount