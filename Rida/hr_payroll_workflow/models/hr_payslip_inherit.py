# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import base64

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval


class hr_payroll_workflow(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Added workflows to payroll stages'
   
    salary_currency = fields.Many2one(related='contract_id.salary_currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('director_approve','HR Director Approve'),
        ('ccso_approve','CCSO Approve'),
        ('verify','Finance Approve'),
        ('done', 'Confirmed'),
        ('cancel', 'Rejected'),
        ('to_pay','To pay') 
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Confirmed\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")



    def compute_sheet(self):
        res = super(hr_payroll_workflow,self).compute_sheet()
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify','director_approve','ccso_approve'])
        for payslip in payslips:
            payslip.write({'state':'draft'})
        return res

    # Submit Button function
    def submit_draft_state(self):  
        self.write({'state': 'director_approve'})

    # HR Director Approve Button function
    def director_approve_state(self):  
        self.write({'state': 'ccso_approve'})

    # CCSO Approve Button function
    def ccso_approve_state(self):  
        self.write({'state': 'verify'})

    def action_payslip_done(self):
        """
            Generate the accounting entries related to the selected payslips
            A move is created for each journal and for each month.
        """
        res = super(hr_payroll_workflow, self).action_payslip_done()
        self._action_create_account_move()
        return res




class hr_payroll_workflow_run(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Added workflows to payroll stages'
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('director_approve','HR Director Approve'),
        ('ccso_approve','CCSO Approve'),
        ('verify', 'Finance Approve'),
        ('close','Confirmed'),
        ('to_pay','To pay'),
        ('cancel', 'Rejected')], string='Status', index=True, readonly=True, copy=False, default='draft')
    currency_id = fields.Many2one("res.currency",required=True,default=lambda self: self.env.company.currency_id,tracking=True)
    structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    # Submit Button function
    def set_to_submit_state_batch(self):  
        self.write({'state': 'director_approve'})
        self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel').submit_draft_state()


    # HR Director Approve Button function
    def set_to_director_approve_state_batch(self):  
        self.write({'state': 'ccso_approve'})
        self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel').director_approve_state()

    # CCSO Approve Button function
    def set_to_ccso_approve_state_batch(self):  
        self.write({'state': 'verify'})
        self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel').ccso_approve_state()
   
   


    # cancel button
    # def cancel_of_batch(self):
    #     if any(self.filtered(lambda payslip_run: payslip_run.state in ('paid'))):
    #         raise UserError(_('You cannot delete a payslip batch which is in paid'))
    #     if any(self.mapped('slip_ids').filtered(lambda payslip: payslip.state in ('paid'))):
    #         raise UserError(_('You cannot delete a payslip which is in paid'))
    #     else:
    #         self.write({'state': 'cancel'})
    #         self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel').set_to_ccso_approve_state()

class HrContract(models.Model):
    _inherit = 'hr.contract'

    salary_currency = fields.Many2one("res.currency",required=True,string="Contract Currency",default=lambda self: self.env.company.currency_id)
