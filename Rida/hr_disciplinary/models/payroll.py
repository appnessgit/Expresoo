# -*- coding: utf-8 -*-
from odoo import models, fields, api
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
import time
import datetime

class HrPayslipEmployees(models.TransientModel):
	_inherit="hr.payslip.employees"

	def compute_sheet(self):
		active_id = self._context.get('active_id')
		date_from = self.env['hr.payslip.run'].search([('id','=',active_id)]).date_start
		date_to = self.env['hr.payslip.run'].search([('id','=',active_id)]).date_end
		slp_start = datetime.datetime.strftime(date_from, '%Y-%m-%d')
		slp_end = datetime.datetime.strftime(date_to, '%Y-%m-%d')
		total_amount = 0.00
		discplines = self.env['hr.employee.discipline'].search([('suspend_payroll','=',True),('state','=','confirm')])
		suspended_emps = []
		for dicsp in discplines:
			if dicsp.violation_date != False:
				month = datetime.datetime.strftime(dicsp.violation_date,'%Y-%m-%d')
				if month >= slp_start and month <= slp_end:
					suspended_emps.append(dicsp.employee_id.id)
		for emp in self.employee_ids:
			if emp.id in suspended_emps:	
				self.write({'employee_ids':[(3, emp.id)]})
		res = super(HrPayslipEmployees,self).compute_sheet()
		return res

class hr_sanction_line(models.Model):
	_inherit = 'hr.sanction.line'

	slip_id = fields.Many2one('hr.payslip','Slip')

class hr_payslip(models.Model):
	_name ='hr.payslip'
	_inherit='hr.payslip'

	sanction_ids = fields.One2many('hr.sanction.line','slip_id')
	sanction_total = fields.Float('Amount',compute="compute_sanction_total")

	@api.depends('sanction_ids')
	def compute_sanction_total(self):
		for rec in self:
			total = 0
			for line in rec.sanction_ids:
				total += line.amount
			rec.sanction_total = total

	def compute_sheet(self):
		self.compute_discipline()
		res = super(hr_payslip,self).compute_sheet()
		return res

	def compute_discipline(self):
		for rec in self:
			payslip_id = rec.id
			emp_id = rec.employee_id.id
			slp_start = datetime.datetime.strftime(self.date_from, '%Y-%m-%d')
			slp_end = datetime.datetime.strftime(self.date_to, '%Y-%m-%d')
			total_amount = 0.00
			discplines = self.env['hr.employee.discipline'].search([('employee_id', '=', emp_id),('suspend_payroll','=',True),('state','=','confirm')])

			for dicsp in discplines:
				if dicsp.violation_date != False:
					month = datetime.datetime.strftime(dicsp.violation_date,'%Y-%m-%d')#.strftime('%m')
					if month >= slp_start and month <= slp_end :
						pass

			sanctions = self.env['hr.sanction.line'].search([('employee_id', '=', emp_id),('deducted','=',True),('state','=','confirm')])
			for sanction in sanctions:
				if sanction.date != False:
					month = datetime.datetime.strftime(sanction.date,'%Y-%m-%d')#.strftime('%m')
					for rec in sanction:
						if month >=slp_start and month <= slp_end :
							rec.write({'slip_id':self.id})



