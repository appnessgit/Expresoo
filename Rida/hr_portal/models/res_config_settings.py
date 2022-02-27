# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_hr_holidays_portal = fields.Boolean(string='Leaves')
    module_hr_expense_portal = fields.Boolean(string='Expenses')
    module_hr_attendance_portal = fields.Boolean(string='Attendance')
    module_hr_payslip_portal = fields.Boolean(string='Payslips')
