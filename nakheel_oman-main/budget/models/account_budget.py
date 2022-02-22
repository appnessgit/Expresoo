# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, except_orm
import itertools
import psycopg2


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'
    _rec_name = 'display_name'

    months = [
        ('01', "January"),
        ('02', "February"),
        ('03', "March"),
        ('04', "April"),
        ('05', "May"),
        ('06', "June"),
        ('07', "July"),
        ('08', "August"),
        ('09', "September"),
        ('10', "October"),
        ('11', "November"),
        ('12', "December"),
    ]

    year = fields.Char()
    month = fields.Selection(months)
    planned_amount = fields.Monetary("Planned Amount")
    allocated_amount = fields.Monetary("Allocated Amount", compute="_compute_totals")
    remaining_amount = fields.Monetary("Remaining Amount", compute="_compute_totals", store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    department_id = fields.Many2one('hr.department', "Department")
    display_name = fields.Char(compute='compute_display_name')
    type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], default="expense")

    def unlink(self):
        for rec in self:
            if not rec.state == 'draft':
                raise UserError("Sorry! only draft records can be deleted!")

        return super(CrossoveredBudget, self).unlink()

    @api.depends('name', 'department_id')
    def compute_display_name(self):
        for attr in self:
            display_name = attr.name
            if attr.department_id:
                display_name += " - " + attr.department_id.name
            display_name += " (" + str(attr.date_from) + " - " + str(attr.date_to) + ")"
            attr.display_name = display_name

    def action_budget_validate(self):
        self.ensure_one()
        self.write({'state': 'validate'})
        for line in self.crossovered_budget_line:
            line.initial_planned_amount = line.planned_amount

    @api.depends('crossovered_budget_line', 'planned_amount')
    def _compute_totals(self):
        for record in self:
            allocated_amout = sum(line.planned_amount for line in record.crossovered_budget_line)
            remaining_amount = record.planned_amount - allocated_amout
            record.update({
                'allocated_amount': allocated_amout,
                'remaining_amount': remaining_amount
            })

    @api.constrains('planned_amount', 'crossovered_budget_line')
    def _check_budget_exceed(self):

        if self.type == "expense" and self.planned_amount >= 0:
            raise UserError("Expense Budgets Should have negative amounts!")
        elif self.type == "profit" and self.planned_amount <= 0:
            raise UserError("Revenue Budgets Should have positive amounts!")

        if not self.crossovered_budget_line:
            return
        allocated_amout = sum(line.planned_amount for line in self.crossovered_budget_line)

        if self.type == "expense":
            if allocated_amout < self.planned_amount:
                raise UserError("Budget Exceeded")
        else:
            if allocated_amout > self.planned_amount:
                raise UserError("Budget Exceeded! \n Budget lines total should not exceed the budget planned amount.")

    def action_view_amendments(self):
        return {
            'name': "Amendments",
            'type': 'ir.actions.act_window',
            'res_model': 'account.budget.amendment',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'target': 'current',
            'domain': ['|', ('budget_line_from', 'in', self.crossovered_budget_line.ids),
                       ('budget_line_to', 'in', self.crossovered_budget_line.ids)],
        }


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'
    _rec_name = "name"

    name = fields.Char(compute='_compute_line_name', store=True)

    account_id = fields.Many2one('account.account', string="Account", required=True)
    categ_id = fields.Many2one('product.category', "Category")
    remaining_amount = fields.Monetary("Remaining Amount", compute='_compute_remaining_amount')
    department_id = fields.Many2one('hr.department', string="Department", related="crossovered_budget_id.department_id")

    department_line = fields.Boolean("Department Line?", compute="_compute_department_line", store=True)
    allow_over_budget = fields.Boolean("Allow Budget Exceeding")

    type = fields.Selection([('expense', 'Expenses'), ('profit', 'Revenue')], default="expense",
                            related="crossovered_budget_id.type")

    initial_planned_amount = fields.Monetary("Initially Planned Amount")
    planned_amount_date = fields.Monetary("Planned Amount on Date", compute="compute_planned_amount_date")

    @api.depends('initial_planned_amount')
    def compute_planned_amount_date(self):
        self.ensure_one()
        date = fields.Datetime.now()

        if self.env.context.get('practical_date'):
            date = fields.Date.from_string(self.env.context.get('practical_date'))
        amendments = self.env['account.budget.amendment'].search(['|',
                                                                  ('budget_line_from', '=', self.id),
                                                                  ('budget_line_to', '=', self.id),
                                                                  ('date', '<=', date),
                                                                  ])

        add_amendments = amendments.filtered(lambda l: l.budget_line_to.id == self.id)
        substract_amendments = amendments.filtered(lambda l: l.type == 'swap' and l.budget_line_from.id == self.id)

        add_amount = sum(line.amount for line in add_amendments)
        sub_amount = sum(line.amount for line in substract_amendments)

        self.planned_amount_date = self.initial_planned_amount + add_amount - sub_amount

    @api.model
    def create(self, vals):
        vals['initial_planned_amount'] = vals.get('planned_amount')
        return super(CrossoveredBudgetLines, self).create(vals)

    @api.constrains('planned_amount')
    def check_amounts(self):
        if self.type == "expense" and self.planned_amount >= 0:
            raise UserError("Expense Budgets Should have negative amounts! \n "
                            "*Make sure that all the budget lines have negative values!")
        elif self.type == "profit" and self.planned_amount <= 0:
            raise UserError("Revenue Budgets Should have positive amounts! \n *"
                            "Make sure that all the budget lines have positive values!")

    def action_allow_exceeding(self):
        self.ensure_one()
        self.allow_over_budget = True

    def action_stop_exceeding(self):
        self.ensure_one()
        self.allow_over_budget = False

    @api.depends('department_id', 'analytic_account_id')
    def _compute_department_line(self):
        for record in self:
            if not record.department_id.analytic_account_id:
                return
            if record.analytic_account_id == record.department_id.analytic_account_id:
                record.department_line = True

    @api.depends('planned_amount', 'practical_amount')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = abs(record.planned_amount) - abs(record.practical_amount)

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if not self.categ_id:
            return
        if self.categ_id.property_account_expense_categ_id:
            self.account_id = self.categ_id.property_account_expense_categ_id.id

    def _compute_practical_amount(self):
        for line in self:
            date_to = line.date_to
            date_from = line.date_from

            if self.env.context.get('practical_date'):
                date_to = fields.Date.from_string(self.env.context.get('practical_date'))

            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                domain += [('general_account_id', '=', line.account_id.id)]

                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', '=',
                           line.account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ('move_id.state', '=', 'posted'),
                          ]
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                # raise UserError(str(from_clause))
                select = "SELECT sum(account_move_line.credit)-sum(account_move_line.debit) from " + from_clause + " where " + where_clause

            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    @api.constrains('account_id', 'analytic_account_id')
    def _must_have_analytical_or_budgetary_or_both(self):
        for record in self:
            if not record.analytic_account_id and not record.account_id:
                raise UserError(
                    _("You have to enter at least a GL account or analytic account on a budget line."))

    @api.depends("account_id", "general_budget_id", "analytic_account_id")
    def _compute_line_name(self):
        # just in case someone opens the budget line in form view
        for record in self:
            computed_name = record.crossovered_budget_id.name
            if record.account_id:
                computed_name += ' - ' + record.account_id.name
            if record.analytic_account_id:
                computed_name += ' - ' + record.analytic_account_id.name
            if record.categ_id:
                computed_name += ' - ' + record.categ_id.name
            record.name = computed_name

    def action_open_budget_entries(self):
        if self.analytic_account_id:
            # if there is an analytic account, then the analytic items are loaded
            action = self.env['ir.actions.act_window'].for_xml_id('analytic', 'account_analytic_line_action_entries')
            action['domain'] = [('account_id', '=', self.analytic_account_id.id),
                                ('date', '>=', self.date_from),
                                ('date', '<=', self.date_to),
                                ('general_account_id', '=', self.account_id.id)
                                ]

        else:
            # otherwise the journal entries booked on the accounts of the budgetary postition are opened
            action = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_moves_all_a')
            action['domain'] = [('account_id', '=', self.account_id.id),
                                ('date', '>=', self.date_from),
                                ('date', '<=', self.date_to)
                                ]
        return action

    @api.onchange('planned_amount')
    def onchange_planned_amount(self):
        if self.planned_amount > 0.0:
            self.allow_over_budget = True
        else:
            self.allow_over_budget = False

    @api.depends('date_from', 'date_to')
    def _compute_theoritical_amount(self):
        # beware: 'today' variable is mocked in the python tests and thus, its implementation matter
        today = fields.Date.today()
        for line in self:
            if line.paid_date:
                if today <= line.paid_date:
                    theo_amt = 0.00
                else:
                    theo_amt = line.planned_amount
            else:
                if not line.date_from or not line.date_to:
                    line.theoritical_amount = 0
                    continue
                # One day is added since we need to include the start and end date in the computation.
                # For example, between April 1st and April 30th, the timedelta must be 30 days.
                line_timedelta = line.date_to - line.date_from + timedelta(days=1)
                elapsed_timedelta = today - line.date_from + timedelta(days=1)

                if elapsed_timedelta.days < 0:
                    # If the budget line has not started yet, theoretical amount should be zero
                    theo_amt = 0.00
                elif line_timedelta.days > 0 and today < line.date_to:
                    # If today is between the budget line date_from and date_to
                    theo_amt = (
                                           elapsed_timedelta.total_seconds() / line_timedelta.total_seconds()) * line.planned_amount
                else:
                    theo_amt = line.planned_amount
            line.theoritical_amount = theo_amt
