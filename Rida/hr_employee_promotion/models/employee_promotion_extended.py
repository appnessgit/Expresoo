from odoo import _, api, fields, models


class employee_promotion_extended(models.Model):
    _inherit = 'employee.promotion'


    qualifications = fields.Text(string='Qualifications')
    experience = fields.Text(string='Experience')
    competencies = fields.Text(string='Competencies')
    promotion_document = fields.Binary(string= 'Promotion Document', required=True)

