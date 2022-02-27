

from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    line_manager_id = fields.Many2one(comodel_name='res.users', string='Line Manager')
    