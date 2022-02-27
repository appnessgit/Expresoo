# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class AccountAssetsCategory(models.Model):
    _name = 'account.assets.category'
    _description = 'Asset Type Categories'
    _parent_name = "parent_id"

    _parent_store = True

    name = fields.Char(string='Asset Category Name', required=True)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('account.assets.category', string="Parent", ondelete='cascade', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    parent_path = fields.Char(index=True)
    children_ids = fields.One2many('account.assets.category', 'parent_id', string="Childrens")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

