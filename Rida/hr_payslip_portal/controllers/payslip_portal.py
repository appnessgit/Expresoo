# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.web.controllers.main import Binary
from odoo.tools import float_compare
from pytz import timezone, UTC
import datetime


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

            values['payslip_count'] = request.env['hr.payslip'].search_count([
                ('employee_id', '=', employee_id.id)
            ])
            values['employee_id'] = employee_id
        return values

    def _payslip_get_page_view_values(self, payslip, access_token, **kwargs):
        values = {
            'payslip': payslip,
        }
        return self._get_page_view_values(payslip, access_token, values, 'my_payslip_history', True, **kwargs)

    @http.route(['/my/payslip', '/my/payslip/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payslips(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')
        HrPayslip = request.env['hr.payslip']

        domain = [('employee_id', '=', employee_id.id)]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'date_from desc, id desc'},
            'date_old': {'label': _('Oldest'), 'order': 'date_from asc, id asc'},
            'name': {'label': _('Payslip Name'), 'order': 'name asc, id asc'},
            'number': {'label': _('Reference'), 'order': 'number asc, id asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},

        }
        # default filter by value
        if not filterby:
            filterby = 'done'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        payslip_count = HrPayslip.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/payslip",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=payslip_count,
            page=page,
            step=self._items_per_page
        )
        # search the records to display, according to the pager data
        payslips = HrPayslip.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_payslip_history'] = payslips.ids[:100]

        values.update({
            'date': date_begin,
            'payslips': payslips,
            'page_name': 'payslip',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employee_id': employee_id,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/payslip',
        })
        return request.render("hr_payslip_portal.portal_my_payslips", values)


    @http.route(['/my/payslip/<int:payslip_id>'], type='http', auth="public", website=True)
    def portal_my_payslip(self, payslip_id, access_token=None, report_type=None, download=False, **kw):
        try:
            payslip_sudo = self._document_check_access('hr.payslip', payslip_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=payslip_sudo, report_type=report_type, report_ref='hr_payroll.action_report_payslip',
                                     download=download)

        values = self._payslip_get_page_view_values(payslip_sudo, access_token, **kw)
        return request.render("hr_payslip_portal.portal_my_payslip", values)
