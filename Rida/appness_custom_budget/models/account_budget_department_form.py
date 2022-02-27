# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm, ValidationError
from datetime import date
import datetime

class BudgetDepartmentForm(models.Model):
	_name = 'account.budget.department.form'
	_description = 'Budget Department Form'
	_inherit = ['mail.thread','mail.activity.mixin']
	_order = 'id desc'

	name = fields.Char(string="Reference", required=True, index=True)
	budget_id = fields.Many2one('crossovered.budget', string="Budget", ondelete='restrict', readonly=True)
	department_id = fields.Many2one('hr.department', string="Department", ondelete='restrict')
	user_id = fields.Many2one(related='department_id.manager_id.user_id',readonly=True)
	manager_id = fields.Many2one(related='department_id.manager_id',readonly=True)
	analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", ondelete='restrict')
	general_budget_id = fields.Many2one('account.budget.post', string="Budgetary Positions", ondelete='restrict')
	line_ids = fields.One2many('account.budget.department.form.line', 'form_id', string="Lines")
	state = fields.Selection([
		('draft', 'BD attachements'),
		('department_user', 'To Submit'),
		('section_head', 'Waiting For Section Head'),
		('department_manager', 'Waiting For Dept. Manager'),
		('bd', 'Business Development'),
		('approve', 'Approved'),
		('bd_cont', 'Business Development'),
		('md_cont', 'Waiting For Managing Director'),
		('bod_cont', 'Waiting For Board of Directors'),
		('acutalize_cont', 'Acutalization Cont.'),
		('approve_cont', 'Cont. Approved'),
		('cancel', 'Cancelled'),
		('reject', 'Rejected'),
		 ], string="Status", readonly=True, default='draft')
	business_unit_id = fields.Many2one('hr.department', string="Business Unit")
	bd_comment = fields.Text("Business Development Comment")
	dep_manager_comment = fields.Text("Department Manager Comment")
	sectiom_head_comment = fields.Text("Section Head Comment")

	def action_submit_to_user(self):
		if self.message_main_attachment_id.id is False:
			raise ValidationError("Please attach supporting documents!")
		self.write({'state': 'department_user'})
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_reject'])
		#Send notification to users
		users = []
		_user = self.env.ref('budget.group_budget_department_user').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_dep_form_approve', user_id=u.id)
			


	def action_submit_to_section_head(self):
		self.write({'state': 'section_head'})
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_reject'])
		#Send notification to users
		users = []
		_user = self.env.ref('budget.group_budget_department_section_head').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_dep_form_approve', user_id=u.id)
			

	def action_submit_to_manager(self):
		self.write({'state': 'department_manager'})
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_reject'])
		#Send notification to users
		users = []
		_user = self.env.ref('budget.group_budget_department_manager').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_dep_form_approve', user_id=u.id)
			

	def action_approve(self):
		self.write({'state': 'bd'})
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_reject'])
		#Send notification to users
		users = []
		_user = self.env.ref('budget.group_bd').users
		for u in _user:
			users.append(u)
			self.activity_schedule('budget.mail_budget_dep_form_approve', user_id=u.id)

	def action_bd_approve(self):
		self.write({'state': 'approve'})
		self.add_to_budget()
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_reject'])

	def action_reject(self):
		if self.state=='department_manager':
			self.write({'state': 'section_head'})
			#Clear all previous notifications
			self.activity_unlink(['budget.mail_budget_dep_form_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget.group_budget_department_section_head').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_dep_form_reject', user_id=u.id)
			

		elif self.state=='bd':
			self.write({'state': 'department_manager'})
			#Clear all previous notifications
			self.activity_unlink(['budget.mail_budget_dep_form_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget.group_budget_department_manager').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_dep_form_reject', user_id=u.id)
			

		elif self.state=='section_head':
			self.write({'state': 'department_user'})
			#Clear all previous notifications
			self.activity_unlink(['budget.mail_budget_dep_form_approve'])
			#Send notification to users of the previous stage
			users = []
			_user = self.env.ref('budget.group_budget_department_user').users
			for u in _user:
				users.append(u)
				self.activity_schedule('budget.mail_budget_dep_form_reject', user_id=u.id)
			


	def action_draft(self):
		self.write({'state': 'draft'})
		#Clear all previous notifications
		self.activity_unlink(['budget.mail_budget_dep_form_approve'])
	

	def add_to_budget(self):
		for record in self:
			budget_id = record.budget_id
			for line in record.line_ids:
				budget_line = line.budget_line_id
				if not budget_line:
					budget_line = self.env['crossovered.budget.lines'].sudo().create({
						'crossovered_budget_id': budget_id.id,
						'department_id': line.business_unit_id.id,
						'analytic_account_id': line.analytic_account_id and line.analytic_account_id.id,
						'general_budget_id': line.general_budget_id and line.general_budget_id.id,
						'date_from': line.date_from,
						'date_to': line.date_to,
						'variable_amount': line.variable_amount,
						'fixed_amount': line.fixed_amount,
						'pre_planned_amount': line.pre_planned_amount, 
						'planned_amount': line.planned_amount if budget_id.type == 'profit' else line.planned_amount * -1,
						'cont_amount': line.cont_amount if budget_id.type == 'profit' else line.cont_amount * -1
					})
					line.budget_line_id = budget_line.id
				else:
					budget_line.sudo().update({
						'analytic_account_id': line.analytic_account_id and line.analytic_account_id.id,
						'general_budget_id': line.general_budget_id and line.general_budget_id.id,
						'department_id': line.business_unit_id.id,
						'date_from': line.date_from,
						'date_to': line.date_to,
						'variable_amount': line.variable_amount,
						'fixed_amount': line.fixed_amount,
						'pre_planned_amount': line.pre_planned_amount,
						'planned_amount': line.planned_amount if budget_id.type == 'profit' else line.planned_amount * -1,
						'cont_amount': line.cont_amount if budget_id.type == 'profit' else line.cont_amount * -1
					})


		'''Activate the Cont Amount'''

	def action_submit_cont(self):
		if self.message_main_attachment_id.id is False:
			raise ValidationError("Please attach supporting documents!")
		self.write({'state': 'bd_cont'})

	def action_approve_cont(self):
		# self.write({'state': 'md_cont'})
		# change in flow was requested by NUS, by removing MD and BOD from Buget LOA
		self.write({'state': 'acutalize_cont'})

	def action_md_approve(self):
		self.write({'state': 'bod_cont'})

	def action_bod_approve(self):
		self.write({'state': 'acutalize_cont'})

	def action_bd_acutalize_cont(self):
		self.write({'state': 'approve_cont'})
		self.activate_cont_amount()

	def action_reject_cont(self):
		self.write({'state': 'reject'})

	def action_md_reject_cont(self):
		self.write({'state': 'bd_cont'})

	def action_bod_reject_cont(self):
		self.write({'state': 'md_cont'})

	def action_draft_cont(self):
		self.write({'state': 'draft'})

	def activate_cont_amount(self):
		current_date = datetime.date.today()
		for record in self:
			budget_id = record.budget_id
			clear_cont_amount = 0
			for line in record.line_ids:
				if line.date_to >= current_date:	
					budget_line = line.budget_line_id		
					cont_planned_amount = line.cont_amount + line.planned_amount
					line.update({
						'planned_amount': cont_planned_amount,
						'cont_amount': clear_cont_amount,
						})
					budget_line.sudo().update({
						'planned_amount': cont_planned_amount if budget_id.type == 'profit' else cont_planned_amount * -1,
						'cont_amount': clear_cont_amount,
						})



class BudgetDepartmentFormLine(models.Model):
	_name = 'account.budget.department.form.line'
	_description = 'Budget Department Form Line'

	analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", ondelete='restrict')
	general_budget_id = fields.Many2one('account.budget.post', string="Budgetary Positions", ondelete='restrict')
	date_from = fields.Date(string="Start", required=True, readonly=True)
	date_to = fields.Date(string="End", required=True, readonly=True)
	planned_amount = fields.Monetary(string="Firm Budget")
	variable_amount = fields.Monetary(string="Variable")
	fixed_amount = fields.Monetary(string="Fixed")
	pre_planned_amount = fields.Monetary(string="Pre-Planned")
	cont_amount = fields.Monetary(string="Cont. Budget")
	currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)
	form_id = fields.Many2one('account.budget.department.form', string="Department Form", ondelete='cascade')
	budget_line_id = fields.Many2one('crossovered.budget.lines', string="Budget Line")
	expense_type = fields.Selection([('capx', 'CAPX'), ('opex', 'OPEX')], related="form_id.budget_id.expense_type")
	type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], related="form_id.budget_id.type")
	business_unit_id = fields.Many2one('hr.department')
	cont = fields.Boolean(related='business_unit_id.cont_budget_only',readonly=True)

	@api.onchange('variable_amount','fixed_amount')
	def _compute_planned_amount(self):
		for rec in self:
			if rec.expense_type == 'opex':
				rec.planned_amount = rec.variable_amount + rec.fixed_amount
			else :
				rec.update({'planned_amount': rec.planned_amount})

	@api.onchange('planned_amount')
	def onchange_planned_amount(self):
		for record in self:
			record.update({'cont_amount': record.planned_amount})



			
