from odoo import api, fields, models
from datetime import datetime


class Eos(models.Model):
    _inherit = 'hr.end.service'

    date = fields.Date(string='Date', default=datetime.today())
    