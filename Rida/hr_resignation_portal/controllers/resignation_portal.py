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

    RESIGNATION_MANDATORY_BILLING_FIELDS = ["request_date", "expected_revealing_date", "resignation_type", "reason"]

    RESIGNATION_OPTIONAL_BILLING_FIELDS = []

    def resignation_details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.RESIGNATION_MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.RESIGNATION_MANDATORY_BILLING_FIELDS + self.RESIGNATION_OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

            values['resignation_count'] = request.env['hr.resignation'].search_count([
                ('employee_id', '=', employee_id.id)
            ])
            values['employee_id'] = employee_id
        return values

    def _resignation_get_page_view_values(self, resignation, access_token, **kwargs):

        values = {
            'resignation': resignation,
        }
        return self._get_page_view_values(resignation, access_token, values, 'my_resignation_history', True, **kwargs)

    @http.route(['/my/resignation', '/my/resignation/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_resignations(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')

        Hrresignation = request.env['hr.resignation']

        domain = [('employee_id', '=', employee_id.id)]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'request_date desc, id desc'},
            'date_old': {'label': _('Oldest'), 'order': 'request_date asc, id asc'},
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
        resignation_count = Hrresignation.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/resignation",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=resignation_count,
            page=page,
            step=self._items_per_page
        )
        # search the records to display, according to the pager data
        resignations = Hrresignation.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_resignation_history'] = resignations.ids[:100]

        values.update({
            'date': date_begin,
            'resignations': resignations,
            'page_name': 'resignation',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employee_id': employee_id,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/resignation',
        })

        return request.render("hr_resignation_portal.portal_my_resignations", values)

    @http.route(['/my/resignation/<int:resignation_id>'], type='http', auth="public", website=True)
    def portal_my_resignation(self, resignation_id=None, access_token=None, **kw):
        try:
            resignation_sudo = self._document_check_access('hr.resignation', resignation_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._resignation_get_page_view_values(resignation_sudo, access_token, **kw)
        return request.render("hr_resignation_portal.portal_my_resignation", values)

    @http.route(['/my/resignation/edit'], type='http', auth="public", website=True)
    def update_resignation(self, redirect=None, **post):
        attachment = False

        resignation_id = False
        if post.get('id'):
            resignation_id = int(post.get('id'))
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

        values.update({
            'error': {},
            'error_message': [],
        })


        Hrresignation = request.env['hr.resignation']


        resignation = False
        if resignation_id:
            resignation = request.env['hr.resignation'].browse(resignation_id)
        attachment = post.get('attachment', False)
        post.pop('attachment', None)
        post.pop('id', None)

        if post:
            error, error_message = self.resignation_details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            if error:
                values.update({
                    'employee_id': employee_id,
                    'resignation': resignation,
                    'redirect': redirect,
                    'page_name': 'resignation',
                    'error_message': error_message,
                    'resignation_name': '/',
                })

                response = request.render("hr_resignation_portal.edit_resignation_details", values)
                response.headers['X-Frame-Options'] = 'DENY'
                return response

            values = {key: post[key] for key in self.RESIGNATION_MANDATORY_BILLING_FIELDS}
            values.update({key: post[key] for key in self.RESIGNATION_OPTIONAL_BILLING_FIELDS if key in post})


            values.update(
                {
                    'employee_id': employee_id.id,
                })


            if not resignation_id:
                resignation = Hrresignation.create(values)


                resignation.sudo().submit_resignation()

            else:
                resignation.update(values)

            if redirect:
                return request.redirect(redirect)
            return request.redirect('/my/resignation')

        values.update({
            'employee_id': employee_id,
            'resignation': resignation,
            'redirect': redirect,
            'page_name': 'resignation',
            'resignation_name': '/',
        })

        response = request.render("hr_resignation_portal.edit_resignation_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
