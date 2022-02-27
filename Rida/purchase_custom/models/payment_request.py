from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime

class PaymentRequest(models.Model):
    _name = 'payment.request'
    _inherit = 'mail.thread'
    _description = 'Payment request details'
    
    
    name = fields.Char('Payment Request', required=True, index=True, copy=False, default='New')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Contracter', track_visibility='onchange')
    contract_number = fields.Many2one(comodel_name='contract.contract',string='Contract Reference')
    date = fields.Date(string='Date')
    type_of_change = fields.Selection(string='Type of change', selection=[('change_order', 'Change Order'), 
                                                                          ('amendment', 'Amendment'),
                                                                          ('extension', 'Extension'),
                                                                          ('renewal ', 'Renewal')])
    
    # portion_of_agreement_affected = fields.Text(string='Portion of agreement affected')
    reason_for_change = fields.Binary(string='Reason for change',track_visibility='onchange')
    contract_ids = fields.One2many(comodel_name='contract.lines', inverse_name='contract_id')
    inherit_po = fields.Many2one(comodel_name='purchase.order')
    state = fields.Selection(string="Status", selection=[('user_department', 'User Department'), 
                                                         ('procurement_manger', 'Procurement manager'),
                                                         ('buyer', 'Buyer'),
                                                         ('managing_director', 'Managing Director'),
                                                         ('changed', 'Changed'),
                                                         ('reject', 'Rejected'),], default='user_department', track_visibility='onchange')
        
    total = fields.Monetary(string='Total', 
    # compute='compute_totals'
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id, )
    contract_duration = fields.Char(string='Contract Duration',)
    start_date = fields.Date(string='Start Date', track_visibility='onchange')
    end_date = fields.Date(string='End Date', track_visibility='onchange')
    description = fields.Text(string='Descriprtion of services')
    terms_note = fields.Text(string='Terms notes')
    # contract_type = fields.Selection(string='Contract Type', selection=[('minor', 'Minor'), 
    #                                                                     ('service_order', 'Service Order'),
    #                                                                     ('service_agreement','Service Agreement')])
    # # scope_of_work = fields.Text(string='Scope of work',track_visibility='onchange')
    terms_and_conditions = fields.Binary(string='Terms and conditions', )
    # buyer = fields.Many2one(comodel_name='res.users', string='Assign buyer', track_visibility='onchange')
    
    this_claim = fields.Float(string='This clame')
    address = fields.Char(string='Address')
    fax_number = fields.Integer(string='Fax number')
    telephone_number = fields.Char(string='Telephone No.')
    email = fields.Char(string='Email')


    # @api.depends('contract_ids.unit_price')
    # def compute_totals(self):
    #     self.ensure_one()
    #     totals = purchase_total = 0.0
    #     for line in self.contract_ids:
    #         totals += line.unit_price * line.quantity
    #     self.update({'total': totals, })
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('payment.request.sequence') or _('New')
        result = super(PaymentRequest, self).create(vals)
        return result    
        
    @api.onchange('contract_number')
    def onchange_contract_number(self):
        if self.contract_number:
            self.vendor_id=self.contract_number.vendor_id
            # self.buyer=self.contract_number.buyer
            # self.description=self.contract_number.description
            self.address=self.contract_number.address
            self.telephone_number=self.contract_number.telephone_number
            self.fax_number=self.contract_number.fax_number
            self.email=self.contract_number.email
        