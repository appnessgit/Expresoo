# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm, UserError
import itertools
import psycopg2
from datetime import datetime
from dateutil import relativedelta

class HrSalaryIncrease(models.Model):
    _name = 'hr.salary.increase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Salary Increments'

    name = fields.Char(string='Reference', required=True)
    employee_id = fields.Many2one('hr.employee','Employee')
    date = fields.Datetime('Effective Date')
    date_applied_on = fields.Datetime('Applied On')
    percentage = fields.Float(string="Percentage(%)")
    increase_type = fields.Selection([('promotion','Promotion'),('annual','Annual Increase'),('bonus','Bonus')],'Increase Type',default='annual')
    applied_for = fields.Selection([('employee','Employee'),('batch','Batch')],'Applied for',default='batch')
    # state = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('cancel','Rejected')], default='draft',track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('hr_mgr', 'Waitting HR Manager'),('confirm', 'Confirmed'), ('cancel', 'Rejected')], default='draft',
                             track_visibility='onchange')
    computed = fields.Boolean('Is Computed ?', default=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    

    line_ids = fields.One2many('hr.salary.increase.line', 'increase_id',hr_appraisalstring='Lines')

    def update_activities(self):
        for rec in self:
            users = []
            if rec.state not in ['draft','hr_mgr','confirm','cancel']:
                continue
            message = ""
            if rec.state == 'hr_mgr':
                users = self.env.ref('hr.group_hr_manager').users
                message = "Approve"

            elif rec.state == 'cancel':
                users = [self.create_uid]
                message = "Rejected"
            for user in users:
                self.activity_schedule('hr_salary_increment.mail_act_approval', user_id=user.id, note=message)

    
    @api.constrains('date','date_applied_on')
    def check_date(self):
        if self.date_applied_on and self.date_applied_on < self.date:
            raise UserError('Applied On Date must be greater than Effective Date!')


    def action_generate(self):
        domain = []
        employees = self.env['hr.employee'].search(domain)
        for employee in employees:
            if employee.contract_id:
                self.env['hr.salary.increase.line'].create({
                    'employee_id': employee.id,
                    'increase_id': self.id
                })
    

    def action_compute(self):
        for rec in self:
            for line in rec.line_ids:
                if not line.employee_id.contract_id:
                    continue
                amount = line.amount
                if line.employee_id.contract_id and line.increase_type in ['bonus']:
                    perc = line.percentage
                    if perc > 0:
                        amount = (line.employee_id.contract_id.basic * perc) / 100

                if line.employee_id.contract_id and line.increase_type in ['promotion', 'annual']:
                    perc = rec.percentage
                    if perc > 0:
                        amount = (line.employee_id.contract_id.basic * perc) / 100
                line.amount = amount
                line.basic = line.employee_id.contract_id.basic
                line.new_basic = line.employee_id.contract_id.basic + amount
        self.computed = True

    def action_submit(self):
        if not self.computed:
            raise UserError('Please compute before submit')
        for rec in self:
            rec.state = "hr_mgr"
            rec.update_activities()


    def action_confirm(self):
        self.action_compute()
        for line in self.line_ids:
            amount = line.amount
            if not line.date_applied_on:
                raise UserError('Please set Applied On Date')
            for rec in self.env['hr.payslip'].search([('employee_id','=',line.employee_id.id),('date_from','<=',line.date_applied_on),('date_to','>=',line.date_applied_on),('state','not in',['draft'])]):
                raise UserError('You cannot apply Bonus for this Month, Payroll is allready Confirmed!')
            if line.employee_id.contract_id and line.increase_type in ['bonus']:
                perc = line.percentage
                if perc > 0:
                    amount = (line.employee_id.contract_id.basic * perc) / 100
            if line.employee_id.contract_id and line.increase_type in ['promotion','annual']:
                perc = self.percentage
                if perc > 0:
                    amount = (line.employee_id.contract_id.basic * perc) / 100
                line.employee_id.contract_id.basic += amount
            line.amount = amount
        self.state = "confirm"
        self.activity_unlink(['hr_salary_increment.mail_act_approval'])

    def action_reject(self):
        for rec in self:
            rec.state = 'cancel'
        self.activity_unlink(['hr_salary_increment.mail_act_approval'])

    
    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'



class HRSalaryIncreaseLine(models.Model):
    _name = 'hr.salary.increase.line'

    increase_id = fields.Many2one('hr.salary.increase')
    employee_id = fields.Many2one('hr.employee', string="Name")
    include = fields.Boolean("Include?", default=True)
    date_applied_on = fields.Datetime('Applied On',related="increase_id.date_applied_on")
    date = fields.Datetime('Effective Date',related="increase_id.date")
    no_of_month = fields.Float(compute='compute_no_month')
    amount = fields.Float()
    state = fields.Selection([('draft', 'Draft'), ('hr_mgr', 'Waitting HR Manager'), ('confirm', 'Confirmed'), ('cancel', 'Rejected')],default='draft',
        track_visibility='onchange')
    note = fields.Char()
    percentage = fields.Float(string="Percentage(%)")
    computed = fields.Boolean('Is Computed ?', related="increase_id.computed")

    
    increase_type = fields.Selection([('promotion','Promotion'),('annual','Annual Increase'),('bounus','Bonus')],'Increase Type',related="increase_id.increase_type",readonly="True")
    basic = fields.Float("Basic")
    total_allowances = fields.Float("Total Allowances",)

    new_basic = fields.Float("New Basic")
    new_total_allowances = fields.Float("New Total Allowances",)


    @api.constrains('date','date_applied_on')
    def check_date(self):
        if self.date_applied_on < self.date:
            raise UserError('Applied On Date must be greater than Effective Date!')

    @api.depends('date','date_applied_on')
    def compute_no_month(self):
        for rec in self:
            rec.no_of_month = 0
            if rec.date and rec.date_applied_on:
                try:
                    effective_date = datetime.strptime(str(rec.date), '%Y-%m-%d %H:%M:%S')
                    applied_on_date = datetime.strptime(str(rec.date_applied_on), '%Y-%m-%d %H:%M:%S')
                except:
                    d1,m1 = str(rec.date).split('.')
                    d2,m2 = str(rec.date_applied_on).split('.')
                    effective_date = datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    applied_on_date = datetime.strptime(d2, '%Y-%m-%d %H:%M:%S')
                date = relativedelta.relativedelta(applied_on_date, effective_date)
                if date.months < 1 or rec.increase_type == 'promotion':
                    rec.no_of_month = 1 
                else:
                    rec.no_of_month = date.months