# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017-Today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError



class Product(models.Model):
    _inherit = "product.template"

    warehouse_quantity = fields.Float(compute='_get_warehouse_quantity', string='User Available Quantity')
    item_type = fields.Selection([('service', 'Service'), ('material', 'Material')], string="Item Type", compute="compute_item_type", store=True)

    @api.depends('type')
    def compute_item_type(self):
        for product in self:
            if product.type == 'service':
                product.item_type = 'service'
            else:
                product.item_type = 'material'


    def _get_warehouse_quantity(self):
        for product in self:
            qty_on_hand = 0
            user = self.env.user
            location = user.location_id
            context = self.env.context
            if context.get('location'):
                location = self.env['stock.location'].browse(int(context.get('location')))
            if not location:
                product.warehouse_quantity = 0
                return
            quant_ids = self.env['stock.quant'].sudo().search([ '|', 
                ('product_id', '=', product.id),
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id', '=', location.id),
            ])
            qty_on_hand = sum(line.quantity - line.reserved_quantity for line in quant_ids)
            product.warehouse_quantity = qty_on_hand


class ProductCategory(models.Model):
    _inherit = 'product.category'

    mr_use = fields.Boolean(string="Use in MRs")
    mr_transfer = fields.Boolean(string="Automatically Create Internal Transfer", default=True)
    mr_location_id = fields.Many2one('stock.location', string="Default Location")
    mr_operation_type_id = fields.Many2one('stock.picking.type', string="Default Operation Type")
    item_type = fields.Selection([('material', 'Material'), ('service', 'Service')], default="material",
                                 string='Item Type', required=True)
    