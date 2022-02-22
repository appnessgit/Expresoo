# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class User(models.Model):
    _inherit = 'res.users'

    department_id = fields.Many2one('hr.department', string="Department", compute='get_cost_center')

    def get_cost_center(self):
        for rec in self:
            if not rec.employee_ids:
                return
            employee_id = rec.employee_ids[0]
            rec.update({
                'department_id': employee_id.department_id,
                })

    @api.model
    @tools.ormcache('self._uid', 'group_ext_id')
    def _has_group(self, group_ext_id):
        """Checks whether user belongs to given group.

        :param str group_ext_id: external ID (XML ID) of the group.
           Must be provided in fully-qualified form (``module.ext_id``), as there
           is no implicit module to use..
        :return: True if the current user is a member of the group with the
           given external ID (XML ID), else False.
        """
        if group_ext_id == 'procurement':
            group_ext_id = 'procurement.group_purchase_request_user'

        assert group_ext_id and '.' in group_ext_id, "External ID must be fully qualified"
        module, ext_id = group_ext_id.split('.')
        self._cr.execute("""SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid IN
                                (SELECT res_id FROM ir_model_data WHERE module=%s AND name=%s)""",
                         (self._uid, module, ext_id))
        return bool(self._cr.fetchone())