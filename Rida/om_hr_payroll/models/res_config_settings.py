# -*- coding: utf-8 -*-

from odoo import fields, models


class ResInhertenceCompany(models.Model):
    _inherit = 'res.company'

    module_om_hr_payroll_account = fields.Boolean(string='Payroll Accounting', store='True')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    module_om_hr_payroll_account = fields.Boolean(string='Payroll Accounting', related='company_id.module_om_hr_payroll_account', readonly=False)

