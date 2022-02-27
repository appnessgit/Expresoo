# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm
import itertools
import psycopg2


class CrossoveredBudget(models.Model):
	_name = 'crossovered.budget'
	_inherit = ['crossovered.budget','mail.activity.mixin']
	_rec_name = 'display_name'

	months = [
		('01', "January"),
		('02', "February"),
		('03', "March"),
		('04', "April"),
		('05', "May"),
		('06', "June"),
		('07', "July"),
		('08', "August"),
		('09', "September"),
		('10', "October"),
		('11', "November"),
		('12', "December"),
	]

	state = fields.Selection([
		('draft', 'Draft'),
		('department', 'Waiting for Departments Input'),
		('bd', 'Waiting for Business Development'),
		('md', 'Waiting for Managing Director'),
		('bd_2nd', 'Waiting for Business Development'),
		('mc', 'Waiting for Managing Commitee'),
		('bd_3rd', 'Waiting for Business Development'),
		('bod', 'Waiting for Board of Directors'),
		('confirm', 'Confirmed'),
		('validate', 'Validated'),
		('reject', 'Rejected'),
		], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, tracking=True)

	md_comment = fields.Text("Managing Director Comment")
	bod_comment = fields.Text("Board of Directors Comment")

	### Flow ###
	# Business Development

	def action_create_budgt_forms(self):
		return {
			'type': 'ir.actions.act_window',
			'name': 'Genereate Departments Forms',
			'view_mode': 'form',
			'target': 'new',
			'res_model': 'appness_custom_budget.department.form.wizard',
		}
		self.write({'state': 'department'})

		# 2nd Business Development
	def action_bd_submit(self):
		self.write({'state': 'bd'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])



		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)



	def action_bd_approve(self):
		self.write({'state': 'md'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget.group_md').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)




		# Managing Director
	def action_md_approve(self):
		self.write({'state': 'bd_2nd'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)



		# 2nd Business Development
	def action_bd_2_approve(self):
		# self.write({'state': 'mc'})
		# change in flow was requested by NUS, by removing MC and BOD from Buget LOA
		self.write({'state': 'confirm'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)




		# Managing Commitee
	def action_mc_approve(self):
		self.write({'state': 'bd_3rd'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)



		# 2nd Business Development
	def action_bd_3_approve(self):
		self.write({'state': 'bod'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)




		# Board of Directors
	def action_bod_approve(self):
		self.write({'state': 'confirm'})
		#Clear all previous Reject notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)




		# 3rd Business Development final validate 
	def action_bd_3rd_validate(self):
		self.action_budget_validate()
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_crossovered_reject'])


		#Send new notification
		users = []
		_user = self.env.ref('budget').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_crossovered_approve', user_id=u.id)




	def action_reject(self):
		if self.state == 'md':
			self.write({'state': 'bd'})
			#Clear all previous Approve notifications
			self.activity_unlink(['budget.mail_budget_crossovered_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_crossovered_reject', user_id=u.id)
		  
		elif self.state == 'mc':
			self.write({'state': 'bd_2nd'})
			#Clear all previous Approve notifications
			self.activity_unlink(['budget.mail_budget_crossovered_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_crossovered_reject', user_id=u.id)
  

		elif self.state == 'bod':
			self.write({'state': 'bd_3rd'})
			#Clear all previous Approve notifications
			self.activity_unlink(['budget.mail_budget_crossovered_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_crossovered_reject', user_id=u.id)
			
		else:
			self.write({'state': 'reject'})


	def action_draft(self):
		self.write({'state': 'draft'})
	


	year = fields.Char()
	month = fields.Selection(months)
	planned_amount = fields.Monetary("Planned Amount")
	allocated_amount = fields.Monetary("Allocated Amount", compute="_compute_totals")
	remaining_amount = fields.Monetary("Remaining Amount", compute="_compute_totals", store=True)
	currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
	analytic_account_id = fields.Many2one('account.analytic.account', 'CostCenter')
	# general_budget_id = fields.Many2one('account.budget.post', string="Budgetary Positions")
	department_id = fields.Many2one('hr.department', "Department")
	display_name = fields.Char(compute='compute_display_name')
	type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], default="expense")
	crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lin',
		states={'draft': [('readonly', True)]}, copy=True)

	expense_type = fields.Selection([('capx', 'CAPX'), ('opex', 'OPEX')])
	dep_budget_form_ids = fields.One2many('account.budget.department.form', 'budget_id')
	total_remaining_amount = fields.Monetary("TOTAL", compute="_compute_remaining_amount_totals", store=True)
	safe_margin = fields.Float("Margin %", store=True)


	@api.onchange('safe_margin')
	def _onchange_safe_margin(self):
		if self.type=="expense":
			for i in self.crossovered_budget_line:
				i.planned_amount += (self.safe_margin*i.planned_amount)/100
		if self.type=="profit":
			for i in self.crossovered_budget_line:
				i.planned_amount -= (self.safe_margin*i.planned_amount)/100
	#     for rec in self:
	#         if rec.type=="expense":
	#             for i in rec.crossovered_budget_line:
	#                 value = i.planned_amount + (rec.safe_margin*i.planned_amount)/100
	#                 i.write({'planned_amount': value})
	#         if rec.type=="profit":
	#             for i in rec.crossovered_budget_line:
	#                 value = i.planned_amount - (rec.safe_margin*i.planned_amount)/100
	#                 i.write({'planned_amount': value})

	def _compute_remaining_amount_totals(self):
		for rec in self:
			total= 0
			for i in rec.crossovered_budget_line:
				total += i.remaining_amount
			rec.total_remaining_amount = total


	def unlink(self):
		for rec in self:
			if not rec.state == 'draft':
				raise UserError("Sorry! only draft records can be deleted!")

		return super(CrossoveredBudget, self).unlink()

	@api.depends('name','department_id')
	def compute_display_name(self):
		for record in self:
			display_name = record.name
			if record.department_id:
				display_name += " - " + record.department_id.name
			display_name += " (" + str(record.date_from) + " - " + str(record.date_to) + ")"
			record.display_name = display_name


	def action_budget_validate(self):
		self.ensure_one()
		self.write({'state': 'validate'})
		for line in self.crossovered_budget_line:
			line.initial_planned_amount = line.planned_amount

	@api.depends('crossovered_budget_line', 'planned_amount', 'safe_margin')
	def _compute_totals(self):
		for record in self:
			allocated_amout = sum(line.planned_amount for line in record.crossovered_budget_line)
			remaining_amount = record.planned_amount - allocated_amout
			record.update({
				'allocated_amount': allocated_amout,
				'remaining_amount': remaining_amount
			})

		# if self.type=="expense":
		#     for i in self.crossovered_budget_line:
		#         i.planned_amount += (self.safe_margin*i.planned_amount)/100
		# if self.type=="profit":
		#     for i in self.crossovered_budget_line:
		#         i.planned_amount -= (self.safe_margin*i.planned_amount)/100

	# @api.constrains('planned_amount', 'crossovered_budget_line')
	# def _check_budget_exceed(self):

	#     if self.type == "expense" and self.planned_amount > 0:
	#         raise UserError("Expense Budgets Should have negative amounts!")
	#     elif self.type == "profit" and self.planned_amount <= 0:
	#         raise UserError("Revenue Budgets Should have positive amounts!")

	#     if not self.crossovered_budget_line:
	#         return
	#     allocated_amout = sum(line.planned_amount for line in self.crossovered_budget_line)

	#     if self.type == "expense":
	#         if allocated_amout < self.planned_amount:
	#             raise UserError("Budget Exceeded")
	#     else:
	#         if allocated_amout > self.planned_amount:
	#             raise UserError("Budget Exceeded! \n Budget lines total should not exceed the budget planned amount.")

	def action_view_amendments(self):
		return {
			'name': "Amendments",
			'type': 'ir.actions.act_window',
			'res_model': 'account.budget.amendment',
			'view_id': False,
			'view_mode': 'tree,form',
			'view_type': 'form',
			'target': 'current',
			'domain': ['|', ('budget_line_from', 'in', self.crossovered_budget_line.ids),
					   ('budget_line_to', 'in', self.crossovered_budget_line.ids)],
		}

	def action_view_departments_forms(self):
		return {
			'name': "Departments Forms",
			'type': 'ir.actions.act_window',
			'res_model': 'account.budget.department.form',
			'view_id': False,
			'view_mode': 'tree,form',
			'view_type': 'form',
			'target': 'current',
			'domain': [('budget_id', '=', self.id)],
		}


class CrossoveredBudgetLines(models.Model):
	_inherit = 'crossovered.budget.lines'
	_rec_name = "name"

	name = fields.Char(compute='_compute_line_name', store=True)

	account_id = fields.Many2one('account.account', string="Account", required=False)
	categ_id = fields.Many2one('product.category', "Category")
	remaining_amount = fields.Monetary("Remaining Amount", compute='_compute_remaining_amount', store=True)
	department_id = fields.Many2one('hr.department', string="Department")
	user_id = fields.Many2one(related='department_id.manager_id.user_id',readonly=True)
	planned_amount = fields.Monetary(string="Firm Budget", store=True)
	variable_amount = fields.Monetary(string="Variable")
	fixed_amount = fields.Monetary(string="Fixed")
	pre_planned_amount = fields.Monetary(string="Pre-Planned")
	cont_amount = fields.Monetary(string="Cont. Budget")
	cont_amount_active = fields.Boolean(string="Cont. Budget Acticve")
	allow_over_budget = fields.Boolean("Allow Budget Exceeding")

	budget_amendment_id = fields.Many2one('account.budget.amendment')

	def write(self, values):
		super(CrossoveredBudgetLines, self).write(values)
		if values.get('planned_amount'):
			for line in self:
				department_line = self.env['account.budget.department.form.line'].search([('budget_line_id', '=', line.id)])
				if department_line:
					department_line.write({
						'planned_amount': abs(line.planned_amount),
						})
					
		if values.get('variable_amount'):
			for line in self:
				department_line = self.env['account.budget.department.form.line'].search([('budget_line_id', '=', line.id)])
				if department_line:
					department_line.write({
						'variable_amount': abs(line.variable_amount),
						})

		if values.get('fixed_amount'):
			for line in self:
				department_line = self.env['account.budget.department.form.line'].search([('budget_line_id', '=', line.id)])
				if department_line:
					department_line.write({
						'fixed_amount': abs(line.fixed_amount),
						})

		if values.get('cont_amount'):
			for line in self:
				department_line = self.env['account.budget.department.form.line'].search([('budget_line_id', '=', line.id)])
				if department_line:
					department_line.write({
						'cont_amount': abs(line.cont_amount),
						})


	type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], default="expense",
							related="crossovered_budget_id.type")
	expense_type = fields.Selection([('capx', 'CAPX'), ('opex', 'OPEX')],related="crossovered_budget_id.expense_type")

	initial_planned_amount = fields.Monetary("Initially Planned Amount")
	planned_amount_date = fields.Monetary("Planned Amount on Date", compute="compute_planned_amount_date")


	@api.depends('initial_planned_amount')
	def compute_planned_amount_date(self):
		self.ensure_one()
		date = fields.Datetime.now()

		if self.env.context.get('practical_date'):
			date = fields.Date.from_string(self.env.context.get('practical_date'))
		amendments = self.env['account.budget.amendment'].search(['|',
			('budget_line_from', '=', self.id),
			('budget_line_to', '=', self.id),
			('date', '<=', date),
		])

		add_amendments = amendments.filtered(lambda l: l.budget_line_to.id == self.id)
		substract_amendments = amendments.filtered(lambda l: l.type == 'swap' and l.budget_line_from.id == self.id)

		add_amount = sum(line.amount for line in add_amendments)
		sub_amount = sum(line.amount for line in substract_amendments)

		self.planned_amount_date = self.initial_planned_amount + add_amount - sub_amount

	@api.model
	def create(self, vals):
		vals['initial_planned_amount'] = vals.get('planned_amount')
		return super(CrossoveredBudgetLines, self).create(vals)

	@api.constrains('planned_amount')
	def check_amounts(self):
		if self.type == "expense" and self.planned_amount > 0:
			raise UserError("Expense Budgets Should have negative amounts! \n "
							"*Make sure that all the budget lines have negative values!")
		elif self.type == "profit" and self.planned_amount < 0:
			raise UserError("Revenue Budgets Should have positive amounts! \n *"
							"Make sure that all the budget lines have positive values!")

	def action_allow_exceeding(self):
		self.ensure_one()
		self.allow_over_budget = True

	def action_stop_exceeding(self):
		self.ensure_one()
		self.allow_over_budget = False

	@api.depends('department_id', 'analytic_account_id')
	def _compute_department_line(self):
		for record in self:
			if not record.department_id.analytic_account_id:
				return
			if record.analytic_account_id == record.department_id.analytic_account_id:
				record.department_line = True

	@api.depends('planned_amount', 'practical_amount')
	def _compute_remaining_amount(self):
		for record in self:
			record.remaining_amount = abs(record.planned_amount) - abs(record.practical_amount)

	@api.onchange('categ_id')
	def onchange_categ_id(self):
		if not self.categ_id:
			return
		if self.categ_id.property_account_expense_categ_id:
			self.account_id = self.categ_id.property_account_expense_categ_id.id

	@api.onchange('fixed_amount','variable_amount','pre_planned_amount')
	def onchange_fixed_amount(self):
		for rec in self:
			rec.planned_amount = rec.fixed_amount + rec.variable_amount + rec.pre_planned_amount

   
	# @api.constrains('account_id', 'analytic_account_id')
	# def _must_have_analytical_or_budgetary_or_both(self):
	#     for record in self:
	#         if not record.analytic_account_id and not record.account_id:
	#             raise UserError(
	#                 _("You have to enter at least a GL account or analytic account on a budget line."))

	@api.depends("account_id", "general_budget_id", "analytic_account_id")
	def _compute_line_name(self):
		# just in case someone opens the budget line in form view
		for record in self:
			computed_name = record.crossovered_budget_id.name
			if record.account_id:
				computed_name += ' - ' + record.account_id.name
			if record.analytic_account_id:
				computed_name += ' - ' + record.analytic_account_id.name
			if record.categ_id:
				computed_name += ' - ' + record.categ_id.name
			record.name = computed_name

	def action_open_budget_entries(self):
		if self.analytic_account_id:
			# if there is an analytic account, then the analytic items are loaded
			action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action_entries')
			action['domain'] = [('account_id', '=', self.analytic_account_id.id),
								('date', '>=', self.date_from),
								('date', '<=', self.date_to),
								('general_account_id', '=', self.account_id.id)
								]

		else:
			# otherwise the journal entries booked on the accounts of the budgetary postition are opened
			action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_moves_all_a')
			action['domain'] = [('account_id', '=', self.account_id.id),
								('date', '>=', self.date_from),
								('date', '<=', self.date_to)
								]
		return action

	@api.onchange('planned_amount')
	def onchange_planned_amount(self):
		if self.planned_amount > 0.0:
			self.allow_over_budget = True
		else:
			self.allow_over_budget = False


	@api.constrains('date_from', 'date_to')
	def _line_dates_between_budget_dates(self):
		pass


		for line in self:
			budget_date_from = line.crossovered_budget_id.date_from
			budget_date_to = line.crossovered_budget_id.date_to
			if line.date_from:
				date_from = line.date_from
				if date_from < budget_date_from or date_from > budget_date_to:
					return True

                    # raise ValidationError(_('"Start Date" of the budget line should be included in the Period of the budget'))
			if line.date_to:
				date_to = line.date_to
				if date_to < budget_date_from or date_to > budget_date_to:
					return True
                    # raise ValidationError(_('"End Date" of the budget line should be included in the Period of the budget'))
		super(CrossoveredBudgetLines, self)._line_dates_between_budget_dates()