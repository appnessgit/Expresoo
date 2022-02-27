# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_hr_eos_accounting = fields.Boolean(string="EOS Accounting Management")
    module_hr_eos_custody = fields.Boolean(string="EOS Custody Management")
    module_hr_eos_custody_accounting = fields.Boolean(string="EOS Accounting Custody")
    module_hr_eos_loan = fields.Boolean(string="EOS Loan")
    module_hr_eos_loan_accounting = fields.Boolean(string="EOS Accounting Loan")
