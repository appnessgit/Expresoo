# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm


class AccountMove(models.Model):
    _name='account.move'
    _inherit = ['account.move','mail.activity.mixin']

    over_budget = fields.Boolean()

    def post(self):
        budget_exceeded = False
        for rec in self:
            # rec.line_ids.check_budget()
            budget_exceeded = False
            updated = False
            for line in rec.line_ids:
                if not updated:
                    budget_exceeded, budget_amount = line.check_budget()
                if budget_exceeded:
                    updated = True

        if budget_exceeded:
            raise UserError("Budget Exceeded! \n %s" % budget_exceeded.name)
        else:
            return super(AccountMove, self).post()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def check_budget(self):
        for rec in self:
            budget = False
            line_amount = budget_remaining = budget_diff = 0.0
            analytic_account_id = rec.analytic_account_id.id if rec.analytic_account_id else False
            budgetItem = self.env['crossovered.budget.lines'].search([
                ('account_id', '=', rec.account_id.id),
                ('analytic_account_id', 'in', [analytic_account_id, False]),
                ('date_from', '<=', rec.date_maturity),
                ('date_to', '>=', rec.date_maturity),
                ('allow_over_budget', '=', False),
                ('crossovered_budget_id.type', '=', 'expense'),
                ('crossovered_budget_id.state', 'in', ('validate', 'done'))
            ], limit=1)

            if budgetItem and not rec.invoice_id:
                line_amount = abs(rec.credit - rec.debit)
                budget_remaining = budgetItem.remaining_amount
                if line_amount > budget_remaining:
                    budget = budgetItem
                    budget_diff = line_amount - budget_remaining
            return budget, budget_diff
