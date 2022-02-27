# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class GenerateBudgetDepatrmentForm(models.TransientModel):
    _name = 'budget.department.form.wizard'
    _description = "Generate Budget Department Form Wizard"

    department_ids = fields.Many2many('hr.department', string="Departments",
                                      default=lambda self: self.env['hr.department'].search(
                                          [('analytic_account_id', '!=', False), ('dep_type', '=', 'section')]))
    business_unit_ids = fields.Many2many('hr.department', 'sec_bu_rel', 'sec_id', 'bu_id', string="Departments",
                                         default=lambda self: self.env['hr.department'].search(
                                             [('section_parent_id', '!=', False), ('virtual_dep', '!=', False)]))
    budgetary_position_ids = fields.Many2many('account.budget.post', string="Budgetary Position",
                                              default=lambda self: self.env['account.budget.post'].search(
                                                  [('department_ids', '!=', False)]))

    def quarter_start_end(self, quarter, year=None):
        """
		Returns datetime.daet object for the start
		and end dates of `quarter` for the input `year`
		If `year` is none, it defaults to the model start_from date
		year.
		"""

        context = dict(self._context or {})
        active_model = self.env.context.get('active_model')
        active_id = self.env.context['active_ids']

        budget = self.env[active_model].browse(active_id)

        if year is None:
            # year = dt.datetime.now().year
            year = budget.date_from.year
        # d = dt.date(year, 1+3*(quarter-1), 1)
        # return d, d+relativedelta(months=3, days=-1)
        d = dt.date(year, 1 + 1 * (quarter - 1), 1)
        return d, d + relativedelta(months=1, days=-1)

    #		line to be created must have a Business unit & budgetary position having this
    # 		business unit inside & have a section as a perant ,this section must have analtyic account(cost center)
    # 		this business unit should be Virtual type as customized

    def action_confirm(self):
        context = dict(self._context or {})
        active_model = self.env.context.get('active_model')
        active_id = self.env.context['active_ids']

        budget = self.env[active_model].browse(active_id)
        duration = relativedelta(budget.date_to, budget.date_from).months

        # raise UserError(duration.months)

        budget_department_form = self.env['account.budget.department.form']
        business_unit_ids = self.env['hr.department'].search(
            [('section_parent_id', 'in', self.department_ids.ids), ('virtual_dep', '!=', False)])
        quarters = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        section_ids = self.env['hr.department'].search([('id', 'in', self.business_unit_ids.section_parent_id.ids)])

        for bu in business_unit_ids:
            budget_department_form_lines = []
            vals = {
                'name': budget.name + ": " + bu.name,
                'budget_id': budget.id,
                'department_id': bu.section_parent_id.id,
                'analytic_account_id': bu.analytic_account_id and bu.analytic_account_id.id,
            }

            # raise UserError(bu.id)
            for bp in self.budgetary_position_ids:

                if bu.id not in bp.department_ids.ids:
                    pass
                else:
                    # raise UserError(bp.department_ids.ids)
                    if bp.budgetary_position_type == budget.type or bp.budgetary_position_type == budget.expense_type:
                        # if bu.id in bp.department_ids.ids and bu.section_parent_id.id == sec.id:
                        # for quarter in quarters:
                        x = int(dt.datetime.strptime(str(budget.date_from), '%Y-%m-%d').strftime('%m'))

                        for y in range(duration):
                            date_start, date_end = self.quarter_start_end(x)
                            line = {
                                'analytic_account_id': bu.analytic_account_id and bu.analytic_account_id.id,
                                'general_budget_id': bp.id,
                                'date_from': date_start,
                                'date_to': date_end,
                                'business_unit_id': bu.id,
                            }
                            budget_department_form_lines.append((0, 0, line))
                            x += 1
            # raise UserError(budget_department_form_lines)
            vals['line_ids'] = budget_department_form_lines
            self.env['account.budget.department.form'].sudo().create(vals)

            # budgetary_position_ids = self.env['account.budget.post'].search([('department_ids', 'in', business_unit_ids.ids)])
            # if not budgetary_position_ids:
            # 	continue
            # for bp in budgetary_position_ids:
            # 	for bu in business_unit_ids:
            # 		if bp.budgetary_position_type == budget.type or bp.budgetary_position_type == budget.expense_type:
            # 			if bu.id in bp.department_ids.ids and bu.section_parent_id.id == bu.section_parent_id.id:
            # 				for quarter in quarters:
            # 					date_start, date_end = self.quarter_start_end(quarter)
            # 					line = {
            # 						'analytic_account_id': bu.analytic_account_id and bu.analytic_account_id.id,
            # 						'general_budget_id': bp.id,
            # 						'date_from': date_start,
            # 						'date_to': date_end,
            # 						'business_unit_id':bu.id,
            # 					}
            # 					budget_department_form_lines.append((0,0, line))
            # 	vals['line_ids'] = budget_department_form_lines
            # self.env['account.budget.department.form'].sudo().create(vals)

        budget.write({
            'state': 'department',
        })
