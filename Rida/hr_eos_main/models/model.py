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

	_name = 'hr.end.service'
	_description = 'HR End Of Service'
	_inherit = ['mail.thread','mail.activity.mixin', 'image.mixin']

	_rec_name = "employee_id"

	TYPE2JOURNAL = {
		'out_invoice': 'sale',
		'in_invoice': 'purchase',
		'out_refund': 'sale',
		'in_refund': 'purchase',
	}

	date = fields.Date("Date", required=True,default=datetime.date.today())
	employee_id = fields.Many2one("hr.employee", "Employee", required=True)
	contract_id = fields.Many2one("hr.contract", "Contract", related="employee_id.contract_id", store=True)
	eos_type = fields.Many2one("hr.eos.type", string="Case", required=True)
	join_date = fields.Date("Join Date", related="contract_id.date_start", store=True, readonly=True)
	end_date = fields.Date("End Service Date", default=datetime.date.today() ,required=True)
	years = fields.Float("Years", compute="get_service_time", store=True, readonly=True)
	months = fields.Float("Months", compute="get_service_time", store=True, readonly=True)
	days = fields.Float("Days", compute="get_service_time", store=True, readonly=True)
	note = fields.Text("Note")
	currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
	company_id = fields.Many2one("res.company", string="Company", related="employee_id.company_id", store=True,readonly=True)
	emp_age = fields.Integer(string='Age', compute="_comp_age")
	state = fields.Selection([('draft', 'Draft'),
							  ('hrm', 'Waitting HR Manager Approval'),
							  ('confirm', 'Confirmed'),
							  ('cancel', 'Rejected')
							  ], default="draft", string="status",track_visibility='onchange')

	# Payslip
	slip_id = fields.Many2one('hr.payslip', string='Pay Slip')
	payslip_count = fields.Integer(string='')
	# Resignation module
	resign_id = fields.Many2one('hr.resignation')

	##custom
	# custody_id = fields.Many2one("account.custody")
	clear_date = fields.Date("clear date")

	# Leaves Settlement
	leave_days = fields.Float("Remaining Leaves", compute="_get_leaves", readonly=True, store=True)
	leaves_amount = fields.Float("Leaves Amount", compute="_get_leaves", readonly=True, store=True)

	gross = fields.Monetary("Gross", related='contract_id.payroll_wage')
	basic = fields.Float("Basic", related='contract_id.basic')

	# Benfits
	gratuity_id = fields.Many2one('hr.gratuity.configuration')
	benefit_amount = fields.Float(string='Benefit Amount')
	benefit_line_ids = fields.One2many('hr.benefit.line', 'eos_id', string='')



	# Overtime
	overtime = fields.Float(string='Total Overtime Amount', compute='_compute_overtime', readonly=True)

	# Other Allowance
	other_allowances_ids = fields.One2many('hr.eos.other.allowance', 'eos_id', string='Other Allowances')
	total_allowances = fields.Float(compute='_compute_allowances_total', string='Total Allowances', store=False)

	# Other Deduction
	other_deductions_ids = fields.One2many('hr.eos.other.deduction', 'eos_id', string='Other Deduction')
	total_deduction = fields.Float(compute='_compute_deductions_total', string='Total Deductions', store=False)

	# Gross Allowance 6 month basic
	gross_allowance = fields.Float("6 Months Basic", compute="get_gross_allowance", store=True)

	# end of service total amount
	allow_total_amount = fields.Float("Allowance Total Amount", compute="_get_allow_total_amount", store=True)
	ded_total_amount = fields.Float("Deduction Total Amount", compute="_get_ded_total_amount", store=True)

	total_amount = fields.Float("Total Amount", compute="_get_total_amount", store=True)
	amount_char = fields.Text("Amount(Character)", compute="compute_char_amount", store=True)

	# End Of Service
	end_service = fields.Float("End Of Service", compute="get_end_service")


	custody_installed = fields.Boolean(compute='_check_installed_module', string='')
	accounting_installed = fields.Boolean(compute='_check_installed_module', string='')
	loan_installed = fields.Boolean(compute='_check_installed_module', string='')

	def _check_installed_module(self):
		custody = self.env['ir.module.module'].search([('name', '=', 'hr_eos_custody')])
		loan = self.env['ir.module.module'].search([('name', '=', 'hr_eos_loan_accounting')])
		accounting = self.env['ir.module.module'].search([('name', '=', 'hr_eos_accounting')])
		self.accounting_installed = False
		self.custody_installed = False
		self.loan_installed = False
		if custody and custody.state == 'installed':
			self.custody_installed = True
		if loan and loan.state == 'installed': 
			self.loan_installed = True
		if accounting and accounting.state == 'installed':
			self.accounting_installed = True


	def create_payslip_button(self):
		if self.slip_id:
			raise UserError('You already created a payslip, Please delete it first ')
		else:
			count = 0
			for rec in self:
				payslip_obj = rec.env['hr.payslip']
				y, m, d = str(rec.end_date).split('-')
				start_date = datetime.date(int(y), int(m), int(1))
				payslip_name = _('End Of Service Salary Slip')
				record_dict = {
					'employee_id': rec.employee_id.id,
					'contract_id': rec.contract_id.id,
					'date_from':start_date,
					'date_to':rec.end_date,
					'struct_id':rec.contract_id.eos_struct_id.id,
					'name': '%s - %s - %s' % (payslip_name, self.employee_id.name or '', format_date(self.env, self.end_date, date_format="MMMM y")),
					'eos_id': rec.id,
				}
		
				slip_id = payslip_obj.create(record_dict)
				slip_id.compute_sheet()
				rec.slip_id = slip_id.id
				count+= 1
			self.payslip_count = count


	def employee_payslip_button(self):
		for rec in self:
			return {
			'name': _('Payroll'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.payslip',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', '=', rec.slip_id.id)],
		}

	def update_activities(self):
		for rec in self:
			users = []
			rec.activity_unlink(['hr_eos_main.mail_eos_approve'])
			if rec.state not in ['hrm','cancel']:
				continue
			message = ""
			if rec.state == 'hrm':
				users = self.env.ref('hr.group_hr_manager').users
				message = "Approve"

			elif rec.state == 'cancel':
				users = [self.create_uid]
				message = "cancelled"
			for user in users:
				self.activity_schedule('hr_eos_main.mail_eos_approve', user_id=user.id, note=message)

	def submit(self):
		for rec in self:
			hr_manager_user = []
			hr_manager_user = rec.env.ref('hr.group_hr_manager').users
			hr_managers = rec.env.ref('hr.group_hr_manager').users.mapped('employee_ids')
			emails = [manager.work_email for manager in hr_managers]
			for manager_user in hr_manager_user:
				mail_content = "  Hello  "  ",<br> There is a End of service  request for employee " + str(
					rec.employee_id.name) \
							   + " with employee code of " + str(
					rec.employee_id.emp_code) + " Please review the request for Approval."
				main_content = {
					'subject': _('EOS of %s') % (rec.employee_id.name),
					'author_id': rec.env.user.partner_id.id,
					'body_html': mail_content,
					'email_to': emails,
				}
				rec.env['mail.mail'].sudo().create(main_content).send()
			rec.state = 'hrm'
			rec.update_activities()

	def action_hrm_reject(self):
		for rec in self:
			rec.state = 'cancel'
			self.activity_unlink(['hr_eos_main.mail_eos_approve'])

	def confirm_button(self):
		for rec in self:
			rec.state = 'confirm'
			self.activity_unlink(['hr_eos_main.mail_eos_approve'])
			rec.employee_id.contract_id.state='close'
			rec.employee_id.active=False
			# rec.employee_id.user_id.active=False
			emails = rec.employee_id.work_email
			mail_content = "  Hello  "  ",<br> Your End of service  Settlement was approved by HR."
			main_content = {
				'subject': _('EOS of %s') % (rec.employee_id.name),
				'author_id': rec.env.user.partner_id.id,
				'body_html': mail_content,
				'email_to': emails,
			}
			rec.env['mail.mail'].sudo().create(main_content).send()

	def action_set_draft(self):
		for rec in self:
			rec.state = 'draft'


	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise UserError("You cannot delete this  Request. Only DRAFT Requests can be deleted.")
		return super(hr_end_service, self).unlink()


	@api.depends('employee_id.birthday')
	def _comp_age(self):
		age=0
		for rec in self:
			if rec.employee_id.birthday:
				y, m, d = str(rec.employee_id.birthday).split('-')
				d1 = datetime.date(int(y), int(m), int(d))

				date_today = datetime.date.today()
				y, m, d = str(date_today).split('-')
				d2 = datetime.date(int(y), int(m), int(d))

				diff = relativedelta(d2, d1)
				age = diff.years
				rec.emp_age=age
			else:
				rec.emp_age=age


	@api.onchange('gratuity_id','basic')
	def get_benefit_amount(self):
		for rec in self:
			if rec.contract_id.employee_benefits and rec.gratuity_id:
				employee_months = (rec.years * 12) + rec.months
				month_basic = rec.basic / 12
				total_benefits = 0
				lines = [(5, 0, 0)]
				for rule in rec.gratuity_id.gratuity_configuration_line:
					from_months = (rule.from_year * 12)
					to_months =  (rule.to_year * 12)
					rule_benefit = 0
					if employee_months < from_months:
						rule_benefit += 0
						total_benefits += 0
					elif employee_months > to_months:
						difference = (to_months - from_months) + 12
						rule_benefit += ((rule.percentage/100) * month_basic) * difference 
						total_benefits += ((rule.percentage/100) * month_basic) * difference 
					elif from_months <= employee_months <= to_months:
						if employee_months == to_months:
							difference = (to_months - from_months) + 12
							rule_benefit += ((rule.percentage/100) * month_basic) * difference
							total_benefits += ((rule.percentage/100) * month_basic) * difference
						elif employee_months == from_months:
							rule_benefit += ((rule.percentage/100) * month_basic)
							total_benefits += ((rule.percentage/100) * month_basic)
						else:
							difference = (employee_months - from_months)
							rule_benefit += ((rule.percentage/100) * month_basic) * difference
							total_benefits += ((rule.percentage/100) * month_basic) * difference
					if rule_benefit:
						vals = {
							'name': rule.name,
							'from_year': rule.from_year,
							'to_year': rule.to_year,
							'months':difference,
							'percentage': rule.percentage,
							'amount': rule_benefit,
							'eos_id':rec.id
							}
						lines.append((0, 0, vals))
				rec.benefit_line_ids = lines 
				rec.benefit_amount = total_benefits
			else:
				rec.benefit_line_ids.sudo().unlink()
				rec.benefit_amount = 0

	def _compute_overtime(self):
		for rec in self:
			ovt = 0.0
			emp_id = rec.employee_id.id
			ovtm_obj = self.env['hr.over.time']
			y, m, d = str(rec.end_date).split('-')
			date_from = datetime.date(int(y), int(m), int(1))
			y2, m2, d2 = str(rec.end_date).split('-')
			date_to = datetime.date(int(y), int(m), int(d2))
			ovtm_ids = ovtm_obj.search([('employee_id','=',emp_id),('date','>=',date_from),('date','<=',date_to),('state','=','confirm')])
			for ovtm_id in ovtm_ids:
				ovt += ovtm_id.net_overtime
			rec.overtime = ovt

	@api.depends('other_allowances_ids')
	def _compute_allowances_total(self):
		for rec in self:
			amount_total = sum(rec.other_allowances_ids.mapped('amount'))
			rec.total_allowances = amount_total


	@api.depends('other_deductions_ids')
	def _compute_deductions_total(self):
		for rec in self:
			amount_total = sum(rec.other_deductions_ids.mapped('amount'))
			rec.total_deduction = amount_total

	# Get service duration time
	@api.depends('join_date', 'end_date')
	def get_service_time(self):
		for rec in self:
			if rec.join_date and rec.end_date:
				y, m, d = str(rec.join_date).split('-')
				date_start = datetime.date(int(y), int(m), int(d))
				y, m, d = str(rec.end_date).split('-')
				date_end = datetime.date(int(y), int(m), int(d))
				diff = relativedelta(date_end, date_start)
				rec.years = diff.years
				rec.months = diff.months
				rec.days = diff.days + 1


	# get remaining leaves Balance
	# @api.depends('employee_id', 'end_date', 'join_date')
	@api.depends('employee_id')
	def _get_leaves(self):
		for rec in self:
			leave_requests = self.env['hr.leave'].search([('employee_id','=',rec.employee_id.id),('state','=','validate')])
			leave_allocations = self.env['hr.leave.allocation'].search([('employee_id','=',rec.employee_id.id),('state','=','validate')])
			leave_days = [requests.number_of_days for requests in leave_requests ]
			allocation_days = [allocations.number_of_days_display  for allocations in leave_allocations ]
			rec.leave_days = sum(allocation_days) - sum(leave_days) 
			rec.leaves_amount = (rec.employee_id.contract_id.payroll_wage / 30) * rec.leave_days


	@api.depends('contract_id', 'years')
	def get_end_service(self):
		for rec in self:
			# days =  rec.days + rec.months * 30 + rec.years * 365
			days =  rec.days + rec.months * 30.417 + rec.years * 365 + 30
			if rec.contract_id :
				if rec.years > 3 and  rec.years < 5 :
						rec.end_service = (rec.contract_id.payroll_wage * 0.25 * days) / 365
				if rec.years > 5 and  rec.years < 15 :
					rec.end_service = (rec.contract_id.payroll_wage * 0.50 * days) / 365
				if rec.years > 15 and  rec.years < 20 :
					rec.end_service = (rec.contract_id.payroll_wage * 0.75 * days) / 365
				if rec.years > 20 :
					rec.end_service = (rec.contract_id.payroll_wage * days) / 365


	# get 6 month basic
	@api.depends('basic','eos_type')
	def get_gross_allowance(self):
		for rec in self:
			if rec.contract_id and rec.eos_type:
				if rec.eos_type.arbitrary_dismissal:
					rec.gross_allowance = 6 * rec.basic
				else:
					rec.gross_allowance = 0.0

	@api.depends('leaves_amount', 'gross_allowance','total_allowances','benefit_amount')
	def _get_allow_total_amount(self):
		for rec in self:
			rec.allow_total_amount = rec.leaves_amount + rec.gross_allowance + rec.total_allowances + rec.benefit_amount


	@api.depends('total_deduction')
	def _get_ded_total_amount(self):
		for rec in self:
			rec.ded_total_amount =  rec.total_deduction


	@api.depends( 'allow_total_amount', 'ded_total_amount')
	def _get_total_amount(self):
		for rec in self:
			rec.total_amount = rec.allow_total_amount - rec.ded_total_amount


##########################################################################################################

class eos_type(models.Model):
	_name = 'hr.eos.type'

	name = fields.Char("Name", required=True)
	arbitrary_dismissal = fields.Boolean("Arbitrary Dismissal", default=False)

class eos_other_allowance(models.Model):
	_name = 'hr.eos.other.allowance'

	allowance_name = fields.Text(string='Allowance Name')
	amount = fields.Float("Amount")
	eos_id = fields.Many2one('hr.end.service', string='')
	

class eos_other_deduction(models.Model):
	_name = 'hr.eos.other.deduction'

	deduction_name = fields.Text(string='Deduction Name')
	amount = fields.Float("Amount")
	eos_id = fields.Many2one('hr.end.service', string='')


class EosBenefitLine(models.Model):
	_name = 'hr.benefit.line'

	name = fields.Char(string='Rule Name')
	from_year = fields.Float(string="From Year")
	to_year = fields.Float(string="To Year")
	months = fields.Integer(string='Months')
	percentage = fields.Float(string='Percentage(%)')
	amount = fields.Float(string='Amount')

	eos_id = fields.Many2one('hr.end.service')

