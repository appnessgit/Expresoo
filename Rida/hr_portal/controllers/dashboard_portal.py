# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.web.controllers.main import Binary
from odoo.tools import float_compare
from pytz import timezone, UTC
import datetime


class CustomerPortal(CustomerPortal):

    def _dashboard_get_page_view_values(self, employee, access_token, **kwargs):
        values = {
            'employee': employee,
        }
        return self._get_page_view_values(payslip, access_token, values, 'my_dashboard_history', True, **kwargs)

    @http.route(['/my/dashboard'], type='http', auth="user", website=True)
    def portal_my_dashboard(self,  **kw):
        values = {}
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')

        values.update({
            'employee_id': employee_id.sudo(),
            'default_url': '/my/dashboard',
            'page_name': 'dashboard',
        })
        return request.render("hr_portal.portal_my_dashboard", values)
