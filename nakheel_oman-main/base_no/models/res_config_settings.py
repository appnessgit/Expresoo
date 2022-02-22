# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

# Procurement
    po_committee_limit = fields.Monetary("Need to upload attachment for PO committee approval", default=20000.0, readonly=False, related='company_id.po_committee_limit')
