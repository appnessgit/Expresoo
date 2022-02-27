# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm, ValidationError
from datetime import date
import datetime


class CrossoveredBudgetAmendment(models.Model):
	_name = 'account.budget.amendment'
	_description = "Budget Amendment"
	_inherit = ['mail.thread','mail.activity.mixin']
	_order = "create_date desc"

	states = [
		('draft', 'Draft'),
		('cancel', 'Cancelled'),
		('submit', 'Submited'),
		('bd', 'Waitting Business Development Review'),
		('m_director', 'Waitting Manage Director Review'),
		('b_director', 'Waitting Board of Directors Review'),
		('approve', 'Approved'),
		('validate', 'Validated'),
	]

	name = fields.Char("Name", readonly=True, required=True, copy=False, default='New')
	date = fields.Date(default=datetime.datetime.now().date())
	type = fields.Selection([('swap','Swap'),('add','Add/ Subtract')], "Amendment Type", default='swap', readonly=True)
	currency_id = fields.Many2one('res.currency', default=lambda self: self.get_currency(), readonly=True)
	notes = fields.Text(string="Justification")


	budget_line_from = fields.Many2one('crossovered.budget.lines', string="From", domain=lambda self: [('type', '!=', 'profit')])
	budget_line_to = fields.Many2one('crossovered.budget.lines', string="To", domain=lambda self: [('type', '!=', 'profit')])
	budget_id = fields.Many2one('crossovered.budget', "Budget", related="budget_line_from.crossovered_budget_id")
	budget_id_2 = fields.Many2one('crossovered.budget', "Budget 2", related="budget_line_to.crossovered_budget_id")
	amount = fields.Monetary('Amount')
	remaining_amount = fields.Monetary("Remaining", compute='compute_remaining', store=True)
	internal_swap = fields.Boolean(compute="compute_internal_swap")
	md_approve = fields.Boolean(default=False, readonly=True, store=True)
	bod_approve = fields.Boolean(default=False, readonly=True, store=True)

	bd_comment = fields.Text("Business Development Comment")
	md_comment = fields.Text("Managing Director Comment")
	bod_comment = fields.Text("Board of Directors Comment")

	user_section_id = fields.Many2one('hr.department', default=lambda self: self.env.user.employee_ids.department_id, readonly=True, store=True)
	budget_lines_from = fields.One2many('budget.lines.from', 'budget_amendment_id', string="From", domain=lambda self: [('type', '!=', 'profit')], readonly=False)
	currency_id = fields.Many2one('res.currency')
	total_subtract = fields.Monetary("Total", compute='compute_total_subtract', store=True)


	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New' and vals.get('type') == 'add':
			vals['name'] = self.env['ir.sequence'].next_by_code('account.budget.add') or 'New'
		if vals.get('name', 'New') == 'New' and vals.get('type') == 'swap':
			vals['name'] = self.env['ir.sequence'].next_by_code('account.budget.reallocation') or 'New'
			# if vals.get('type') == 'add':
		

		result = super(CrossoveredBudgetAmendment, self).create(vals)
		return result


	@api.onchange('budget_line_from','budget_line_to')
	def onchange_budget_domain(self):
		if self.state == 'draft':
			if self.user_section_id.section_parent_id:
				return {
				'domain':{
				'budget_line_from':[('department_id','=', self.user_section_id.id)],
				'budget_line_to':[('department_id','=', self.user_section_id.id)]}}
			elif self.user_section_id.parent_id:
				return {
				'domain':{
				'budget_line_from':[('department_id.section_parent_id','=', self.user_section_id.id)],
				'budget_line_to':[('department_id.section_parent_id','=', self.user_section_id.id)]}}



	def compute_internal_swap(self):
		for record in self:
			if record.budget_line_from.department_id == record.budget_line_to.department_id and \
					record.budget_line_from.department_line and record.budget_line_to.department_line:
				record.internal_swap = True
			else:
				record.internal_swap = False

	@api.constrains('amount', 'budget_lines_from', 'budget_line_to')
	def check_all_fields(self):
		if self.state=="bd":
			self.check_budget_validity()
			if self.type == "swap":
				for line in self.budget_lines_from:
					if line.budget_line_from == self.budget_line_to:
						raise UserError("Please select a different budget!")
					if line.budget_line_from.type != self.budget_line_to.type:
						raise UserError("You cannot swap between different budget types!")
			# if self.budget_line_to.type == "expense" and self.amount >= 0:
			# 	raise UserError("Expense Budgets Should have negative amounts!")
			# if self.budget_line_to.type == "profit" and self.amount <= 0:
			# 	raise UserError("Profit Budgets Should have positive amounts!")

	@api.depends('budget_line_to')
	def compute_remaining(self):
		self.ensure_one()
		if self.budget_line_to:
			# self.remaining_amount = self.budget_line_to.crossovered_budget_id.total_remaining_amount
			self.remaining_amount = self.budget_line_to.remaining_amount
		else :
			return

	@api.depends('budget_lines_from')
	def compute_total_subtract(self):
		sum = 0 
		for line in self.budget_lines_from:
			sum += line.reallocted_amount 
		self.total_subtract = sum

	# @api.onchange('budget_line_from','budget_line_to')
	# def re_compute_remaining():
	# 	self.compute_remaining()
	# 	pass
		# else:
		# 	self.remaining_amount = self.budget_line_from.remaining_amount

	state = fields.Selection(states, string="Status", default="draft", track_visibility='onchange')

	# @api.depends('type')
	# def compute_name(self):
	# 	self.ensure_one()
	# 	name = " "
	# 	if self.type == 'swap':
	# 		name += "Swap: " + self.budget_line_from.name + " > " + self.budget_line_to.name

	# 	else:
	# 		name += "Add: " + self.budget_line_to.name
	# 	self.name = name

	def get_currency(self):
		return self.env.user.company_id.currency_id.id

	# @api.onchange('type')
	# def onchange_type(self):
	# 	if self.type == 'add':
	# 		self.budget_line_from = False

	def unlink(self):
		for rec in self:
			if not rec.state == "draft":
				raise UserError("Only Draft Records Can Be Deleted")
			return super(CrossoveredBudgetAmendment, self).unlink()

	def action_cancel(self):
		for rec in self:
			rec.state = "cancel"

	def action_draft(self):
		for rec in self:
			rec.state = "draft"

	def action_submit(self):
		for rec in self:
			if rec.message_main_attachment_id.id is False:
				raise ValidationError("Please attach supporting documents!")
			rec.state = "bd"
			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_reject'])

			#Send notification to users of the next stage
			users = []
			_user = rec.env.ref('budjet.group_bd').users
			for u in _user:
				users.append(u)
				rec.activity_schedule('budget.mail_account_budget_amendment_approve', user_id=u.id)
		


	def action_bd_confirm(self):
		amount_l = self.env['ir.config_parameter'].sudo().get_param('budget.amount_limit') or False
		# amount_l_ne = float(amount_l) * -1
		remaining_amount = abs(self.remaining_amount)

		for rec in self:

			if rec.total_subtract != rec.amount:
				raise ValidationError("Amount MUST equal the Total in From lines!")

			# if rec.type=="swap":
				# if rec.budget_line_to.type == "expense":
			if abs(rec.amount) > remaining_amount:
				# rec.state = "b_director"
				raise ValidationError("Amount Can NOT be more than Remaining!")
			elif abs(rec.amount) >= float(amount_l) and not rec.md_approve:
				rec.state = "m_director"
				#Send notification to users of the prvious stage
				users = []
				_user = rec.env.ref('budget.group_md').users
				for u in _user:
					users.append(u)
					rec.activity_schedule('budget.mail_account_budget_amendment_approve', user_id=u.id)
				

			else:
				rec.action_confirm()

			# else:
			# 	if abs(rec.amount) > remaining_amount and not rec.bod_approve:
			# 		rec.state = "b_director"					
			# 	elif abs(rec.amount) >= abs(amount_l) and not rec.md_approve:
			# 		rec.state = "m_director"
			# 	else:
			# 		rec.action_confirm()

			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_reject'])




			# if requested amount is more than budget remaining amount: BoD approve needed
				# if it is less but more than config limit amount in settings : MD approve needed
			# if rec.budget_line_to.type == "expense":
			# 	if rec.amount > abs(remaining_amount) and not rec.bod_approve:
			# 		if rec.type=="add":
			# 			rec.state = "b_director"
			# 		elif rec.type=="swap":
			# 			raise UserError('Amount cannot be greater than remaining amount!')

			# 	elif rec.amount >= abs(amount_l) and not rec.md_approve:
			# 		rec.state = "m_director"
			# 	else:
			# 		rec.action_confirm()

			# elif rec.budget_line_to.type == "profit":
			# 	if rec.amount >= float(remaining_amount) and not rec.bod_approve:
			# 		if rec.type=="add":
			# 			rec.state = "b_director"
			# 		else:
			# 			raise UserError('Amount cannot be greater than remaining amount!')
			# 	elif rec.amount >= float(amount_l) and not rec.md_approve:
			# 		rec.state = "m_director"
			# 	else:
			# 		rec.action_confirm()

	def action_bd_reject(self):
		for rec in self:
			rec.state = "draft"
			
			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_approve'])

			#Send notification to users of the previous stage
			users = []
			_user = rec.env.ref('budget.group_budget_department_user').users
			for u in _user:
				users.append(u)
				rec.activity_schedule('budget.mail_account_budget_amendment_reject', user_id=u.id)
			



	def action_md_confirm(self):
		for rec in self:
			rec.write({'md_approve': True})
			rec.action_confirm()
			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_reject'])

	def action_md_reject(self):
		for rec in self:
			rec.state = "bd"
			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_approve'])

			#Send notification to users of the previous stage
			users = []
			_user = rec.env.ref('budget.group_bd').users
			for u in _user:
				users.append(u)
				rec.activity_schedule('budget.mail_account_budget_amendment_reject', user_id=u.id)
			



	def action_bod_confirm(self):
		for rec in self:
			rec.write({'bod_approve': True})
			# rec.state = "bd"
			rec.action_confirm()
			#Clear all previous notifications
			rec.activity_unlink(['budget.mail_account_budget_amendment_reject'])

	def action_bod_reject(self):
		for rec in self:
			rec.state = "bd"
			#Send notification to users of the previous stage
			users = []
			_user = rec.env.ref('budget.group_bd').users
			for u in _user:
				users.append(u)
				rec.activity_schedule('budget.mail_account_budget_amendment_reject', user_id=u.id)
			



	def action_confirm(self):
		for rec in self:
			# if rec.type == 'swap':
			# 	if rec.budget_line_to.type == "expense":
			# 		if abs(rec.amount) > rec.remaining_amount:
			# 			raise UserError('Amount cannot be greater than remaining amount!')
			# 	else:
			# 		if rec.amount > rec.remaining_amount:
			# 			raise UserError('Amount cannot be greater than remaining amount!')

			rec.state = 'approve'

			#Send notification to users
			users = []
			_user = rec.env.ref('budget.group_bd').users
			for u in _user:
				users.append(u)
				rec.activity_schedule('budget.mail_account_budget_amendment_approve', user_id=u.id)
			


			# rec.compute_name()

			# if rec.internal_swap:
			# 	rec.action_validate()

	def check_budget_validity(self):
		self.ensure_one()
		year_start = date(date.today().year, 1, 1)
		year_end = date(date.today().year, 12, 31)
		message = "Budget Expired!\n -One of the selected budgets are out of the current financial year!"

		from_from = from_to = to_from = to_to = False

		to_from = fields.Date.from_string(self.budget_line_to.date_from)
		to_to = fields.Date.from_string(self.budget_line_to.date_to)

		if to_from < year_start or to_to > year_end:
			raise UserError(message)
		if self.type == "swap":
			from_from = fields.Date.from_string(self.budget_lines_from.budget_line_from.date_from)
			from_to = fields.Date.from_string(self.budget_lines_from.budget_line_from.date_to)
			if from_from < year_start or from_to > year_end:
				raise UserError(message)

	def action_validate(self):
		# if self.type == 'swap':
		if self.bod_approve == True:
			self.sudo().budget_line_to.planned_amount += self.amount


		else :

			for line in self.budget_lines_from:
				if line.budget_line_from.planned_amount >= 0:
					line.sudo().budget_line_from.planned_amount -= line.reallocted_amount
				elif line.budget_line_from.planned_amount < 0:
					line.sudo().budget_line_from.planned_amount += line.reallocted_amount
			if self.budget_line_to.planned_amount >= 0:
				self.sudo().budget_line_to.planned_amount += self.amount
			elif self.budget_line_to.planned_amount < 0:
				self.sudo().budget_line_to.planned_amount -= self.amount


		# if self.sudo().budget_line_from.crossovered_budget_id != self.sudo().budget_line_to.crossovered_budget_id:
			# self.sudo().budget_line_from.crossovered_budget_id.planned_amount -= self.amount
		

		# for line in self.budget_lines_from:
		# 	if line.sudo().budget_line_from.crossovered_budget_id != self.sudo().budget_line_to.crossovered_budget_id:
		# 		if line.budget_line_from.planned_amount >= 0:
		# 			line.sudo().budget_line_from.planned_amount -= line.reallocted_amount
		# 		elif line.budget_line_from.planned_amount < 0:
		# 			line.sudo().budget_line_from.planned_amount += line.reallocted_amount
		# 		if self.budget_line_to.planned_amount >= 0:
		# 			self.sudo().budget_line_to.planned_amount += line.reallocted_amount
		# 		elif self.budget_line_to.planned_amount < 0:
		# 			self.sudo().budget_line_to.planned_amount -= line.reallocted_amount
		# else:
		# 	self.sudo().budget_line_to.planned_amount += self.amount
		# 	self.sudo().budget_line_to.crossovered_budget_id.planned_amount += self.amount
		# 	if not self.budget_line_to.allow_over_budget:
		# 		message = _("Planned amount cannot be less than practical_amount")
		# 		if self.budget_line_to.type == "expense" and \
		# 			self.sudo().budget_line_to.planned_amount > self.sudo().budget_line_to.practical_amount:
		# 			raise UserError(message)
		# 		elif self.budget_line_to.type == "profit" and \
		# 				self.sudo().budget_line_to.planned_amount < self.sudo().budget_line_to.practical_amount:
		# 			raise UserError(message)
		self.state = "approve"

	def action_approve(self):
		for rec in self:
			rec.action_validate()
			rec.state = "validate"



class CrossoveredBudgetLinesFrom(models.Model):
	_name = 'budget.lines.from'


	currency_id = fields.Many2one('res.currency')
	budget_line_from = fields.Many2one('crossovered.budget.lines', string="From", domain=lambda self: [('type', '!=', 'profit')])
	planned_amount = fields.Monetary(string="Firm Amount", related="budget_line_from.planned_amount")
	remaining_amount = fields.Monetary(string="Remaining Amount", related="budget_line_from.remaining_amount")
	reallocted_amount = fields.Monetary("Subtract", store=True)
	budget_amendment_id = fields.Many2one('account.budget.amendment')
	type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], default="expense",
							related="budget_line_from.crossovered_budget_id.type")

