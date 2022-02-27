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
from odoo.exceptions import UserError


class CustomerPortal(CustomerPortal):

    SALARY_ADVANCE_MANDATORY_BILLING_FIELDS = ["advance", "date", "reason"]

    SALARY_ADVANCE_OPTIONAL_BILLING_FIELDS = []

    def salary_advance_details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.SALARY_ADVANCE_MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.SALARY_ADVANCE_MANDATORY_BILLING_FIELDS + self.SALARY_ADVANCE_OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

            values['salary_advance_count'] = request.env['salary.advance'].search_count([
                ('employee_id', '=', employee_id.id)
            ])
            values['employee_id'] = employee_id
        return values

    def _salary_advance_get_page_view_values(self, salary_advance, access_token, **kwargs):

        values = {
            'salary_advance': salary_advance,
        }
        return self._get_page_view_values(salary_advance, access_token, values, 'my_salary_advance_history', True, **kwargs)

    @http.route(['/my/salary_advance', '/my/salary_advance/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_salary_advances(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')

        Hrsalary_advance = request.env['salary.advance']

        domain = [('employee_id', '=', employee_id.id)]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'date desc, id desc'},
            'date_old': {'label': _('Oldest'), 'order': 'date asc, id asc'},
            'name': {'label': _('Description'), 'order': 'name asc, id asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        salary_advance_count = Hrsalary_advance.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/salary_advance",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=salary_advance_count,
            page=page,
            step=self._items_per_page
        )
        # search the records to display, according to the pager data
        salary_advances = Hrsalary_advance.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_salary_advance_history'] = salary_advances.ids[:100]

        values.update({
            'date': date_begin,
            'salary_advances': salary_advances,
            'page_name': 'salary_advance',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employee_id': employee_id,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/salary_advance',
        })

        return request.render("hr_salary_advance_portal.portal_my_salary_advances", values)

    @http.route(['/my/salary_advance/<int:salary_advance_id>'], type='http', auth="public", website=True)
    def portal_my_salary_advance(self, salary_advance_id=None, access_token=None, **kw):
        try:
            salary_advance_sudo = self._document_check_access('salary.advance', salary_advance_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._salary_advance_get_page_view_values(salary_advance_sudo, access_token, **kw)
        return request.render("hr_salary_advance_portal.portal_my_salary_advance", values)

    @http.route(['/my/salary_advance/edit'], type='http', auth="public", website=True)
    def update_salary_advance(self, redirect=None, **post):
        attachment = False

        salary_advance_id = False
        if post.get('id'):
            salary_advance_id = int(post.get('id'))
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

        values.update({
            'error': {},
            'error_message': [],
        })


        Hrsalary_advance = request.env['salary.advance']


        salary_advance = False
        if salary_advance_id:
            salary_advance = request.env['salary.advance'].browse(salary_advance_id)
        attachment = post.get('attachment', False)
        post.pop('attachment', None)
        post.pop('id', None)

        if post:
            error, error_message = self.salary_advance_details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            if error:
                values.update({
                    'employee_id': employee_id,
                    'salary_advance': salary_advance,
                    'redirect': redirect,
                    'page_name': 'salary_advance',
                    'error_message': error_message,
                    'salary_advance_name': '/',
                })

                response = request.render("hr_salary_advance_portal.edit_salary_advance_details", values)
                response.headers['X-Frame-Options'] = 'DENY'
                return response

            values = {key: post[key] for key in self.SALARY_ADVANCE_MANDATORY_BILLING_FIELDS}
            values.update({key: post[key] for key in self.SALARY_ADVANCE_OPTIONAL_BILLING_FIELDS if key in post})


            values.update(
                {
                    'employee_id': employee_id.id,
                })


            if not salary_advance_id:
                salary_advance = Hrsalary_advance.create(values)


                salary_advance.sudo().action_submit()

            else:
                salary_advance.update(values)

            if redirect:
                return request.redirect(redirect)
            return request.redirect('/my/salary_advance')

        values.update({
            'employee_id': employee_id,
            'salary_advance': salary_advance,
            'redirect': redirect,
            'page_name': 'salary_advance',
            'salary_advance_name': '/',
        })

        response = request.render("hr_salary_advance_portal.edit_salary_advance_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
