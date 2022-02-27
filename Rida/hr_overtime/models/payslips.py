from openerp import models, fields, api , _
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

class hr_payslip(models.Model):
    _name='hr.payslip'
    _inherit='hr.payslip'

    overtime = fields.Float("Overtime", readonly=True)

    def compute_sheet(self):
        self.compute_overtime()
        res = super(hr_payslip,self).compute_sheet()
        return res

    def compute_overtime(self):
        for rec in self:
            ovt = 0.0
            pay_obj = self.env['hr.payslip']
            pay_id = rec.id
            emp_id = rec.employee_id.id
            ovtm_obj = self.env['hr.over.time']
            ovtm_ids = ovtm_obj.search([('employee_id','=',emp_id),('date','>=',rec.date_from),('date','<=',rec.date_to),('state','=','paid')])
            for ovtm_id in ovtm_ids:
                ovt += ovtm_id.net_overtime
            rec.overtime = ovt
