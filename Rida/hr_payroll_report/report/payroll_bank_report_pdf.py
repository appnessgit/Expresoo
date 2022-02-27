# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import models, api,fields, _
from odoo.exceptions import UserError
from num2words import num2words

class Payroll_annualReportParser(models.AbstractModel):
    _name = 'report.hr_payroll_annual_report.payroll_bank_report_temp'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        emp_ids=data['employees']
        slip_ids=data['payslips']
        rules_ids = data['rules']
        payroll_annual_report = self.env['ir.actions.report']._get_report_from_name('hr_payroll_annual_report.payroll_bank_report_temp')
        employees = self.env['hr.employee'].browse(emp_ids)
        payslips = self.env['hr.payslip'].browse(slip_ids)
        rules = self.env['hr.payslip.line'].search([('salary_rule_id','in',rules_ids),('slip_id','in',slip_ids)])
        banks = self.env['res.bank'].search([('id','=',employees.mapped('bank_account_id').mapped('bank_id').ids)])

        report_data = {}
        
        grand_total = 0.0
        for bank in banks:
            list = []
            total = 0.0
            for payslip in payslips:
                if payslip.bank_account_id.bank_id == bank:
                    total = total + payslip.net_amount
                    total = round(total,2)
                    list.append(payslip)
            report_data.update({bank.name:{'payslips':list,'total':total}})
            grand_total = grand_total + total
        return {
            'bank_date_1':data['bank_date_1'],
            'bank_date_2':data['bank_date_2'],
            'banks':banks,
            'docs_emp': emp_ids,
            'docs': payslips,
            'report_data':report_data,
            'grand_total':grand_total,
            'grand_total_text':num2words(grand_total)
        }




