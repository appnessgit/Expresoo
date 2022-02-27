from odoo import fields , api , models , _
import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
import math
from odoo.tools import float_round
from odoo.tools.misc import format_date
from calendar import monthrange
import json


class hr_end_service(models.Model):
	_inherit = 'hr.end.service'

	loan_ids = fields.One2many('hr.loan', 'eos_id', compute="_get_loan", readonly=False)

	@api.depends('employee_id')
	def _get_loan(self):
		for rec in self:
			loans = rec.env['hr.loan'].search([('employee_id','=',rec.employee_id.id),('state','=','approve'),('balance_amount','!=',0)])
			rec.loan_ids = loans

	total_loans = fields.Float(compute='_compute_total_loans', string='Total Loans Deducted', store=False)
	
	@api.depends('loan_ids')
	def _compute_total_loans(self):
		for rec in self:
			amount_total = sum(rec.loan_ids.mapped('balance_amount'))
			rec.total_loans = amount_total

	@api.depends('total_deduction','total_custodies','total_loans')
	def _get_ded_total_amount(self):
		for rec in self:
			rec.ded_total_amount =  rec.total_deduction + rec.total_custodies + rec.total_loans


class HRLoan(models.Model):
	_inherit = 'hr.loan'

	eos_id = fields.Many2one("hr.end.service", "End Of Service", readonly=True)
	


		