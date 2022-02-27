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


	custody_ids = fields.One2many('hr.custody', 'eos_id',readonly=False)

	@api.onchange('employee_id')
	def _get_custody(self):
		for rec in self:
			custodies = rec.employee_id.custody_id.filtered(lambda x: x.state == 'not_cleared')
			rec.custody_ids = custodies

	total_custodies = fields.Float(compute='_compute_total_custodies', string='Total Custodies Deducted', store=False)
	
	@api.depends('custody_ids')
	def _compute_total_custodies(self):
		for rec in self:
			amount_total = sum(rec.custody_ids.mapped('amount'))
			rec.total_custodies = amount_total

	@api.depends('total_deduction','total_custodies')
	def _get_ded_total_amount(self):
		for rec in self:
			rec.ded_total_amount =  rec.total_deduction + rec.total_custodies

	
			
	def submit(self):
		result = super(hr_end_service, self).submit()
		for rec in self:
			for line in rec.custody_ids:
				if line.state != 'cleared':
					raise UserError('Please Clear All Custodies')
				else:
					pass
		return result


class Custody(models.Model):
	_inherit = 'hr.custody'

	amount = fields.Float(string='Amount Deducted')
	eos_id = fields.Many2one("hr.end.service", "End Of Service", readonly=True)