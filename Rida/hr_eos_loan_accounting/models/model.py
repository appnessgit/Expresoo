from odoo import fields , api , models , _
import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm, Warning, RedirectWarning, UserError
import math
from odoo.tools import float_round
from odoo.tools.misc import format_date
from calendar import monthrange
import json



class hr_end_service(models.Model):
	_inherit = 'hr.end.service'

	loan_acc = fields.Many2one('account.account', string='Loan Account')
	


		