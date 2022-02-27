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

	def unlink(self):
		for rec in self:
			if rec.resign_id:
				rec.resign_id.eos_count = 0
			else:
				pass
		return super(hr_end_service, self).unlink()