# -*- coding: utf-8 -*-

from odoo import fields , api , models , _
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
from datetime import datetime, timedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _order = 'emp_code'

    display_name = fields.Char("Display Name", compute='compute_display_name', store=True)
    emp_code = fields.Char(string='Employee Code')
    id_expiry_date = fields.Date(string='ID Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Passport Expiry Date', help='Expiry date of Passport ID')
    age = fields.Integer(string="Age", readonly=True, compute="_compute_age")
    custody_id = fields.One2many('hr.custody', 'employee_id', groups="hr.group_hr_user")
    relative_ids = fields.One2many(string='Relatives',comodel_name='hr.employee.relative',inverse_name='employee_id', groups="hr.group_hr_user")
    training_ids = fields.One2many('hr.training', 'employee_id', groups="hr.group_hr_user")
    allow_pasi = fields.Boolean(string='Allow PASI')
    # employee_attendance_ids = fields.One2many(comodel_name='hr.attendance', inverse_name='employee_id', domain=lambda self:self._get_employee_id_domain())
    # total_w_hours = fields.Float(string='Total Worked Hours', compute = 'total_worked_hours')

    # def _get_employee_id_domain(self):
    #     return [('employee_id', '=', self.id)]

    # @api.depends('employee_attendance_ids.worked_hours')
    # def total_worked_hours(self):
    #     for emp in self:
    #         employee_attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id)])
    #         for rec in employee_attendance:
    #             emp.total_w_hours += rec.worked_hours

    @api.depends('emp_code', 'name')
    def compute_display_name(self):
        for record in self:
            display_name = record.name
            if record.emp_code:
                display_name = "[%s] %s" % (record.emp_code, display_name)
            record.display_name = display_name

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthday:
                age = relativedelta(fields.Date.today(), record.birthday).years
            record.age = age



    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport to HR Manager and Cc TO employee"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        employees = self.env.ref('hr.group_hr_user').users.mapped('employee_ids')
        emails = [employee.work_email for employee in employees]
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  "  ",<br> ID of " + str(i.name) + " # "  + str(i.identification_id) +" " + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emails,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  "  ",<br> Passport of " + str(i.name) + " # " + str(i.passport_id) + " " + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emails,
                        'email_cc': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

        match2 = self.search([])
        for i in match2:
            if i.visa_expire:
                exp_date2 = fields.Date.from_string(i.visa_expire) - timedelta(days=14)
                if date_now >= exp_date2:
                    mail_content = "  Hello  "  ",<br> Visa of  " + i.name + " # " + i.visa_no +" " +"is going to expire on " + \
                                   str(i.visa_expire) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Visa-%s Expired On %s') % (i.visa_no, i.visa_expire),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emails,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()


class hrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    emp_code = fields.Char(string='Employee Code')
    allow_pasi = fields.Boolean(string='Allow PASI')