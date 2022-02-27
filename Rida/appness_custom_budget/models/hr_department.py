from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError



class Department(models.Model):
    _inherit = 'hr.department'

    cont_budget_only = fields.Boolean(string="Cont. budget only", default=False)
    virtual_dep = fields.Boolean(string="Virtual Dep.", default=False)
    dep_type = fields.Selection(selection=[
            ('department', 'Department'),
            ('section', 'Section'),
            ('business_unit', 'Business Unit'),
        ], string='Type', required=True, readonly=True, copy=False, tracking=True,
        default='department')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    general_budget_id = fields.Many2one('account.budget.post', string="Budgetary Positions")
    section_head = fields.Many2one('hr.employee', string="Section Head")
    rig_manager = fields.Many2one('hr.employee', string="Rig Manager")
    section_parent_id = fields.Many2one('hr.department', string="Section", domain="[('dep_type', '=', 'section')]")

    @api.onchange('section_parent_id')
    def get_section_parent_id(self):
        if self.section_parent_id:
            self.parent_id=self.section_parent_id



    @api.onchange('section_head','rig_manager')
    def get_manager(self):
        if self.section_head:
            self.manager_id = self.section_head.id
        if self.rig_manager:
            self.manager_id = self.rig_manager.id