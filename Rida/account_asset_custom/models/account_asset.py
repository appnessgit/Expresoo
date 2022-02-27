# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from pickletools import string1
from dateutil.relativedelta import relativedelta
from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    #rida custom fields
    code=fields.Char(string='Asset code',track_visibility='onchange')
    responsile=fields.Many2one('hr.employee' ,track_visibility='onchange')
    asset_location=fields.Many2one('res.city',track_visibility='onchange')
    asset_type_category=fields.Many2one('account.assets.category',track_visibility='onchange')
    reson=fields.Char(string='Asset Tranformation Reson',track_visibility='onchange')

    def action_asset_transfer(self):
        context = {
            'active_model': 'account.asset',
            'active_ids': self.ids,
            'default_olde_responsile': self.responsile.id,
            'default_olde_asset_location': self.asset_location.id,
            'default_olde_account_analytic_id': self.account_analytic_id.id,
        }
        print("connnnnnnntext",context)
        return {
            'name': _('Transfer Asset'),
            'res_model': 'account.asset.transfer.wizard',
            'view_mode': 'form',
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

