# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError
from odoo import exceptions

class SalaryAdvanceAccount(models.Model):
    _inherit = "salary.advance"



    state = fields.Selection([('draft', 'Draft'),
                              ('hr_manager', 'HR Manager Approval'),
                              ('finance', 'Finance Approval'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('reject', 'Rejected')], string='Status', default='draft', track_visibility='onchange')
    debit = fields.Many2one('account.account', string='Debit Account')
    credit = fields.Many2one('account.account', string='Credit Account')
    journal = fields.Many2one('account.journal', string='Journal')
    move_id = fields.Many2one('account.move', string="Journal Entry ", readonly=True)

    def update_activities(self):
        for rec in self:
            users = []
            rec.activity_unlink(['hr_salary_advance.mail_act_approval'])
            if rec.state not in ['draft','hr_officer','hr_manager','ceo','approve','reject']:
                continue
            message = ""
            if rec.state == 'hr_manager':
                users = self.env.ref('hr.group_hr_manager').users
                message = "Approve"

            if rec.state == 'finance':
                users = self.env.ref('account.group_account_user').users
                message = "Confirm"

            elif rec.state == 'reject':
                users = [self.create_uid]
                message = "Cancelled"
            for user in users:
                self.activity_schedule('hr_salary_advance.mail_act_approval', user_id=user.id, note=message)


    def action_hr_manager(self):
        """This Approve the employee salary advance request.
                   """
        emp_obj = self.env['hr.employee']
        # address = emp_obj.browse([self.employee_id.id]).address_home_id
        # if not address.id:
        #     raise except_orm('Error!', 'Define home address for the employee. i.e address under private information of the employee.')
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id),('id', '!=', self.id),('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Advance can be requested once in a month')
        if not self.employee_contract_id:
            raise UserError('Define a contract for the employee')
        adv = self.advance
        amt = self.employee_contract_id.basic

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

        self.state = 'finance'
        self.update_activities()


    def approve_request_acc_dept(self):
        """This Approve the employee salary advance request from accounting department.
                   """
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month
        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise UserError('Advance can be requested once in a month')
        if not self.debit or not self.credit or not self.journal:
            raise UserError("You must enter Debit & Credit account and journal to approve ")
        if not self.advance:
            raise UserError('You must Enter the Salary Advance amount')

        move_obj = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for request in self:
            amount = request.advance
            request_name = request.employee_id.name
            reference = request.name
            journal_id = request.journal.id
            move = {
                'narration': 'Salary Advance Of ' + request_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
            }

            debit_account_id = request.debit.id
            credit_account_id = request.credit.id

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': request_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': request_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
            move.update({'line_ids': line_ids})
            print("move.update({'line_ids': line_ids})",move.update({'invoice_line_ids': line_ids}))
            draft = move_obj.create(move)
            draft.post()
            request.move_id = draft.id
            self.state = 'approve'
            self.activity_unlink(['hr_overtime.mail_act_approval'])
            return True
