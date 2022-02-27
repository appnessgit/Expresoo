from odoo import fields , api , models , _
import datetime
from dateutil.relativedelta import relativedelta
# from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError
import math
from odoo.tools import float_round
from odoo.tools.misc import format_date
from calendar import monthrange
import json

class hr_end_service(models.Model):
	_inherit = 'hr.end.service'

	state = fields.Selection([('draft', 'Draft'),
							  ('hrm', 'Waitting HR Manager Approval'),
							  ('fin2', 'Waitting Finance Manager Approval'),
							  ('confirm', 'Confirmed'),
							  ('post', 'Posted'),
							  ('cancel', 'Rejected')
							  ], default="draft", string="status",track_visibility='onchange')

	credit_acc = fields.Many2one("account.account", string="Credit Account")
	journal_id = fields.Many2one('account.journal', string="Journal")
	journal_entries = fields.Many2one('account.move', 'Journal Entry', readonly=True, track_visibility='onchange',copy=False)
	#Accounts
	leave_sett_acc = fields.Many2one("account.account", string="Leave Sattlement Account")
	arbitrary_dismissal_acc = fields.Many2one("account.account", string="Arbitrary Dismissal Account")
	benfit_acc = fields.Many2one('account.account', string='Benfit Account')
	insurance_acc = fields.Many2one('account.account', string='Insurance Account')
	#payment
	payment_method = fields.Many2one("account.journal", string="Payment Method")
	payment_date = fields.Date ("Payment Date")
	payment_entries = fields.Many2one('account.move', 'Journal Entry', readonly=True, track_visibility='onchange',copy=False)

	def update_activities(self):
		for rec in self:
			users = []
			rec.activity_unlink(['hr_eos_main.mail_eos_approve'])
			if rec.state not in ['hrm','fin2','cancel']:
				continue
			message = ""

			if rec.state == 'hrm':
				users = self.env.ref('hr.group_hr_manager').users
				message = "Approve"

			if rec.state == 'fin2':
				users = self.env.ref('account.group_account_manager').users
				message = "Approve"

			elif rec.state == 'cancel':
				users = [self.create_uid]
				message = "cancelled"
			for user in users:
				self.activity_schedule('hr_eos_main.mail_eos_approve', user_id=user.id, note=message)


	def confirm_button(self):
		for rec in self:
			rec.state = 'fin2'
			self.activity_unlink(['hr_eos_main.mail_eos_approve'])
			rec.employee_id.contract_id.state='close'
			rec.employee_id.active=False
			rec.employee_id.user_id.active=False

			emails = rec.employee_id.work_email
			mail_content = "  Hello  "  ",<br> Your End of service  Settlement was approved."
			main_content = {
				'subject': _('EOS of %s') % (rec.employee_id.name),
				'author_id': rec.env.user.partner_id.id,
				'body_html': mail_content,
				'email_to': emails,
			}
			rec.env['mail.mail'].sudo().create(main_content).send()
			rec.update_activities()



	def action_fin2_approve(self):
		for rec in self:

			if not rec.credit_acc or not rec.journal_id:
				raise ValidationError("You must enter Credit account and journal to Confirm ")

			if not rec.leave_sett_acc and rec.leaves_amount > 0:
				raise ValidationError("You must enter leave Settlement account in leave Settlement tab ")


			if not rec.arbitrary_dismissal_acc and rec.gross_allowance > 0:
				raise ValidationError("You must enter arbitrary dismissal account in Arbitrary dismissal tab ")


			# if not rec.insurance_acc and rec.insurance_amount > 0:
			# if not rec.insurance_acc:
			# 	raise ValidationError("You Must Enter Insurance Account In Insurance Tab ")

			if not rec.benfit_acc and rec.benefit_amount > 0:
				raise ValidationError("You Must Enter Benfit Account In Benfit Tab ")

			if rec.total_allowances > 0:
				for line in rec.other_allowances_ids:
					if not line.account_id:
						raise ValidationError("You must enter the account in Other allowances Tab ")

			if rec.total_deduction > 0:
				for line in rec.other_deductions_ids:
					if not line.account_id:
						raise ValidationError("You must enter the account in Other deductions Tab ")


			if rec.total_amount < 0:
				raise ValidationError("The Total amount of EOS less Than zero, Please Clear loan or Custody or Other Deduction ")

			can_close = False
			move_obj = self.env['account.move']
			move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
			currency_obj = self.env['res.currency']
			created_move_ids = []
			for eos in self:
				end_service_date = eos.end_date
				company_currency = eos.employee_id.company_id.currency_id.id
				current_currency = self.env.user.company_id.currency_id.id
				amount = eos.total_amount
				eos_name = eos.employee_id.name
				reference = 'END OF Service ' + eos.employee_id.name
				journal_id = eos.journal_id.id
				move_vals = {
					'name': '/',
					'date': end_service_date,
					'ref': reference,
					'journal_id': journal_id,
					'state': 'draft',
					'eos_id': self.id,
				}
				move_id = move_obj.create(move_vals)


				move_line_vals = {
					'ref': reference,
					'name': 'END OF Service ' + eos.employee_id.name,
					'move_id': move_id.id,
					'account_id': eos.credit_acc.id,
					'debit': 0.0,
					'credit': eos.total_amount,
					'journal_id': journal_id,
					'currency_id': company_currency != current_currency and current_currency or False,
					'amount_currency': 0.0,
					'date': end_service_date,
					'eos_id': self.id,

				}
				move_line_obj.create(move_line_vals)

				if eos.leaves_amount > 0:
					move_line_vals2 = {
						'ref': reference,
						'name':'Leave Settlement ',
						'move_id': move_id.id,
						'account_id': eos.leave_sett_acc.id,
						'credit': 0.0,
						'debit': eos.leaves_amount,
						'journal_id': journal_id,
						'currency_id': company_currency != current_currency and current_currency or False,
						'amount_currency': 0.0,
						'date': end_service_date,
						'eos_id': self.id,
					}
					move_line_obj.create(move_line_vals2)

				if eos.gross_allowance > 0:
					move_line_vals5 = {
						'ref': reference,
						'name': 'Arbitrary dismissal ',
						'move_id': move_id.id,
						'account_id': eos.arbitrary_dismissal_acc.id,
						'credit': 0.0,
						'debit': eos.gross_allowance,
						'journal_id': journal_id,
						'currency_id': company_currency != current_currency and current_currency or False,
						'amount_currency': 0.0,
						'date': end_service_date,
						'eos_id': self.id,
					}
					move_line_obj.create(move_line_vals5)

				if rec.other_allowances_ids:
					for allowance in rec.other_allowances_ids:
						move_line_vals6 = {
							'ref': reference,
							'name':  _('Other Allowance ') + str(allowance.allowance_name) or " - " ,
							'move_id': move_id.id,
							'account_id': allowance.account_id.id,
							'credit': 0.0,
							'debit': allowance.amount,
							'journal_id': journal_id,
							'currency_id': company_currency != current_currency and current_currency or False,
							'amount_currency': 0.0,
							'date': end_service_date,
							'eos_id': self.id,
						}
						
						move_line_obj.sudo().create(move_line_vals6)


				if rec.other_deductions_ids:
					for deduction in rec.other_deductions_ids:
						move_line_vals7 = {
							'ref': reference,
							'name':  _('Other Deductions ') + str(deduction.deduction_name) or " + "  ,
							'move_id': move_id.id,
							'account_id': deduction.account_id.id,
							'credit': deduction.amount,
							'debit': 0.0,
							'journal_id': journal_id,
							'currency_id': company_currency != current_currency and current_currency or False,
							'amount_currency': 0.0,
							'date': end_service_date,
							'eos_id': self.id,
						}

						move_line_obj.sudo().create(move_line_vals7)

				if eos.benefit_amount > 0:
					move_line_vals9 = {
						'ref': reference,
						'name': 'Benfits',
						'move_id': move_id.id,
						'account_id': eos.benfit_acc.id,
						'credit': 0.0,
						'debit': eos.benefit_amount,
						'journal_id': journal_id,
						'currency_id': company_currency != current_currency and current_currency or False,
						'amount_currency': 0.0,
						'date': end_service_date,
						'eos_id': self.id,
					}
					move_line_obj.create(move_line_vals9)


				# if eos.insurance_amount > 0:
				# 	move_line_vals10 = {
				# 		'ref': reference,
				# 		'name': 'Insurance',
				# 		'move_id': move_id.id,
				# 		'account_id': eos.insurance_acc.id,
				# 		'credit': 0.0,
				# 		'debit': eos.insurance_amount,
				# 		'journal_id': journal_id,
				# 		'currency_id': company_currency != current_currency and current_currency or False,
				# 		'amount_currency': 0.0,
				# 		'date': end_service_date,
				# 		'eos_id': self.id,
				# 	}
				# 	move_line_obj.create(move_line_vals10)
				
				if rec.custody_installed:
					if rec.custody_ids:
						for custody in rec.custody_ids:
							move_line_vals11 = {
								'ref': reference,
								'name':  _('Custody ') + str(custody.name) or " - " ,
								'move_id': move_id.id,
								'account_id': custody.account_id.id,
								'credit': custody.amount,
								'debit': 0.0,
								'journal_id': journal_id,
								'currency_id': company_currency != current_currency and current_currency or False,
								'amount_currency': 0.0,
								'date': end_service_date,
								'eos_id': self.id,
							}	
							move_line_obj.sudo().create(move_line_vals11)

				if eos.loan_installed:
					if eos.total_loans > 0:
						move_line_vals12 = {
							# 'name': eos_name,
							# 'name': '/',
							'ref': reference,
							'name': 'Loan',
							'move_id': move_id.id,
							'account_id': eos.loan_acc.id,
							'credit': eos.total_loans,
							'debit': 0.0,
							'journal_id': journal_id,
							'currency_id': company_currency != current_currency and current_currency or False,
							'amount_currency': 0.0,
							'date': end_service_date,
							'eos_id': self.id,
						}
						move_line_obj.create(move_line_vals12)

				####### update date from date of the last confirm of Finance Manager#####

				# self.write({'move_id': move_id.id})
				move_id.action_post() #Post Entries
				rec.state = 'confirm'
				rec.journal_entries = move_id.id
				rec.slip_id.action_payslip_done()
				rec.employee_id.contract_id.state='close'
				rec.employee_id.active=False
				# rec.employee_id.user_id.active=False
				rec.activity_unlink(['hr_eos_main.mail_eos_approve'])

			return True


	def action_fin2_reject(self):
		for rec in self: 
			rec.state = 'cancel'
		self.activity_unlink(['hr_eos_main.mail_eos_approve'])

	def action_paid(self):
		for rec in self:
			if not rec.payment_method or not rec.payment_date:
				raise ValidationError("Please Select Payment Method and Payment Date In Payment Tap For Complete Payment ")

			move_obj = self.env['account.move']
			move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
			currency_obj = self.env['res.currency']
			created_move_ids = []
			for eos in self:
				end_service_date = eos.payment_date
				company_currency = eos.employee_id.company_id.currency_id.id
				current_currency = self.env.user.company_id.currency_id.id
				amount = eos.total_amount
				eos_name = eos.employee_id.name
				reference = 'EOS Payment for ' + eos.employee_id.name
				journal_id = eos.payment_method.id
				move_vals = {
					'name': '/',
					'date': end_service_date,
					'ref': reference,
					'journal_id': journal_id,
					'state': 'draft',
					'eos_id': self.id,
				}
				move_id = move_obj.create(move_vals)
				move_line_vals = {
					# 'name':'/' ,
					'ref': reference,
					'name': 'EOS Payment for ' + eos.employee_id.name,
					'move_id': move_id.id,
					'account_id': eos.payment_method.default_account_id.id,
					'debit': 0.0,
					'credit': amount,
					'journal_id': journal_id,
					'currency_id': company_currency != current_currency and current_currency or False,
					'amount_currency': 0.0,
					'date': end_service_date,
					'eos_id': self.id,

				}
				move_line_obj.create(move_line_vals)
				move_line_vals2 = {
					# 'name': eos_name,
					# 'name': '/',
					'ref': reference,
					'name': 'EOS Payment for ' + eos.employee_id.name,
					'move_id': move_id.id,
					'account_id': eos.credit_acc.id,
					'credit': 0.0,
					'debit': amount,
					'journal_id': journal_id,
					'currency_id': company_currency != current_currency and current_currency or False,
					'amount_currency': 0.0,
					'date': end_service_date,
					'eos_id': self.id,
				}
				move_line_obj.create(move_line_vals2)
				# self.write({'move_id': move_id.id})
				move_id.action_post() #Post Entries
				rec.state = 'post'
				rec.payment_entries = move_id.id
			return True



class eos_other_allowance(models.Model):
	_inherit = 'hr.eos.other.allowance'

	account_id = fields.Many2one('account.account',string='Account')

class eos_other_deduction(models.Model):
	_inherit = 'hr.eos.other.deduction'

	account_id = fields.Many2one('account.account',string='Account')



class eosAccountMove(models.Model):
	_inherit = 'account.move'

	eos_id = fields.Many2one('hr.end.service',string='End of Service')


class eosAccountMove(models.Model):
	_inherit = 'account.move.line'

	eos_id = fields.Many2one('hr.end.service',string='End of Service')


	
	
