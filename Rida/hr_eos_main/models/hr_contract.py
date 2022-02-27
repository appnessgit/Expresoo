# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from odoo.exceptions import UserError


class Contract(models.Model):
	_inherit= "hr.contract"

	eos_struct_id = fields.Many2one('hr.payroll.structure', required=True,  string='Structure')
	employee_benefits = fields.Boolean(string='Is Gratuity ?')