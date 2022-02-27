from odoo import fields , api , models , _
import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
import math
from odoo.tools import float_round
from odoo.tools.misc import format_date
from calendar import monthrange
import json



class GratuityConfiguration(models.Model):

    _name = 'hr.gratuity.configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Gratuity Configuration"
    _rec_name = "name"


    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)
    gratuity_start_date = fields.Date(string='Start Date', help="Starting date of the gratuity")
    gratuity_end_date = fields.Date(string='End Date', help="Ending date of the gratuity")
    company_id = fields.Many2one('res.company', 'Company', required=True, help="Company",index=True,default=lambda self: self.env.company)
    gratuity_configuration_line = fields.One2many('hr.gratuity.configuration.line','gratuity_configuration_id')

    @api.onchange('gratuity_start_date', 'gratuity_end_date')
    def onchange_date(self):
        """ Function to check date """
        if self.gratuity_start_date and self.gratuity_end_date:
            if not self.gratuity_start_date < self.gratuity_end_date:
                raise UserError(_("Invalid date configuration!"))

    def unlink(self):
        ids = self.env["hr.end.service"].search([("gratuity_id", "=", self.id)])
        if len(ids) > 0:
            raise UserError("You Cannot Delete This Gratuity Configuration has linked with EOS Request .")
        return super(GratuityConfiguration, self).unlink()


    _sql_constraints = [('name_uniq', 'unique(name)',
                     'Gratuity configuration name should be unique!')]




class GratuityConfigurationLine(models.Model):
    _name = 'hr.gratuity.configuration.line'
    _rec_name = 'name'
    _description = "Gratuity Configuration Line"

    name = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, help="Company",index=True,default=lambda self: self.env.company)
    from_year = fields.Float(string="From Year")
    to_year = fields.Float(string="To Year")
    percentage = fields.Float(default=1,string='Percentage(%)')
    gratuity_configuration_id = fields.Many2one('hr.gratuity.configuration', string='')

    @api.onchange('from_year', 'to_year')
    def onchange_year(self):
        """ Function to check year configuration """
        if self.from_year and self.to_year:
            if not self.from_year < self.to_year:
                raise UserError(_("Invalid year configuration!"))
