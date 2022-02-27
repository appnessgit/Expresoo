from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime


class Bills_Workflow(models.Model):
    _inherit = 'account.move'

    comment = fields.Text(placeholder="Insert your Comment Here...")
    dm_dep = fields.Many2one('res.users', string = 'Depratment User')
    dm_man = fields.Many2one('res.users', string = 'Manager')
    dm_account = fields.Many2one('res.users', string = 'Accountant')
    dm_adv = fields.Many2one('res.users', string = 'Advisor')
    dm_aud = fields.Many2one('res.users', string = 'Auditor')
    dm_gm = fields.Many2one('res.users', string = 'General Manager')


    dm_date_dep = fields.Date(string='Deprartment User Approval Date')
    dm_date_man = fields.Date(string='Manager Approval Date')
    dm_date_account = fields.Date(string='Accountant Approval Date')
    dm_date_adv = fields.Date(string='Advisor Approval Date')
    dm_date_aud = fields.Date(string='Auditor Approval Date')
    dm_date_gm = fields.Date(string='General Manager Approval Date')



    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('department', 'Department'),
        ('manager', 'Manager'),
        ('accountant', 'Accountant'),
        ('advisor', 'Advisor'),
        ('auditor', 'Auditor'),
        ('gm', 'GM'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    def action_dep(self):
        # for rec in self:
        #     rec.state = "department"
        for rec in self:
            # today = fields.Date.today()
            # self.mt_date = today
            rec.write({'state': 'department',
                       'dm_dep': self.env.user,
                       'dm_date_dep': fields.Date.today(),

                       })

    def action_manager(self):
        # for rec in self:
        #     rec.state = "manager"
        for rec in self:
            # today = fields.Date.today()
            # self.mt_date = today
            rec.write({'state': 'manager',
                       'dm_man': self.env.user,
                       'dm_date_man': fields.Date.today(),

                       })

    def action_accountant(self):
        # for rec in self:
        #     rec.state = "accountant"
        for rec in self:
            # today = fields.Date.today()
            # self.mt_date = today
            rec.write({'state': 'accountant',
                       'dm_account': self.env.user,
                       'dm_date_account': fields.Date.today(),

                       })

    def action_advisor(self):
        # for rec in self:
        #     rec.state = "advisor"
        for rec in self:
        #     today = fields.Date.today()
        #     self.mt_date = today
            rec.write({'state': 'advisor',
                       'dm_adv': self.env.user,
                       'dm_date_adv': fields.Date.today(),

                       })

    def action_auditor(self):
        # for rec in self:
        #     rec.state = "auditor"
        for rec in self:

            rec.write({'state': 'auditor',
                       'dm_aud': self.env.user,
                       'dm_date_aud': fields.Date.today(),

                       })

    def action_gm(self):
        # for rec in self:
        #     rec.state = "gm"
        for rec in self:
        #     today = fields.Date.today()
        #     self.mt_date = today
            rec.write({'state': 'gm',
                       'dm_gm': self.env.user,
                       'dm_date_gm': fields.Date.today(),

                       })
