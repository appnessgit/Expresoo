# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import models, api,fields, _
from odoo.exceptions import UserError

class Payroll_annualReportParser(models.AbstractModel):
    _name = 'report.hr_payroll_report.payroll_annual_report_temp'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        emp_ids=data['employees']
        # dep_ids=data['departments']
        slip_ids=data['payslips']
        slip_ids1=data['payslips1']
        rules_ids = data['rules']
        payroll_annual_report = self.env['ir.actions.report']._get_report_from_name('hr_payroll_report.payroll_annual_report_temp')
        employees = self.env['hr.employee'].browse(emp_ids)
        payslips = self.env['hr.payslip'].browse(slip_ids)
        payslips1 = self.env['hr.payslip'].browse(slip_ids1)
        rules = self.env['hr.payslip.line'].search([('salary_rule_id','in',rules_ids),('slip_id','in',slip_ids)])
        rules2 = self.env['hr.payslip.line'].search([('salary_rule_id','in',rules_ids),('slip_id','in',slip_ids1)])
        rules_total = []
        for line in rules_ids:
            total = 0.0
            for rule in rules:
                if rule.salary_rule_id.id == line:
                    total+=rule.total
            rules_total.append(total)
        return {
            'docs_emp': emp_ids,
            # 'docs_dep': dep_ids,
            'docs': payslips,
            'docs1': payslips1,
            'rule_docs': rules,
            'rule_docs2': rules2,
            'rules_total':rules_total,
        }




