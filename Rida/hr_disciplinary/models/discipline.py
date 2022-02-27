
import logging

from odoo import fields, models, api, _
import time
import datetime
from datetime import datetime, timedelta
from dateutil import relativedelta
from datetime import date
from odoo.exceptions import ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
from datetime import datetime, timedelta
import math
from odoo import tools, _
from odoo.modules.module import get_module_resource

class hr_violation_category(models.Model):
    """This class is used to record violation types."""
    _name = 'hr.violation.category'
    
    name = fields.Char('Name')

class hr_violation(models.Model):
    """This class is used to record violation types."""
    _name = 'hr.violation'

    name = fields.Char('Violation Name')
    type = fields.Selection([('minor','Minor'),('second','Second Offence')],'Type')
    sanction_ids = fields.One2many('hr.sanction', 'violation_id', 'Penalties')
    category_id = fields.Many2one('hr.violation.category','Violation Category')

class hr_sanction(models.Model):
    """This class is used to record sanction types"""
    _name = 'hr.sanction'
    name = fields.Char('Penalty Name')
    violation_id = fields.Many2one('hr.violation', 'Violation')

class hr_employee_discipline(models.Model):
    """This class is used to record employees sanctions."""
    _name = 'hr.employee.discipline'
    _rec_name='employee_id'
    _inherit = ['mail.thread', 'hr.violation']

    employee_id = fields.Many2one('hr.employee', 'Employee')
    state = fields.Selection([('draft','Draft'),('hr_manager','Hr manager Confirm'),('confirm','Confirmed'),('cancel','Canceled'),('expired','Expired')],'State',default='draft')
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    currency_id = fields.Many2one('res.currency')
    emp_salary = fields.Monetary(string="Employee Salary",related='employee_id.contract_id.wage')
    job_id = fields.Many2one('hr.job', related="employee_id.job_id",string="Job")
    violation_id = fields.Many2one('hr.violation', 'Violation')
    violation_type = fields.Selection([],'Violation Type',related="violation_id.type",readonly=True)
    suspend_payroll = fields.Boolean('Suspend Payroll')
    terminate_employee = fields.Boolean('Terminate Contract')
    salary_id = fields.Many2one('hr.payslip', 'Salary')
    # eos_id = fields.Many2one('hr.end.service','Eos')
    violation_date = fields.Date(string="Violation date" ,required=True, copy=False,default=time.strftime('%Y-%m-01'))
    line_ids = fields.One2many('hr.sanction.line', 'line_id', 'Penalties Line')
    month = fields.Integer('Month')
    year = fields.Integer('Year')
    total_amount = fields.Float('Total Amount')
    # company_id = fields.Many2one('res.company', string='Company', copy=False,default=lambda self: self.env['res.company']._company_default_get('hr.employee.discipline'))
    note = fields.Text('Discription of Vaiolation')
    improve = fields.Text('Plan Fro Improvement')
    conseq = fields.Text('Consequences of Further Infractions')
    company_id = fields.Many2one("res.company", string="Branch", related="employee_id.company_id", store=True, readonly=True)

    _sql_constraints = [
        ('unique_violation_id_employee_id', 'UNIQUE(violation_id,employee_id)',
         "this Employee had already this violation!!!"),]

    # delete displine if all state is draft
    @api.model
    def _cron_check_discipline(self):
        disciplines = self.env['hr.employee.discipline'].search([('state','in',['draft'])])
        for rec in disciplines:
            today = datetime.now().date()
            violation_date = rec.violation_date
            if (today - rec.violation_date).days > 180:
                rec.state = 'expired'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_submit(self):
        for rec in self:
            rec.state = 'hr_manager'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    @api.depends('violation_type')
    @api.onchange('violation_type')
    def _onchange_violation_type(self):
        self.suspend_payroll = False
        self.terminate_employee = False

    def unlink(self):
        conunt=0
        for rec in self:
           for line in rec.line_ids:
              if line.state == 'confirm':
                 raise UserError(_('You Cannot Delete a Discipline Because Contain Snaction Not Draft !!!!'))
           return super(hr_employee_discipline, self).unlink()

    @api.depends('violation_id')
    def get_sanction_violation(self):
            x = 0
            seq = 0

            """This function get the sanction_ids in specific violation
            @return: Dictionary of values(sanction_ids)"""
            violation_id = self._context.get('violation_id', False)
            employee_id = self.employee_id
            if violation_id:
                sanction_ids = self.env['hr.sanction'].search([('violation_id', '=', violation_id)])
                schedules = self.env['hr.employee.discipline'].search([])
                for schedule in schedules:
                        for line in schedule.line_ids:
                            line.search([('line_id', '=', self.id),('state','!=','confirm')]).unlink()
                sanction_list =[]
                for sanction in sanction_ids:
                    if sanction.id  in sanction_list:
                        print ("sanction.id", sanction.id)
                        continue

                    else:
                        self.write({'line_ids': [(0, 0, {'sanction_id': sanction.id,'employee_id': self.employee_id.id ,'sequence':seq})]})
            return True

    def get_compute_total(self):

        records = 	self.env['hr.sanction.line'].search([])
        employee_id = self.employee_id
        for record in records:
           employee=record.employee_id
           if employee==employee_id and record.state == 'draft':
              if record.deducted == True:
                 wage = self.emp_salary
                 if record.percentage == 'day':
                     y = wage / 30
                     amount = y * record.num
                     record.amount = amount
                 else:
                     y = wage / 240
                     amount = y * record.num
                     record.amount = amount
        return True

class hr_sanction_line(models.Model):
    """This class records Employee sanction Scheduling"""
    _name = 'hr.sanction.line'
    
    sequence = fields.Integer('Sequence')
    sanction_id = fields.Many2one('hr.sanction', 'Penalty')
    date = fields.Date(string="Penalty Date")
    line_id = fields.Many2one('hr.employee.discipline', 'Penalty',ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    salary_id = fields.Many2one('hr.payslip')
    percentage = fields.Selection([('day', 'Day'),('hour', 'Hours')], 'Deduction Type')
    num = fields.Float('Number', default='1')
    amount = fields.Float(string="Deducted Amount")
    deducted = fields.Boolean('Deducted')
    printed = fields.Boolean('Print')
    remark = fields.Text('Remark')
    state = fields.Selection([('draft', 'Draft') ,('confirm', 'Confirmed')], default='draft')
    month = fields.Integer('Month')
    year = fields.Integer('Year')
    total_sanction = fields.Float('Total Sanction')

    def confirm(self):
        self.write({'state': 'confirm'})
        return True

    def draft(self):
        if self.slip_id:
            raise UserError('You cannot reset Penalties that linked to Payroll')
        else:
            self.write({'state': 'draft'})
        return True

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot Delete Confirmed record'))
        return super(hr_sanction_line, self).unlink()





