# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    picking_ids = fields.Many2many('stock.picking', string="GRNs", copy=True)

    @api.onchange('picking_ids')
    def picking_ids_change(self):
        if self.picking_ids and not self.partner_id:
            raise UserError("Please select a vendor first.")
        self.invoice_line_ids = []

        new_lines = self.env['account.move.line']
        for picking in self.picking_ids:
            for line in picking.move_ids_without_package:
                data = self._prepare_invoice_line_from_move_line(line)
                new_line = new_lines.new(data)
                new_line._set_additional_fields(self)
                new_lines += new_line

            self.invoice_line_ids = new_lines
            self.payment_term_id = picking.purchase_id.payment_term_id

        return {}

    def _prepare_invoice_line_from_move_line(self, line):
        qty = 0.0
        if self.type == 'in_invoice':
            qty = line.quantity_done - line.invoice_qty
        elif self.type == 'in_refund':
            qty = line.quantity_done - line.refund_qty

        if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
            qty = 0.0

        taxes = line.purchase_line_id.taxes_id
        invoice_line_tax_ids = line.purchase_line_id.order_id.fiscal_position_id.map_tax(taxes, line.purchase_line_id.product_id,
                                                                        line.purchase_line_id.order_id.partner_id)

        invoice_line = self.env['account.move.line']
        date = self.date or self.date_invoice
        data = {
            'purchase_line_id': line.purchase_line_id.id,
            'stock_move_id': line.id,
            'name': line.picking_id.name + ': ' + line.name,
            'origin': line.purchase_line_id.order_id.origin,
            'uom_id': line.purchase_line_id.product_uom.id,
            'product_id': line.purchase_line_id.product_id.id,
            'account_id': invoice_line.with_context(
                {'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
            'price_unit': line.purchase_line_id.order_id.currency_id._convert(
                line.purchase_line_id.price_unit, self.currency_id, line.purchase_line_id.company_id, date or fields.Date.today(), round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': False,
            'invoice_line_tax_ids': invoice_line_tax_ids.ids
        }
        account = invoice_line.get_invoice_line_account('in_invoice', line.purchase_line_id.product_id, line.purchase_line_id.order_id.fiscal_position_id,
                                                        self.env.user.company_id)
        if account:
            data['account_id'] = account.id
        return data

    def action_invoice_open(self):
        res = super(AccountMove, self).action_invoice_open()
        for rec in self:
            if rec.picking_ids:
                for line in rec.invoice_line_ids:
                    if line.stock_move_id:
                        if self.type == 'in_invoice':
                            line.stock_move_id.invoice_qty += line.quantity
                            # line.stock_move_id.picking_id.invoiced = True
                        elif self.type == 'in_refund':
                            line.stock_move_id.refund_qty += line.quantity
                            # line.stock_move_id.picking_id.returned = True
                            if line.stock_move_id.refund_qty > line.stock_move_id.invoice_qty:
                                raise UserError("You cannot refund more than invoiced quantity")

                        #   update billing status for pickings
                        if all(move.invoice_qty == move.quantity_done for move in line.stock_move_id.picking_id.move_lines):
                            line.stock_move_id.picking_id.invoiced = True
                        if all(move.returned_qty == move.quantity_done for move in line.stock_move_id.picking_id.move_lines):
                            line.stock_move_id.picking_id.returned = True

        return res

    @api.returns('self')
    def refund(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = super(AccountMove, self).refund(date_invoice, date, description, journal_id)

        for refund_invoice in new_invoices:
            refund_invoice.picking_ids = self.picking_ids

        return new_invoices

    @api.model
    def create(self, vals):
        invoice = super(AccountMove, self).create(vals)
        picking = invoice.invoice_line_ids.mapped('stock_move_id.picking_id')
        if picking and not invoice.refund_invoice_id:
            message = _("This vendor bill has been created from: %s") % (",".join(
                ["<a href=# data-oe-model=stock.picking data-oe-id=" + str(order.id) + ">" + order.name + "</a>" for
                 order in picking]))
            invoice.message_post(body=message)
        return invoice

    @api.constrains('invoice_line_ids')
    def check_new_lines(self):
        if any(line.purchase_line_id for line in self.invoice_line_ids):
            if any(not line.purchase_line_id for line in self.invoice_line_ids):
                raise UserError("You cannot add new lines to this invoice.")


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    stock_move_id = fields.Many2one('stock.move')
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ], related='move_id.move_type')

    @api.constrains('quantity')
    def check_grn_qty_(self):
        for record in self:
            if not record.stock_move_id:
                return
            if record.type == 'in_refund' and record.quantity > record.stock_move_id.quantity_done:
                raise UserError(str(record.name) + "\n This product quantity exceeds received quantity.")

            if record.type == 'in_invoice' and record.quantity != record.stock_move_id.quantity_done:
                raise UserError(str(record.name) + "\n You cannot change this product quantity.")



