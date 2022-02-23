# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
from odoo import api, fields, models, _ , SUPERUSER_ID
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
	_inherit = "stock.move"

	mr_purchase_line = fields.Boolean(copy=True)
	mr_line_id = fields.Many2one('purchase.request.line', copy=True)

	invoice_qty = fields.Float(copy=False)
	refund_qty = fields.Float(copy=False)


class StockPicking(models.Model):
	_inherit="stock.picking"

	request_ids = fields.Many2many('purchase.request', string='Material Requests')

	# Inspection
	quantity = fields.Boolean()
	physical_appearance = fields.Boolean()
	delivery_vehicle_status = fields.Boolean()
	specifications = fields.Boolean()
	code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')], related='picking_type_id.code')
	invoiced = fields.Boolean()
	returned = fields.Boolean()

	delivery_note = fields.Binary("Delivery Note")
	return_picking = fields.Boolean(compute="compute_return_picking")


	def _material_check_availability(self, requests):
		for request in requests:
			pickings = self.env['stock.picking'].search([('request_ids', 'in', request.id), ('state','not in', ['done', 'cancel'])])

			for picking in pickings:
				picking.action_confirm()
				picking.action_assign()

	def action_done(self):
		picking = super(StockPicking, self).action_done()
	
		for rec in self:
			# Check availability of the related MR pickings
			if rec.request_ids:
				rec._material_check_availability(rec.request_ids)
			# Restrict returned quantity to not exceed received
			for move in rec.move_lines:
				if move.origin_returned_move_id and move.origin_returned_move_id.returned_qty > move.origin_returned_move_id.quantity_done:
					raise UserError("Returned quantities cannot exceeds original move quantity")


