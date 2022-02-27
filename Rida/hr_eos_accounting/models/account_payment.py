from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError



class Payment(models.Model):
    _inherit = "account.payment"

    eos_payment_id = fields.Many2one('account.direct.payment')