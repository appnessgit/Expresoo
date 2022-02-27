# -*- coding: utf-8 -*-

from odoo import models, fields, api
from calendar import monthrange
import datetime,time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError

"""
    1- 14 = Full pay
    15 - 28 = 75%pay
    29 - 42  =50% pay
    43 - 70 = 25% pay
    71  - 90 = No pay
"""

class hr_leave_type(models.Model):
    _inherit = 'hr.leave.type'

    sick_rule  = fields.Boolean(string='Sick Leave Payroll Rule')
    weekend_sick  = fields.Boolean(string='Exclude Weekend')
    minimum_allowed = fields.Integer(string='Minimum Allowed Days')    
    sick_rule_ids = fields.One2many(comodel_name='sick.leave.rule', inverse_name='leave_type_id', string='Deduction Rules')
    

class sick_leave_rule(models.Model):
    _name = 'sick.leave.rule'
    
    leave_type_id  = fields.Many2one(comodel_name='hr.leave.type', string='Leave Type')
    
    range_from  = fields.Integer(string='From')
    range_to  = fields.Integer(string='To')
    percentage  = fields.Float(string='Paid %')
    
    
class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    sick_leave_deduction  = fields.Float(string='Sick Leave Deduction')

    def compute_sheet(self):
        self.get_sick_leave_deduction()
        super(hr_payslip , self).compute_sheet()

    def get_sick_leave_deduction(self):
        date = datetime.date.today().replace(day=1,month=1)
        for rec in self:
            rec.sick_leave_deduction = 0.0
            gross = rec.contract_id.wage or 0.0
            gross_day = 0.0
            if gross != 0.0:
                gross_day = gross/30
                
            number_of_days = 0.0
            leave_ids = self.env['hr.leave'].search([
                ('holiday_status_id.sick_rule','=', True) ,
                ('employee_id','=',rec.employee_id.id),
                ('state', '=' , 'validate'),
                ('request_date_from', '>=', date)
                ], order="request_date_from")
            
            for leave in leave_ids:
                number_of_days_temp = number_of_days
                number_of_days = number_of_days + leave.number_of_days
                if number_of_days > leave.holiday_status_id.minimum_allowed and  (leave.request_date_from.month == rec.date_from.month or leave.request_date_to.month == rec.date_from.month ):
                    delta = (rec.date_to - rec.date_from).days
                    for i in range( 0 , delta + 1 ):
                        day = rec.date_from + timedelta(days=i)
                        if day >= leave.request_date_from and day <= leave.request_date_to:
                            if leave.holiday_status_id.weekend_sick and ( day.weekday() == 4 or day.weekday() == 5):
                                pass
                            else:
                                number_of_days_temp += 1
                                rule_id = self.env['sick.leave.rule'].search([
                                    ('range_from','<=',number_of_days_temp),
                                    ('range_to','>=',number_of_days_temp),
                                    ('leave_type_id','=',leave.holiday_status_id.id)
                                    ], limit=1)
                                if rule_id:
                                    rec.sick_leave_deduction += gross_day*((100 - rule_id.percentage)/100)
