# from typing_extensions import Required
from odoo import _, api, fields, models


class Hr_leave_extend(models.Model):
    _inherit = 'hr.leave'
    delegated_employee_id = fields.Many2one(comodel_name='hr.employee', string='Delegated Employee')
    justification = fields.Text(string='Justification', readonly=True)
    
    medical_report = fields.Binary(string= 'Medical Report')
    leave_type_test = fields.Selection(string='Leave type test', related='holiday_status_id.leave_type')


    # def required_lg(self):
    #     if self.medical_report:
