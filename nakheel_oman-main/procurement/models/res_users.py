from odoo import api, fields, models, _


class User(models.Model):
    _inherit = "res.users"

    warehouse_ids = fields.Many2many('stock.warehouse', string="Allowed Warehouses")
    x_signature = fields.Html(sting="Report Signature")
    location_id = fields.Many2one('stock.location', string="Default Location")
