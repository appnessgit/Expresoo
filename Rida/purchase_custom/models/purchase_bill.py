from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime



    
class InheritAccountMove(models.Model):
    _inherit = 'account.move'


    # def _get_invoices_partials(self):
    #     # self.ensure_one()
    #     for rec in self:
    #         val=rec.line_ids.matched_debit_ids.credit_amount_currency
    #         print("tttttttttttttttttt",val)

    wo_account_id = fields.Many2one('external.service.management')
    original_contract_sum = fields.Monetary(string='Original contract sum')
    address = fields.Char(string='Address')
    fax_number = fields.Integer(string='Fax number')
    telephone_number = fields.Char(string='Telephone No')
    email = fields.Char(string='Email')
    this_claim = fields.Float(string='This clame')
    #rida custom fields
    # amount=fields.Text(compute="_get_invoices_partials")
    # receipt_no
    # request_date
    # payments_amountfields.Monetary(string='Original contract sum')
    # payment_currency = fields.Many2one('res.currency',)  
    # currency_rate = fields.Float(compute='_get_default_currency_rate' , readonly=False, store='True' )
    # currency_rate = fields.Float(compute='_get_default_currency_rate' , readonly=False )
    curr_rate = fields.Float(string='Currency Rate',compute='_get_default_currency_rate')
    contract_state=fields.Selection(string='Contract State' ,selection=[('pending', 'Pending'),  ('approve', 'Approve'),('reject_then_approve', 'Reject Then Approve'),('reject', 'Reject')],default='pending', tracking=True)
    # state=fields.Selection(selection_add=[
    #     ('store_supervisor', 'Store Supervisor'),('store_manager', 'Store Manager'),('site_manager', 'Site Manager'),
    # ], ondelete={'store_supervisor': 'set default', 'store_manager': 'set default', 'site_manager': 'set default',
    #     }, )

    # remark
    # payment_status
    # payment_dates
    # actual_payment_amounts
    risk_cost = fields.Monetary(string='Risk cost')


    @api.model
    def _get_default_currency_rate(self):
        rate=self.env['res.currency.rate'].search([('id','=',self.currency_id.id)], limit=1).rate
        c_rate=rate
        self.curr_rate=c_rate


   




class InheritPurchaseOrderLogistic(models.Model):
    _inherit = 'purchase.order'

    contract_duration = fields.Char(string='Contract Duration')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    request_service_id = fields.Many2one('service.request')

