# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError
from odoo import exceptions


class SalaryAdvancePayment(models.Model):
    _name = "salary.advance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', readonly=True, default=lambda self: 'Adv/')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, help="Employee")
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.today(), help="Submit date")
    reason = fields.Text(string='Reason', help="Reason")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    advance = fields.Float(string='Advance', required=True)
    payment_method = fields.Many2one('account.journal', string='Payment Method')
    exceed_condition = fields.Boolean(string='Exceed Than Maximum',
                                      help="The Advance is greater than the maximum percentage in salary structure")
    department = fields.Many2one('hr.department', string='Department')
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_manager', 'HR Manager Approval'),
                              ('ccso', 'CCSO Approval'),
                              ('approve', 'Approved'),
                              ('finance', 'Finance Approval'),
                              ('paid', 'Paid'),
                              ('cancel', 'Cancelled'),
                              ('reject', 'Rejected')], string='Status', default='draft', track_visibility='onchange')

    employee_contract_id = fields.Many2one('hr.contract', string='Contract')
    last_salary = fields.Monetary(compute='_compute_last_salary', readonly=True, store=True )
    
    @api.depends('employee_id')
    def _compute_last_salary(self):
        # for record in self:
        #     payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)])
        #     for slip in payslip:
        #         if record.date.month >= slip.date_from.month:
        #             record.last_salary = payslip.net_wage
        last_payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),('state','=','done')],limit=1,order='date_from desc')
        self.last_salary = last_payslip.net_wage


    # Smart Button for last net salary
    def smart_count_of_last_salary(self):
        return {
            'name': ('Net Salary'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'hr.payslip',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': "{'create': False}",
            'domain': [('employee_id','=', self.employee_id.id),('state','=','done')],
            'limit':1,
            'order':'date_from desc'
        }
        
        
        

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('salary.advance.seq') or ' '
        res_id = super(SalaryAdvancePayment, self).create(vals)
        return res_id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        department_id = self.employee_id.department_id.id
        domain = [('employee_id', '=', self.employee_id.id)]
        if self.employee_id:
            self.employee_contract_id = self.sudo().employee_id.contract_id
        return {'value': {'department': department_id}, 'domain': {
            'employee_contract_id': domain,
        }}

    @api.onchange('company_id')
    def onchange_company_id(self):
        company = self.company_id
        domain = [('company_id.id', '=', company.id)]
        result = {
            'domain': {
                'journal': domain,
            },

        }
        return result

    def update_activities(self):
        for rec in self:
            users = []
            rec.activity_unlink(['hr_salary_advance.mail_act_approval'])
            if rec.state not in ['draft','hr_manager','ccso','approve','finance','paid','reject']:
                continue
            message = ""
            if rec.state == 'hr_manager':
                users = self.env.ref('hr.group_hr_manager').users
                message = "Approve" 
            elif rec.state == 'reject':
                users = [self.create_uid]
                message = "Cancelled"
            for user in users:
                self.activity_schedule('hr_salary_advance.mail_act_approval', user_id=user.id, note=message)

    def action_submit(self):
        for rec in self:
            rec.state = 'hr_manager'
            rec.update_activities()

    def action_hr_manager(self):
        """This Approve the employee salary advance request.
                   """
        emp_obj = self.env['hr.employee']
        # address = emp_obj.browse([self.employee_id.id]).address_home_id
        # if not address.id:
        #     raise except_orm('Error!', 'Define home address for the employee. i.e address under private information of the employee.')
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id),('id', '!=', self.id),('state', '=', 'paid')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month
        count = self.search_count([('employee_id', '=', self.employee_id.id),('id', '!=', self.id),('state', '=', 'paid')])
        current_year = datetime.strptime(str(self.date), '%Y-%m-%d').date().year
        for each_advance in salary_advance_search:  
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            existing_year = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().year
            if current_month == existing_month:
                raise UserError('Advance can be requested once in a month')
            if current_year == existing_year and count > 3:
                raise UserError('Advance can not be requested for more than 3 times in the year')

        if not self.employee_contract_id:
            raise UserError('Define a contract for the employee')
        adv = self.advance
        amt = self.employee_contract_id.payroll_wage

        if adv > amt and not self.exceed_condition:
            raise UserError('Advance amount is greater than allowed amount')

        if not self.advance:
            raise UserError('You must Enter the Salary Advance amount')
        payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),
                                                     ('state', '=', 'done'), ('date_from', '<=', self.date),
                                                     ('date_to', '>=', self.date)])
        if payslip_obj:
            raise UserError("This month salary already calculated")

        for slip in self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)]):
            slip_moth = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().month
            if current_month == slip_moth + 1:
                slip_day = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().day
                current_day = datetime.strptime(str(self.date), '%Y-%m-%d').date().day

        self.state = 'ccso'
        self.update_activities()

    def action_ccso(self):
        for rec in self:
            rec.state = 'finance'
            rec.update_activities()

    def action_fainance(self):
        for rec in self:
            rec.state = 'paid'
            rec.update_activities()


            
    def reject(self):
        for rec in self:
            rec.state = 'reject'

    def cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'


    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("You cannot delete this Request. Only DRAFT Requests can be deleted.")
            return super(SalaryAdvancePayment, self).unlink()

