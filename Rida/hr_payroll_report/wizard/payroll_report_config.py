# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PayslipReportConfig(models.Model):
    _name = 'payslip.report.config'

    name = fields.Char('Name')
    rule_ids =fields.Many2many("hr.salary.rule")
    paper_format = fields.Selection([("A4","A4"),("A3","A3")], default="A4",compute="compute_paper_format")
    

    def compute_paper_format(self):
        for rec in self:
            if len(self.rule_ids.ids) > 5:
                rec.paper_format = 'A3'
            else:
                rec.paper_format = 'A4'
    
    