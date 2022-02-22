# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm
from datetime import date
import datetime


class CrossoveredBudgetAmendment(models.Model):
	_name = 'account.budget.amendment'
	_description = "Budget Amendment"
	_inherit = ['mail.thread']
	_order = "create_date desc"

	states = [
		('draft', 'Draft'),
		('finance', 'Finance Manager Approval'),
		('ceo', 'CEO Approval'),
		('cancel', 'Cancelled'),
		('validate', 'Validated')
	]

	name = fields.Char(compute='compute_name', store=True)
	date = fields.Date(default=datetime.datetime.now().date())
	type = fields.Selection([('swap','Swap'),('add','Add/ Subtract')], "Amendment Type", default='swap')
	currency_id = fields.Many2one('res.currency', default=lambda self: self.get_currency(), readonly=True)
	notes = fields.Text()
	crossovered_budget_id = fields.Many2one('crossovered.budget', string="Budget", required=True)
	budget_line_from = fields.Many2one('crossovered.budget.lines', string="From")
	budget_line_to = fields.Many2one('crossovered.budget.lines', string="To")
	budget_id = fields.Many2one('crossovered.budget', "Budget", related="budget_line_from.crossovered_budget_id")
	budget_id_2 = fields.Many2one('crossovered.budget', "Budget 2", related="budget_line_to.crossovered_budget_id")
	amount = fields.Monetary('Amount')
	remaining_amount = fields.Monetary("Remaining", compute='compute_remaining', store=True)
	internal_swap = fields.Boolean(compute="compute_internal_swap")

	def compute_internal_swap(self):
		for record in self:
			if record.budget_line_from.department_id == record.budget_line_to.department_id and \
					record.budget_line_from.department_line and record.budget_line_to.department_line:
				record.internal_swap = True
			else:
				record.internal_swap = False

	@api.constrains('amount', 'budget_line_from', 'budget_line_to')
	def check_all_fields(self):
		self.check_budget_validity()
		if self.type == "swap":
			if self.budget_line_from == self.budget_line_to:
				raise UserError("Please select a different budget!")
			if self.budget_line_from.type != self.budget_line_to.type:
				raise UserError("You cannot swap between different budget types!")

	@api.depends('budget_line_from')
	def compute_remaining(self):
		self.ensure_one()
		if not self.budget_line_from:
			return
		self.remaining_amount = self.budget_line_from.remaining_amount

	state = fields.Selection(states, string="Status", default="draft", track_visibility='onchange')

	@api.depends('type')
	def compute_name(self):
		self.ensure_one()
		name = " "
		if self.type == 'swap':
			name += "Swap: " + self.budget_line_from.name + " > " + self.budget_line_to.name

		else:
			name += "Add: " + self.budget_line_to.name
		self.name = name

	def get_currency(self):
		return self.env.user.company_id.currency_id.id

	@api.onchange('type')
	def onchange_type(self):
		if self.type == 'add':
			self.budget_line_from = False

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

	def action_confirm(self):
		for rec in self:
			if rec.type == 'swap':
				if rec.budget_line_to.type == "expense":
					if abs(rec.amount) > rec.remaining_amount:
						raise UserError('Amount cannot be greater than remaining amount!')
				else:
					if rec.amount > rec.remaining_amount:
						raise UserError('Amount cannot be greater than remaining amount!')

			rec.state = 'finance'

	def action_finance_approve(self):
		for rec in self:
			rec.state = 'ceo'

	def action_ceo_approve(self):
		for rec in self:
			rec.sudo().action_validate()
			

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
			from_from = fields.Date.from_string(self.budget_line_from.date_from)
			from_to = fields.Date.from_string(self.budget_line_from.date_to)
			if from_from < year_start or from_to > year_end:
				raise UserError(message)

	def action_validate(self):
		if self.type == 'swap':
			if self.budget_line_to.type == "expense":
				if abs(self.amount) > self.remaining_amount:
					raise UserError('Amount cannot be greater than remaining amount!')
			else:
				if self.amount > self.remaining_amount:
					raise UserError('Amount cannot be greater than remaining amount!')

			self.sudo().budget_line_from.planned_amount -= self.amount
			self.sudo().budget_line_to.planned_amount += self.amount
			if self.sudo().budget_line_from.crossovered_budget_id != self.sudo().budget_line_to.crossovered_budget_id:
				self.sudo().budget_line_from.crossovered_budget_id.planned_amount -= self.amount
				self.sudo().budget_line_to.crossovered_budget_id.planned_amount += self.amount
		else:
			self.sudo().budget_line_to.planned_amount += self.amount
			self.sudo().budget_line_to.crossovered_budget_id.planned_amount += self.amount
			if not self.budget_line_to.allow_over_budget:
				message = _("Planned amount cannot be less than practical_amount")
				if self.budget_line_to.type == "expense" and \
					self.sudo().budget_line_to.planned_amount > self.sudo().budget_line_to.practical_amount:
					raise UserError(message)
				elif self.budget_line_to.type == "profit" and \
						self.sudo().budget_line_to.planned_amount < self.sudo().budget_line_to.practical_amount:
					raise UserError(message)
		self.state = "validate"
