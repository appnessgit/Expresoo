from odoo import fields, models, api


class Settings(models.TransientModel):
	_inherit = 'res.config.settings'

	amount_limit = fields.Monetary("Limit of Requested Amount")

	def set_values(self):
		res = super(Settings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('budget.amount_limit', self.amount_limit)
		return res
		
	@api.model
	def get_values(self):
		res = super(Settings, self).get_values()
		res.update(
			amount_limit=self.env['ir.config_parameter'].sudo().get_param('budget.amount_limit')
		)
		return res

	