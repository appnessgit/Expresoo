# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
from calendar import monthrange
import time

class hr_displine_report_wizard(models.TransientModel):
    _name='hr.displine.report.wizard'

    employee_id = fields.Many2one('hr.employee', "Employee")
    date_from =fields.Date("Date From")
    date_to =fields.Date("Date To")

    def print_report(self):
        self.ensure_one()
        [data] = self.read()

        datas = {
            'ids': [],
            'model': 'hr.employee.discipline',
            'form': data,
        }
        return self.env.ref('hr_disciplinary.hr_displine_employee_report').report_action(self,data=datas)

class FoReport(models.AbstractModel):
    _name = 'report.hr_disciplinary.displine_employee_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        # department_id = data['form']['department_id']
        domain = [('date', '>=', str(date_from)),('date','<=',str(date_to))]
        # if department_id:
            # domain.append(('department_id','=',department_id[0]))
        employee = data['form']['employee_id']
        if employee :

            emp_list = self.env['hr.employee.discipline'].search(
                [('employee_id', '=', employee[0]),
                 ['violation_date', '>=', data['form']['date_from']],
                 ['violation_date', '<=', data['form']['date_to']]])

        else:
             emp_list = self.env['hr.employee.discipline'].search([
                                                   ['violation_date', '>=', data['form']['date_from']],
                 ['violation_date', '<=', data['form']['date_to']]])
        # raise UserError(employee[0])
        return {
           'data': data,
           'emp_list': emp_list,
           'date_from':date_from,
           'date_to':date_to,
           'employee':employee,
        }


