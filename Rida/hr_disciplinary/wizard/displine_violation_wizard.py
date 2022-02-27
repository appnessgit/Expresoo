# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning
from calendar import monthrange
import time

class hr_displine_report_violation_wizard(models.TransientModel):
    _name='hr.displine.report.violation.wizard'


    violation_id = fields.Many2one('hr.violation', 'Violation')
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
        return self.env.ref('hr_disciplinary.hr_violation_report_id').report_action(self,data=datas)


class FoReport(models.AbstractModel):
    _name = 'report.hr_disciplinary.displine_violation_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        violation = data['form']['violation_id']
        if violation :
            # violation_name = violation[0]
            violation_list = self.env['hr.employee.discipline'].search([('violation_id', '=', violation[0]),['violation_date', '>=', data['form']['date_from']],['violation_date', '<=', data['form']['date_to']]])
        else:
             violation_list = self.env['hr.employee.discipline'].search([['violation_date', '>=', data['form']['date_from']],['violation_date', '<=', data['form']['date_to']]])

        return {
            # 'violation': violation_name,
            'violation_list': violation_list,
            'date_from': date_from,
            'date_to': date_to,
              }
