# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Branch(models.Model):
    _name = "res.branch"
    _description = 'Branches'
    _rec_name = 'display_name'
    _order = 'display_name'

    # General Info
    name = fields.Char(string='Branch Name', required=True, store=True, readonly=False)
    display_name = fields.Char("name", compute='_compute_display_name', store=True)
    parent_id = fields.Many2one('res.branch', string='Parent Branch', index=True)
    code = fields.Char()
    child_ids = fields.One2many('res.branch', 'parent_id', string='Child Branches')
    logo = fields.Binary(string="Logo")

    # Contact Details
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one('res.country.state', string="Fed. State")
    email = fields.Char(store=True, readonly=False)
    phone = fields.Char(store=True, readonly=False)

    # Accounting
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    manager_id = fields.Many2one('res.users', 'Branch Manager')
    line_manager_id = fields.Many2one('res.users', 'MR Approver')

    line_manager_temp_id = fields.Many2one('res.users', 'Acting MR Approver')

    @api.onchange('parent_id')
    def onchange_parent(self):
        if self.parent_id.manager_id:
            self.line_manager_id = self.parent_id.manager_id.id

    @api.depends('name', 'parent_id')
    def _compute_display_name(self):
        self.ensure_one()
        display_name = self.name
        if self.parent_id:
            display_name = self.parent_id.display_name + " / " + display_name
        self.display_name = display_name
