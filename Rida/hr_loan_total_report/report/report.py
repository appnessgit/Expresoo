# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanTotalReport(models.AbstractModel):
    _name = 'report.hr_loan_total_report.loan_total_report_template'
    _description = 'Loan Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # self.ensure_one()
        # [data] = self.read()
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        # docids=data['ids']
        
        department = data['form']['department_id']
        s = data['form']['date_from']
        e = data['form']['date_to']
        department_name = ""
        if department:
            department_name = department[1]
            emp_list = self.env['hr.loan'].search([('department_id', '=', department[1]),'|',('active','=',False),('active','=',True),['payment_start_date','>=', data['form']['date_from']],['payment_start_date','<=', data['form']['date_to']]])
        else:
            department_name = False
            emp_list = self.env['hr.loan'].search(['|',('active','=',False),('active','=',True),['payment_start_date','>=', data['form']['date_from']],['payment_start_date','<=', data['form']['date_to']]])
  
        return {
            'form': data,
            'department': department_name,
            'emp_list': emp_list,
            'from_date': s,
            'to_date': e,
        }
