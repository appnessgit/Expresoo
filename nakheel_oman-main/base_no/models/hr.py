# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class Employee(models.Model):
    _inherit = 'hr.employee'
    
    branch_id = fields.Many2one('res.branch', string="Branch")
    line_manager_id = fields.Many2one('res.users', string="Line Manager")


class Department(models.Model):
    _inherit= "hr.department"

    # Accounting
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    
    manager_id = fields.Many2one('hr.employee', 'Manager')

    # Inventory
    location_id = fields.Many2one('stock.location', string="Consumption Location")