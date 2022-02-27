# -*- coding: utf-8 -*-
import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
					('fired', 'Terminated by Company ')]


class HrResignation(models.Model):
	_name = 'hr.resignation'
	_inherit = 'mail.thread'
	_rec_name = 'employee_id'

	name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,default=lambda self: _('New'))
	emp_code = fields.Char(string="Emp Code",readonly=True, related="employee_id.emp_code")
	employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id,help='Name of the employee for whom the request is creating')
	department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',help='Department of the employee')
	approved_revealing_date = fields.Date(string="Approved Last Day Of Employee",help='Date on which the request is confirmed by the manager.',track_visibility="always")
	joined_date = fields.Date(string="Join Date", required=False, readonly=True, related="employee_id.joining_date",help='Joining date of the employee.i.e Start date of the first contract')
	request_date = fields.Date(string="Request Date", required=True,help='Request date of resignation')
	expected_revealing_date = fields.Date(string="Last Day of Employee", required=True,help='Employee requested date on which he is revealing from the company.')
	reason = fields.Text(string="Reason", required=True, help='Specify reason for leaving the company')
	state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('approved', 'Approved'), ('cancel', 'Rejected')],string='Status', default='draft', track_visibility="always")
	resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Select the type of resignation: normal ""resignation or Terminated by Company ", required=True)
	employee_contract = fields.Char(String="Contract")
	eos_id = fields.Many2one('hr.end.service')
	eos_count = fields.Integer(string='')

	@api.model
	def create(self, vals):
		# assigning the sequence for the record
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
		res = super(HrResignation, self).create(vals)
		return res

	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise ValidationError(_('Only draft records can be deleted!'))
		super(HrResignation, self).unlink()

	@api.constrains('employee_id')
	def check_employee(self):
		# Checking whether the user is creating leave request of his/her own
		for rec in self:
			if not self.env.user.has_group('hr.group_hr_user'):
				if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
					raise ValidationError(_('You cannot create request for other employees'))

	@api.onchange('employee_id')
	@api.depends('employee_id')
	def check_request_existence(self):
		# Check whether any resignation request already exists
		for rec in self:
			if rec.employee_id:
				resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																		 ('state', 'in', ['confirm', 'approved'])])
				if resignation_request:
					raise ValidationError(_('There is a resignation request in confirmed or'
											' approved state for this employee'))
				if rec.employee_id:
					no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
					for contracts in no_of_contract:
						if contracts.state == 'open':
							rec.employee_contract = contracts.name

	@api.constrains('joined_date')
	def _check_dates(self):
		# validating the entered dates
		for rec in self:
			resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																	 ('state', 'in', ['confirm', 'approved'])])
			if resignation_request:
				raise ValidationError(_('There is a resignation request in confirmed or'
										' approved state for this employee'))

	def submit_resignation(self):
		for rec in self:
			rec.state = 'submit'

	def cancel_resignation(self):
		for rec in self:
			rec.state = 'cancel'

	def reject_resignation(self):
		for rec in self:
			rec.state = 'cancel'

	def reset_to_draft(self):
		for rec in self:
			rec.state = 'draft'
			employee = rec.employee_id

			employee.update({
				'active': True,
				'resigned': False,
				'fired': False,
			})
			rec.employee_id.contract_id.state = 'open'


	def approve_resignation(self):
		for rec in self:
			if rec.approved_revealing_date:
				if rec.expected_revealing_date:
					no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
					for contracts in no_of_contract:
						if contracts.state == 'open':
							rec.employee_contract = contracts.name
							rec.state = 'approved'
							contracts.state = 'close'

					# Changing state of the employee if resigning today
					if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
						# rec.employee_id.active = False

						# Changing fields in the employee table with respect to resignation
						rec.employee_id.resign_date = rec.approved_revealing_date
						if rec.resignation_type == 'resigned':
							rec.employee_id.resigned = True
						else:
							rec.employee_id.fired = True
						# deactivating user
						if rec.employee_id.user_id:
							rec.employee_id.user_id.active = False
							# rec.employee_id.user_id = None
					else:
						raise ValidationError(_('Date Today must be greater than or equal Last Day of Employee '))
				else:
					raise ValidationError(_('expected_revealing_date'))

			else:
				raise ValidationError(_('Approved Last Day Of Employee'))

			rec.state = 'approved'

	
	def create_eos_req(self):
		for rec in self:
			if rec.eos_id:
				raise ValidationError(_('You already create eos record, please delete it first to create another one'))
			else:
				if rec.employee_id:
					req_dict = {
						'employee_id':rec.employee_id.id,
						'eos_type':1,
						'end_date':rec.approved_revealing_date if rec.approved_revealing_date else rec.expected_revealing_date ,
						'resign_id':rec.id,
					}
					eos_request = rec.env['hr.end.service'].create(req_dict)
					rec.eos_id = eos_request.id
					rec.eos_count = 1	
				else:
					raise ValidationError(_('Please Select the employee first'))
	
	def employee_eos_button(self):
		for rec in self:
			return {
			'name': _('End of Service'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.end.service',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', '=', rec.eos_id.id)],
		}
	

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	resign_date = fields.Date('Resign Date', readonly=True, help="Date of the resignation")
	resigned = fields.Boolean(string="Resigned", default=False, store=True,help="If checked then employee has resigned")
	fired = fields.Boolean(string="Fired", default=False, store=True, help="If checked then employee has fired")

	joining_date = fields.Date(string='Joining Date',
							   help="Employee joining date computed from the contract start date",
							   compute='compute_joining', store=True)

	@api.depends('contract_id', 'contract_id.date_start')
	def compute_joining(self):
		if self.contract_id:
			date = min(self.contract_id.mapped('date_start'))
			self.joining_date = date
		else:
			self.joining_date = False

class HrContract(models.Model):
	_inherit = 'hr.contract'

	resign_date = fields.Date('Resign Date', readonly=True, help="Date of the resignation", related='employee_id.resign_date')
	resigned = fields.Boolean(string="Resigned", default=False, store=True,help="If checked then employee has resigned" , related='employee_id.resigned')
	fired = fields.Boolean(string="Fired", default=False, store=True, help="If checked then employee has fired",related='employee_id.fired')
