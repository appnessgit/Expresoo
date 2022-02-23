from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    po_reserved = fields.Monetary("PO Reserved", compute="compute_po_reserved")
    po_ids = fields.One2many('purchase.order.line', 'budget_line_id')

    def compute_po_reserved(self):
        for rec in self:
            pos = self.env['purchase.order.line'].search([('budget_line_id', '=', rec.id), ('state', 'in', ['ceo', 'purchase'])])
            po_reserved = 0

            for line in pos:
                invoice_lines = self.env['account.move.line'].search([('purchase_line_id', '=', line.id), ('move_id.state', '=', 'posted')])
                qty_invoiced = sum(l.quantity for l in invoice_lines)
                remaining_qty = line.product_qty - qty_invoiced
                po_reserved += remaining_qty * line.price_unit

            rec.po_reserved = po_reserved

class CrossoveredBudgetAmendment(models.Model):
    _inherit = 'account.budget.amendment'

    @api.depends('budget_line_from')
    def compute_remaining(self):
        self.ensure_one()
        if not self.budget_line_from:
            return
        self.remaining_amount = self.budget_line_from.remaining_amount - self.budget_line_from.po_reserved