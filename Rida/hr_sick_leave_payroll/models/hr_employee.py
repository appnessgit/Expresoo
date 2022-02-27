# -*- coding: utf-8 -*-

from odoo import models, fields, api
from calendar import monthrange
import datetime,time
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sick_days = fields.Float(compute='_compute_sick_leaves', string='Sick Days')
    
    
    def _compute_sick_leaves(self):
        start_date = datetime.date.today().replace(day=1,month=1)
        end_date = datetime.date.today().replace(day=31,month=12)
        for rec in self:
            sick_records = rec.env['hr.leave'].search([
                ('employee_id','=',rec.id),
                ('holiday_status_id.sick_rule','=',True),
                ('request_date_from','>=',start_date),
                ('request_date_to','<=',end_date),
                ('state','=','validate'),
                ])
            sick_leaves = sum(sick_records.mapped('number_of_days'))
            rec.sick_days = sick_leaves

    """
    1- 14 = Full pay
    15 - 28 = 75%pay
    29 - 42  =50% pay
    43 - 70 = 25% pay
    71  - 90 = No pay
    """
    
    first_period = fields.Float(compute='_compute_period_days', string='1 - 14')
    second_period = fields.Float(compute='_compute_period_days', string='15 - 28')
    third_period = fields.Float(compute='_compute_period_days', string='29 - 42')
    forth_period = fields.Float(compute='_compute_period_days', string='43 - 70')
    fifth_period = fields.Float(compute='_compute_period_days', string='71  - 90')
    
 
    def _compute_period_days(self):
        for rec in self:
            if rec.sick_days > 14:
                if rec.sick_days <= 28:
                   rec.second_period = rec.sick_days - 14
                   rec.first_period = 14
                   rec.third_period = 0.0
                   rec.forth_period = 0.0
                   rec.fifth_period = 0.0
                elif 29 <=rec.sick_days <= 42:
                    rec.third_period = rec.sick_days - 28
                    rec.first_period = 14
                    rec.second_period = 14
                    rec.forth_period = 0.0
                    rec.fifth_period = 0.0
                elif 43 <=rec.sick_days <= 70:
                    rec.forth_period = rec.sick_days - 42
                    rec.first_period = 14
                    rec.second_period = 14
                    rec.third_period = 14
                    rec.fifth_period = 0.0
                elif 71 <=rec.sick_days <= 90:
                    rec.fifth_period = rec.sick_days - 70
                    rec.first_period = 14
                    rec.second_period = 14
                    rec.third_period = 14
                    rec.forth_period = 28
                else:
                    rec.first_period = 14
                    rec.second_period = 14
                    rec.third_period = 14
                    rec.forth_period = 28
                    rec.fifth_period = 20
            else:
                rec.first_period = rec.sick_days
                rec.second_period = 0.0
                rec.third_period = 0.0
                rec.forth_period = 0.0
                rec.fifth_period = 0.0