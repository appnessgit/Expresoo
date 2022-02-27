# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # == Business fields ==
    check_ref = fields.Char('Reference')
    check_no = fields.Char('Check Number')
    check_date = fields.Date('Maturity Date')
    check_journal_id = fields.Many2one('account.journal', 'Clearing Journal',domain=[('type', 'in', ('bank', 'cash')), ('is_check_journal', '!=', True)])
    is_check_journal = fields.Boolean(related='journal_id.is_check_journal',store=True)
    # print("uuuuuuuuuuuuuuuuuuuuu",payment_method_id)

  
   
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _create_payment_vals_from_wizard(self):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals['state'] = 'draft'
        payment_vals['check_ref'] = self.check_ref
        payment_vals['check_no'] = self.check_no
        payment_vals['check_date'] = self.check_date
        payment_vals['check_journal_id'] = self.check_journal_id.id
        print('-------0-0-----------------------',self.payment_method_id.name)
        print('-------0-0-----------------------',payment_vals)
        return payment_vals
