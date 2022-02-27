# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountAssetTransferWizard(models.TransientModel):
    _name = 'account.asset.transfer.wizard'
    _description = 'create asset wizard'

    # == Business fields ==
    
    olde_responsile=fields.Many2one('hr.employee', string='Olde Responsiple')
    olde_asset_location=fields.Many2one('res.city' , string='Olde Asset Location')
    olde_account_analytic_id=fields.Many2one('account.analytic.account' , string='Olde Analytic Account')
    
    
    new_responsile=fields.Many2one('hr.employee' , string='New Responsiple')
    new_asset_location=fields.Many2one('res.city', string='New City')  
    new_account_analytic_id=fields.Many2one('account.analytic.account' , string='New Analytic Account')
    reson=fields.Char(string='Asset Tranformation Reson')

    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def asset_transfer(self):
        # OVERRIDE
        print("plaaaaaaaaaaaaaaaaaaaaaplaaaaaaaaaaaaa")
        asset = self.env['account.asset'].browse(self.env.context.get('active_ids'))
        asset.write({'responsile': self.new_responsile.id,
                     'asset_location': self.new_asset_location.id,
                     'account_analytic_id': self.new_account_analytic_id.id,
                     'reson': self.reson,})
        # return asset.update(responsile=self.new_responsile.id)

        