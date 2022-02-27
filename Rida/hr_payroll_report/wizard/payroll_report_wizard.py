# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PayrollAnnualReport(models.TransientModel):
	_name = 'wizard.payroll.annual.report'

	@api.model
	def _get_default_batch1(self):
		batch1 = False
		if len(self.env['hr.payslip.run'].search([('state','!=','cancel')])) >= 2:
			batch1 = self.env['hr.payslip.run'].search([('state','!=','cancel')])[-2]
		return batch1 and batch1.id or False

	@api.model
	def _get_default_batch2(self):
		batch2 = False
		if len(self.env['hr.payslip.run'].search([('state','!=','cancel')])) >= 1:
			batch2 = self.env['hr.payslip.run'].search([('state','!=','cancel')])[-1]
		return batch2 and batch2.id or False

	applied_for = fields.Selection([('all','All'),('employee','Employees'),('department','Department')],'Applied For', default="all")
	# report_type = fields.Selection([('compare','Variance Report Basic'),('rule','Payroll Report'),('total','Variance Report Total')],'Report', default="rule")
	report_type = fields.Selection([('rule','Payroll Report'),('total','Variance Report Total')],'Report', default="rule")
	employee_ids = fields.Many2many('hr.employee')
	department_ids = fields.Many2many('hr.department')
	batch1_id = fields.Many2one('hr.payslip.run',default=_get_default_batch1)
	batch2_id = fields.Many2one('hr.payslip.run',default=_get_default_batch2)
	date_from = fields.Date('Date from')
	date_to = fields.Date('Date to')
	report_id= fields.Many2one('payslip.report.config')
	rule_ids =fields.Many2many("hr.salary.rule")
	paper_format = fields.Selection([("A4","A4"),("A3","A3")], default="A4")
	bank_report = fields.Boolean(string='Bank Report', default=False)
	bank_date_1 = fields.Char(string='Date (1)')
	bank_date_2 = fields.Char(string='Date (2)')

	@api.onchange('report_id')
	def _onchange_report_id(self):
		for rec in self:
			pass
			if rec.report_id.rule_ids:
				rec.rule_ids = rec.report_id.rule_ids.ids
				rec.paper_format = rec.report_id.paper_format

	@api.onchange('report_type')
	def onchange_report_type(self):
		self.update({
			'batch2_id': False,
		})

	@api.onchange('bank_report')
	def onchange_bank_report(self):
		if self.bank_report:
			self.report_type = 'rule'   

	def print_report(self):
		self.ensure_one()
		[data] = self.read()
		if not data.get('batch1_id'):
			raise UserError(_('Please set Salary Batch'))
		if self.report_type == 'compare' and not data.get('batch2_id'):
			raise UserError(_('Please set Salary Batch to compare.'))

		if self.applied_for == 'department' and not data.get('department_ids'):
			raise UserError(_('You have to select at least one department.'))
		if self.applied_for == 'employee' and not data.get('employee_ids'):
			raise UserError(_('You have to select at least one Employee.'))

		date_from = data['date_from']
		date_to = data['date_to']


		payroll_date_from = self.batch1_id.date_start
		payroll_date_to = self.batch1_id.date_end

		batch1_id = data['batch1_id'][0]
		batch2_id = data['batch2_id'][0] if data['batch2_id'] else False
		if batch1_id:
			batch1 = self.env['hr.payslip.run'].browse(batch1_id)
		if batch2_id:
			batch2 = self.env['hr.payslip.run'].browse(batch2_id)

		batches = [batch1, batch2] if batch2_id else [batch1]

		report_type=data['report_type']
		rules = self.rule_ids
		rules_name = [rule.name for rule in self.rule_ids]
		departments = []
		payslips1 = False

		if self.applied_for == "employee" and self.employee_ids.ids:
			employees = self.env['hr.employee'].search([('id','in',self.employee_ids.ids)])
			payslips = self.env['hr.payslip'].search([('payslip_run_id','=',batch1_id),('employee_id','in',employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id','=',batch2_id),('employee_id','in',employees.ids)])
		elif self.applied_for == "department" and self.department_ids.ids:
			departments = [dep.name for dep in self.department_ids]
			employees = self.env['hr.employee'].search([('department_id','in',self.department_ids.ids)])
			payslips = self.env['hr.payslip'].search([('payslip_run_id','=',batch1_id),('employee_id','in',employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id','=',batch2_id),('employee_id','in',employees.ids)])
		else:
			employees = self.env['hr.employee'].search([])
			payslips = self.env['hr.payslip'].search([('payslip_run_id','=',batch1_id),('employee_id','in',employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id','=',batch2_id),('employee_id','in',employees.ids)])

		employees = employees.filtered(lambda e: e in payslips.mapped('employee_id'))

		# Paper Format #
		pf = self.paper_format
		orientation = "Landscape" if pf == "A3" else "Portrait"
		if self.report_type =="compare":
			pf = "A3"
			orientation = "Landscape"
		paper_format = self.env['report.paperformat'].search([['format', '=', pf]], limit=1)
		if not paper_format:
			# raise ValidationError("Format not found!")
			paper_format = self.sudo().env['report.paperformat'].create( {'name': pf + " Format", 'format': pf, 'orientation': orientation})
		report_r = self.env['ir.actions.report'].search([['report_name', '=', 'hr_payroll_annual_report.payroll_annual_report_temp']])
		
		batch_names = [batch.name for batch in batches]
		batch_ids = [batch.id for batch in batches]

		batch1_total = sum(payslips.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').mapped('total'))
		batch2_total = 0
		if batch2_id:
			batch2_total = sum(payslips1.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').mapped('total'))
		# raise UserError(sum(payslips.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').mapped('total')))
		report_r.sudo().write({'paperformat_id': paper_format.id})
		datas = {
			'employees': employees.ids,
			'departments': departments,
			'payslips': payslips.ids,
			'payslips1': payslips1.ids if payslips1 else [],
			'report_type': report_type,
			'rules': rules.ids,
			'rules_name': rules_name,
			'batch_ids': batch_ids,
			'batch_names': batch_names,
			'batch1_total':batch1_total,
			'batch2_total':batch2_total,
			'form': data,
			'payroll_date_from':payroll_date_from,
			'payroll_date_to': payroll_date_to,
			'bank_date_1':data['bank_date_1'],
			'bank_date_2':data['bank_date_2'],
		}
		if self.bank_report:
			return self.env.ref('hr_payroll_report.hr_payroll_bank_report').report_action(self, data=datas)
		else:
			return self.env.ref('hr_payroll_report.hr_payroll_annual_report').report_action(self, data=datas)

	def print_report_xls(self):
		self.ensure_one()
		[data] = self.read()
		if not data.get('batch1_id'):
			raise UserError(_('Please set Salary Batch'))
		if self.report_type == 'compare' and not data.get('batch2_id'):
			raise UserError(_('Please set Salary Batch to compare.'))
		if self.applied_for == 'department' and not data.get('department_ids'):
			raise UserError(_('Please select at least one department.'))
		if self.applied_for == 'employee' and not data.get('employee_ids'):
			raise UserError(_('Please select at least one Employee.'))
		if data.get('batch2_id') and data.get('batch1_id') == data.get('batch2_id'):
			raise UserError('Please select a different batch to compare.')
		return self.env.ref('hr_payroll_report.payroll_xlsx').report_action(self, data=data)
