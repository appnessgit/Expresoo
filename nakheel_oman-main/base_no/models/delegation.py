# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Delegation(models.Model):
    _name = "hr.designation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Delegation"
    _rec_name = "display_name"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Access Granted'),
        ('revoked', 'Access Revoked'),
    ], string='Status', required=True, default='draft', track_visibility='onchange')

    display_name = fields.Char(compute='compute_display_name', string="Name", store=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.get_employee(), track_visibility='always')
    employee_grant_id = fields.Many2one('hr.employee', string="Designated Employee", required=True, track_visibility='always')
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today(), track_visibility='always')
    date_to = fields.Date(string='End Date', required=True, track_visibility='always')

    groups_id = fields.Many2many('res.groups')

    @api.depends('employee_id')
    def compute_display_name(self):
        for rec in self:
            display_name = ""
            if rec.employee_id and rec.employee_grant_id:
                display_name = str(rec.employee_id.name) + " -> " + str(rec.employee_grant_id.name)
            rec.display_name = display_name

    def get_employee(self):
        employee_ids = self.env.user.employee_ids
        if employee_ids:
            return employee_ids[0].id
        raise UserError('Current user is not linked to an employee!')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for rec in self:
            if not rec.employee_id:
                return
            user_id = rec.employee_id.user_id
            groups = user_id.groups_id.ids
            rec.update({
                'groups_id': [(6, 0, groups)]
            })

    @api.onchange('employee_grant_id')
    def onchange_employee_grant_id(self):
        for rec in self:
            if not rec.employee_grant_id or not rec.employee_id:
                return
            user_id = rec.employee_id.user_id
            all_groups = user_id.groups_id.ids
            grant_employee_groups = rec.employee_grant_id.user_id.groups_id.ids
            shared_groups = [value for value in all_groups if value in grant_employee_groups]

            new_groups = list(set(all_groups) - set(shared_groups))

            rec.update({
                'groups_id': [(6, 0, new_groups)]
            })

            return {
                'domain': {'groups_id': [('id', 'in', new_groups)]}
            }

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError("End date should be after start date!")

            domain = [
                ('date_from', '<=', rec.date_to),
                ('date_to', '>', rec.date_from),
                ('employee_grant_id', '=', rec.employee_grant_id.id),
                ('state', 'not in', ['revoked']),
                ('id', '!=', rec.id)
            ]

            ndelegations = rec.search_count(domain)

            if ndelegations:
                raise UserError(
                    _('You can not have 2 delegations that overlaps on the same day for the same employee.'))

    @api.constrains('employee_id', 'employee_grant_id')
    def check_users(self):
        for rec in self:
            if not rec.employee_id.user_id or not rec.employee_grant_id.user_id:
                raise UserError('One of the selected employees is not linked to a user.'
                                ' \n Please contact system administrator.')
            if rec.employee_id == rec.employee_grant_id:
                raise UserError('Please choose a different employee!')

    def action_confirm(self):
        for rec in self:
            today = fields.Date.today()
            if not rec.groups_id:
                raise UserError(_("No access to grant!"))
            if today > rec.date_to:
                raise UserError(_("End date cannot be in the past"))
            # Grant New Groups
            rec.sudo().employee_grant_id.user_id.update({
                'groups_id': [(4, group) for group in rec.groups_id.ids]
            })
            rec.state = 'confirm'

    def action_cancel(self):
        for rec in self:
            # revoke access
            to_remove = [group for group in rec.groups_id.ids]
            groups = rec.sudo().employee_grant_id.user_id.groups_id.ids
            new_groups = list(set(groups) - set(to_remove))
            new_groups = self.env['res.groups'].search([('id', 'in', new_groups)])
            rec.sudo().employee_grant_id.user_id.groups_id = new_groups

            rec.state = 'revoked'

    def action_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if not rec.state == 'draft':
                raise UserError("Only draft records can be deleted!")
        super(Delegation, self).unlink()

    @api.model
    def _cron_update_delegations(self):
        today = fields.Date.today()
        delegations = self.search(['|', '&', ('date_from', '<=', today), ('date_to', '<=', today), ('state', '!=', 'revoked')])

        to_grant = delegations.filtered(lambda d: d.state == 'draft' and d.date_from == today)
        to_revoke = delegations.filtered(lambda d: d.state == 'confirm' and d.date_to == today)

        to_grant.action_confirm()
        to_revoke.action_cancel()

        return True
