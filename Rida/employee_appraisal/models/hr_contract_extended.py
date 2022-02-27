
from email.policy import default
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime



import time

import datetime

from datetime import date

from datetime import datetime, date, time


class HrContract(models.Model):
    _inherit = 'hr.contract'

    probation_end = fields.Date(compute='_compute_probation_end', string='Probatio End')
    old_contract = fields.Boolean(string='Is Old Contract?', default=False)
    contract_permanent = fields.Boolean(string='Is Permanent Contract?', default=False)
    
    @api.onchange('date_start')
    def _compute_probation_end(self):
        for rec in self:
            Y,m,d = str(rec.date_start).split('-')
            m=int(m)+3
            if m==13:
                m=1
            elif m==14:
                m=2
            elif m==15:
                m=3
            else:
                pass
            rec.probation_end = rec.date_start.replace(month=m)

    # @api.onchange('date_start')
    @api.model
    def _cron_check_evaluate_employee(self):
        for rec in self.env['hr.contract'].search([('state','=','open'),('old_contract','=',False)]):
            diff = relativedelta(fields.Date.today(), rec.probation_end)
            if fields.Date.today() >=  rec.probation_end:
                rec.old_contract = True
            elif (diff.days*-1)+1 == 14 and  diff.months == 0 and diff.years == 0:
                hr_manager_user = rec.env.ref('hr.group_hr_user').users
                appraisal = self.env['employee.appraisal'].search([('employee_id','=',rec.employee_id.id),
                           ('date_from','=',rec.date_start or fields.Date.today()) ,
                           ('date_to','=',rec.date_end or fields.Date.today())])
                if not appraisal:
                    appraisal = self.env['employee.appraisal'].create({
                            'employee_id':rec.employee_id.id,
                            'date_from':rec.date_start or fields.Date.today() ,
                            'date_to':rec.date_end or fields.Date.today(),
                            'rate':0,
                        }) 
                for manager in hr_manager_user:
                    email = manager.employee_id.work_email
                    mail_content = ("  Dear %s " ",<br> "
                    "The current empolyee %s have to be evaluated." ",<br> "
                    "Regards," %(manager.name , rec.employee_id.name) )
                    main_content = {
                        'subject': 'Evaluation',
                        'author_id': self.env['res.users'].browse(1).partner_id.id,
                        'body_html': mail_content,
                        'email_to': email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
                    appraisal.activity_schedule('employee_appraisal.mail_probation_reminder_appraisal', user_id=manager.id)
          
    @api.model
    def _cron_employee_expiration_period(self):
        contracts = self.env['hr.contract'].search([('state','=','open'),('contract_permanent','=',False)])
        for rec in contracts:
            diff_s = relativedelta(fields.Date.today(),rec.date_start)
            diff_d = relativedelta(rec.date_end,fields.Date.today())
            diff_sd = relativedelta(rec.date_end,rec.date_start)
            if diff_s.years > 2:
                rec.contract_permanent= True
            else:
                if rec.date_end and  diff_sd.years <= 2 : 
                    if diff_d.months+1 == 2:
                        Y,m,d = str(fields.Date.today()).split('-')
                        y,M,D = str(rec.date_end).split('-')
                        D=int(D)
                        m=int(m)+2
                        if m==13:
                            m=11
                        elif m==14:
                            m=12
                        else:
                            pass
                        period_end = fields.Date.today().replace(month=m ,day=D)
                        hr_manager_user = rec.env.ref('hr.group_hr_user').users
                        contract = self.env['hr.contract'].search([('date_end','=',period_end)])
                        for manager in hr_manager_user:
                            email = manager.employee_id.work_email
                            mail_content = ("  Dear %s " ",<br> "
                            "The contract of  %s Will expire in 2 months." ",<br> "
                            "Regards," %(manager.name , rec.employee_id.name) )
                            main_content = {
                                'subject': 'Contract Expiration Remainder',
                                'author_id': self.env['res.users'].browse(1).partner_id.id,
                                'body_html': mail_content,
                                'email_to': email,
                            }
                            self.env['mail.mail'].sudo().create(main_content).send()
                        contract.activity_schedule('employee_appraisal.mail_contract_expiratin_reminder', user_id=manager.id)
            










