# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class JobBand(models.Model):
    _name='job.band'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Job Band'
    

    name = fields.Char(string='Band Name' ,required=True )
    Sequence = fields.Integer(string='Sequence',required=True)

    

class JobBandEmployee(models.Model):
    _inherit = 'hr.employee'

    band_id = fields.Many2one(comodel_name='job.band', string='Job Band')
    

    
class JobBandPromotion(models.Model):
    _inherit = 'hr.employee'

    band_id = fields.Many2one(comodel_name='job.band', string='Job Band')