# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Payslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread', 'mail.activity.mixin']

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Payslip - %s' % self.name
