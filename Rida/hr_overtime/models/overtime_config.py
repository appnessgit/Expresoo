# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api
import time
from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError




class Company(models.Model):
	_inherit = "res.company"

 # employee overtime 
	hours_normal_rate = fields.Float(string="Day Hours Rate",store=True)
	hours_night_rate = fields.Float(string="Night Hours Rate ",store=True)
	hours_weekend_rate = fields.Float(string="Weekend Hours Rate",store=True)
	hours_holiday_rate = fields.Float(string="Holiday Day Rate",store=True)

	# Select Overtime Salary Calaculation
	normal_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],default='basic'  ,string='Day Rate Salary')
	night_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')] ,default='basic', string='Night Rate Salary')
	weekend_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')] ,default='basic', string='Weekend Rate Salary')
	holiday_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],default='basic' , string='Holiday Rate Salary')
 
 # Site employee overtime 
	hours_normal_rate_site = fields.Float(string="Day Hours Rate",store=True)
	hours_night_rate_site = fields.Float(string="Night Hours Rate ",store=True)
	hours_weekend_rate_site = fields.Float(string="Weekend Hours Rate",store=True)
	hours_holiday_rate_site = fields.Float(string="Holiday Day Rate",store=True)

	# Select Overtime Salary Calaculation
	normal_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')] ,default='basic' ,string='Day Rate Salary')
	night_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],default='basic' , string='Night Rate Salary')
	weekend_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],default='basic' , string='Weekend Rate Salary')
	holiday_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')] ,default='basic', string='Holiday Rate Salary')


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

 # employee overtime 
	hours_normal_rate=fields.Float(string="Day Hours Rate",related='company_id.hours_normal_rate',store=True, readonly=False)
	hours_night_rate=fields.Float(string="Night Hours Rate ",related='company_id.hours_night_rate',store=True, readonly=False)
	hours_weekend_rate=fields.Float(string="Weekend Hours Rate",related='company_id.hours_weekend_rate',store=True, readonly=False)
	hours_holiday_rate=fields.Float(string="Holiday Day Rate",related='company_id.hours_holiday_rate',store=True, readonly=False)

	normal_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.normal_rate_salary',default='basic'  ,string='Day Rate Salary', readonly=False)
	night_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.night_rate_salary' ,default='basic', string='Night Rate Salary', readonly=False)
	weekend_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.weekend_rate_salary' ,default='basic', string='Weekend Rate Salary', readonly=False)
	holiday_rate_salary = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.holiday_rate_salary',default='basic' , string='Holiday Rate Salary', readonly=False)
 
  # Site employee overtime 
	hours_normal_rate_site=fields.Float(string="Day Hours Rate",related='company_id.hours_normal_rate_site',store=True, readonly=False)
	hours_night_rate_site=fields.Float(string="Night Hours Rate ",related='company_id.hours_night_rate_site',store=True, readonly=False)
	hours_weekend_rate_site=fields.Float(string="Weekend Hours Rate",related='company_id.hours_weekend_rate_site',store=True, readonly=False)
	hours_holiday_rate_site=fields.Float(string="Holiday Day Rate",related='company_id.hours_holiday_rate_site',store=True, readonly=False)

	normal_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.normal_rate_salary_site' ,default='basic' ,string='Day Rate Salary', readonly=False)
	night_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.night_rate_salary_site',default='basic' , string='Night Rate Salary', readonly=False)
	weekend_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.weekend_rate_salary_site',default='basic' , string='Weekend Rate Salary', readonly=False)
	holiday_rate_salary_site = fields.Selection([('basic', 'Basic'),('gross', 'Gross')],related='company_id.holiday_rate_salary_site',default='basic' , string='Holiday Rate Salary', readonly=False)