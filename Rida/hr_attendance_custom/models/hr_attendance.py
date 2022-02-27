# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from pytz import timezone, UTC
import pytz
from datetime import datetime, timedelta
# from date import date


class hr_attendance_custom(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Employees attendance'

    justification = fields.Selection(string='Justification', selection=[('sick_leave', 'Sick Leave'), ('absent', 'Absent'), ('on_misiion', 'On Mission')])
    date_tz = fields.Selection('_tz_get', string='Timezone', required=True,default=lambda self: self.env.user.tz or 'UTC')
    default_check_in = fields.Datetime(string='Default Check in', compute='compute_default_check_in', store=True)
    default_check_out = fields.Datetime(string='Default Check out', compute='compute_default_check_out', store=True)
    color_bool = fields.Boolean()
#     work_hours_week= fields.Float(compute='compute_weekly_hours', string='Total',  readonly=True)
# default_check_out = fields.Datetime(string='Default Check out', default= datetime.today + '17:00:00')
#     work_hours_week = fields.Float(string='Work Hours', default = '8')  

#     amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    
#     @api.depends('worked_hours')
#     def compute_weekly_hours(self):
#         total = 0
#         for rec in self:
                # raise UserError(rec.worked_hours)
                # rec.work_hours_week +=rec.worked_hours
                # raise UserError(rec.worked_hours)
                
           

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]


    @api.depends('employee_id')
    def compute_default_check_in(self):
        for rec in self:
                for line in rec.employee_id.contract_ids.resource_calendar_id.attendance_ids[0]: 
                        #to get today's date and time field from employee work sheet 
                        today = fields.Datetime.today().replace(hour=int(line.hour_from))
                        #to fix issues of timezone 
                        rec.default_check_in = timezone(rec.date_tz).localize(today).astimezone(UTC).replace(tzinfo=None)
    
    @api.depends('employee_id')
    def compute_default_check_out(self):
        for rec in self:
                for line in rec.employee_id.contract_ids.resource_calendar_id.attendance_ids[0]: 
                        #to get today's date and time field from employee work sheet 
                        today = fields.Datetime.today().replace(hour=int(line.hour_to))
                        #to fix issues of timezone 
                        rec.default_check_out = timezone(rec.date_tz).localize(today).astimezone(UTC).replace(tzinfo=None)


    @api.onchange('default_check_in', 'check_in', 'default_check_out', 'check_out')
    def color_check_in(self):
        for rec in self:
                if rec.check_out:
                        if rec.default_check_in < rec.check_in:
                                rec.color_bool = False
                        elif rec.default_check_out > rec.check_out:   
                                rec.color_bool = False
                        else: 
                                rec.color_bool = True
                else:
                        pass
