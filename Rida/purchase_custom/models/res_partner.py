# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'
    
    state = fields.Selection([('draft', 'Draft'),
                              ('register', 'Registration'),
                              ('approved', 'Approved'),
                              # ('reject', 'Rejected'),
     ],string="Status", default='draft', readonly=True, track_visibility='onchange')

    price = fields.Integer(string='Price', default=False,)
    delivery_reliability = fields.Boolean(string='Delivery reliability', default=False,)
    delivery_date_adherence = fields.Boolean(string='Delivery Date Adherence', default=False,)
    item_quality = fields.Boolean(string='Item Quality', default=False,)
    pyment_terms = fields.Boolean(string='Payment Terms', default=False,)
    shipment_place = fields.Boolean(string='Shipment Place', default=False,)
    # Approve
    def action_approve(self):
        self.write({'state': 'approved'})
    #
    # # Reject
    # def action_reject(self):
    #     self.write({'state': 'reject'})
    #
    # # Set to Draft
    # def action_draft(self):
    #     self.write({'state': 'draft'})

    @api.model
    def create(self, values):
        partner = super(Partner, self).create(values)
        # if not values.get('is_account'):
        partner.state = 'register'
        return partner

