# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _
import json
#Import logger
import logging
#Get the logger
_logger = logging.getLogger(__name__)


class PayrollReportXls(models.AbstractModel):
	_name = 'report.hr_payroll_report.payroll_report_xlsx'
	_description = "Payroll Report"
	_inherit = 'report.report_xlsx.abstract'

	def generate_xlsx_report(self,workbook, data,lines):
		#We can recieve the data entered in the wizard here as data
		batch1_id = data['batch1_id'][0]
		batch2_id = data['batch2_id'][0] if data['batch2_id'] else False
		batch1 = batch2 = False
		if batch1_id:
			batch1 = self.env['hr.payslip.run'].browse(batch1_id)
		if batch1_id:
			batch2 = self.env['hr.payslip.run'].browse(batch2_id)

		report_type = data['report_type']
		rules = self.env['hr.salary.rule'].browse(data['rule_ids'])
		rule_names = [rule.name for rule in rules]
		payslips1 = False


		if data['applied_for'] == "employee" and data['employee_ids']:
			# raise UserError(json.dumps(data, indent=4, sort_keys=True, default=str))
			employees = self.env['hr.employee'].search([('id', 'in', data['employee_ids'])])
			payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', batch1_id), ('employee_id', 'in', employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id', '=', batch2_id), ('employee_id', 'in', employees.ids)])
		elif data['applied_for'] == "department" and data['department_ids']:
			departments = [dep.name for dep in self.env['hr.department'].search([('id', 'in', data['department_ids'])])]
			employees = self.env['hr.employee'].search([('department_id', 'in', data['department_ids'])])
			payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', batch1_id), ('employee_id', 'in', employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id', '=', batch2_id), ('employee_id', 'in', employees.ids)])
		else:
			employees = self.env['hr.employee'].search([])
			payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', batch1_id), ('employee_id', 'in', employees.ids)])
			if batch2_id:
				payslips1 = self.env['hr.payslip'].search([('payslip_run_id','=',batch2_id), ('employee_id', 'in', employees.ids)])

		employees = employees.filtered(lambda e: e in payslips.mapped('employee_id'))


		format1 = workbook.add_format({'font_size': 12, 'bold': False, 'bg_color': '#02901F', 'font_color': '#FFFFFF'})
		format2 = workbook.add_format({'bold': False})

		format1.set_text_wrap()
		format2.set_text_wrap()

		if report_type == 'compare':
			sheet = workbook.add_worksheet("Variance Report")

			sheet.set_column("A:M", 30)

			sheet.write('A1', "E Code", format1)
			# sheet.write('B1', "Grade", format1)
			sheet.write('B1', "Employee Name", format1)
			sheet.write('C1', "Job Title", format1)
			sheet.write('D1', "Department", format1)
			row = 0

			for employee in employees:
				row += 1
				payslip = payslips.filtered(lambda p: p.employee_id.id == employee.id)
				payslip2 = payslips1.filtered(lambda p: p.employee_id.id == employee.id)

				sheet.write(row, 0, employee.emp_code, format2)
				# sheet.write(row, 1, employee.contract_id.grade_id.name if employee.contract_id and employee.contract_id.grade_id else '', format2)
				sheet.write(row, 1, employee.name, format2)
				sheet.write(row, 2, employee.job_id.name if employee.job_id else '', format2)
				sheet.write(row, 3, employee.department_id.name if employee.department_id else '', format2)
				sheet.write(row, 4, payslip.line_ids.filtered(lambda l: l.category_id.code == 'GROSS').total, format2)
				sheet.write(row, 5, payslip2.line_ids.filtered(lambda l: l.category_id.code == 'GROSS').total, format2)

		if report_type == 'rule':
			sheet = workbook.add_worksheet("Payroll Report")

			sheet.set_column("A:M", 30)

			sheet.write('A1', "E Code", format1)
			# sheet.write('B1', "Grade", format1)
			sheet.write('B1', "Name", format1)
			sheet.write('C1', "Job Title", format1)
			sheet.write('D1', "Department", format1)
			row = 3
			for rule in rule_names:
				row += 1
				sheet.write(0, row, rule, format1)

			row = 0

			for employee in employees:
				row += 1
				payslip = payslips.filtered(lambda p: p.employee_id.id == employee.id)
				if payslips1:
					payslip2 = payslips1.filtered(lambda p: p.employee_id.id == employee.id)

				sheet.write(row, 0, employee.emp_code, format2)
				# sheet.write(row, 1,employee.contract_id.grade_id.name if employee.contract_id and employee.contract_id.grade_id else '', format2)
				sheet.write(row, 1, employee.name, format2)
				sheet.write(row, 2, employee.job_id.name if employee.job_id else '', format2)
				sheet.write(row, 3, employee.department_id.name if employee.department_id else '', format2)
				column = 3
				for rule in rules:
					column += 1
					amount = payslip.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id).total
					sheet.write(row, column, amount, format2)

		if report_type == 'total':
			sheet = workbook.add_worksheet("Variance Report (Total)")

			sheet.set_column("A:M", 30)

			sheet.write('A1', "E Code", format1)
			# sheet.write('B1', "Grade", format1)
			sheet.write('B1', "Name", format1)
			sheet.write('C1', "Job Title", format1)
			sheet.write('D1', "Department", format1)
			column = 3
			for rule in rule_names:
				column += 1
				sheet.write(0, column, rule, format1)

			batches = [batch1, batch2]
			for batch in batches:
				column += 1
				sheet.write(0, column, batch.name, format1)
			column += 1
			sheet.write(0, column, "Difference", format1)
			row = 0

			difference_list = []
			for employee in employees:
				row += 1
				payslip = payslips.filtered(lambda p: p.employee_id.id == employee.id)
				if payslips1:
					payslip2 = payslips1.filtered(lambda p: p.employee_id.id == employee.id)

				sheet.write(row, 0, employee.emp_code, format2)
				# sheet.write(row, 1,employee.contract_id.grade_id.name if employee.contract_id and employee.contract_id.grade_id else '', format2)
				sheet.write(row, 1, employee.name, format2)
				sheet.write(row, 2, employee.job_id.name if employee.job_id else '', format2)
				sheet.write(row, 3, employee.department_id.name if employee.department_id else '', format2)
				column = 3
				for rule in rules:
					column += 1
					amount = payslip.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id).total
					sheet.write(row, column, amount, format2)

				column += 1
				batch1_payslip = payslip.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').total
				_logger.critical("batch1_payslip " + str(batch1_payslip))
				sheet.write(row, column, batch1_payslip, format2)
				column += 1
				batch2_payslip = payslip2.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').total
				_logger.critical("batch2_payslip " + str(batch2_payslip))
				sheet.write(row, column, batch2_payslip, format2)
				column += 1
				difference = batch1_payslip - batch2_payslip
				difference_list.append(difference)
				sheet.write(row, column, difference, format2)

			#Total Row
			row += 1
			sheet.write(row, 0 , "Total", format1)
			sheet.write(row, 1 , " ", format1)
			sheet.write(row, 2 , " ", format1)
			sheet.write(row, 3 , " ", format1)
			sheet.write(row, 4 , " ", format1)
			column = 3
			rule_total = 0.0
			for rule in rules:
				column += 1
				amount = payslips.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id).mapped('total')
				rule_total = sum(amount)
				sheet.write(row, column, rule_total, format1)
			column += 1
			batch1_amount = sum(payslips.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').mapped('total'))
			sheet.write(row, column, batch1_amount, format1)
			column += 1
			batch2_amount = sum(payslips1.line_ids.filtered(lambda l: l.salary_rule_id.category_id.name == 'Net').mapped('total'))
			sheet.write(row, column, batch2_amount, format1)
			column += 1
			_logger.critical("difference_list " + str(difference_list))
			batch_difference = batch1_amount - batch2_amount
			sheet.write(row, column, batch_difference, format1)

		if report_type == 'emp_variance':

			batches = [batch1, batch2]
			batch_ids = [batch1_id, batch2_id]
			payslips = self.env['hr.payslip'].search([('payslip_run_id', 'in', batch_ids)])

			for batch in batches:
				sheet = workbook.add_worksheet(batch.name)
				sheet.set_column("A:M", 30)

				sheet.write('A1', "Employee ", format1)
				row = 0
				for rule in rule_names:
					row += 1
					sheet.write(0, row, rule, format1)

				row = 0

				for employee in employees:
					row += 1
					payslip = payslips.filtered(lambda p: p.employee_id.id == employee.id and p.payslip_run_id.id == batch.id)

					sheet.write(row, 0, employee.name, format2)

					column = 0
					for rule in rules:
						column += 1
						amount = payslip.line_ids.filtered(lambda l: l.salary_rule_id.id == rule.id).total
						sheet.write(row, column, amount, format2)