# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict, namedtuple

from odoo import http, fields
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.web.controllers.main import Binary
from odoo.tools import float_compare
from pytz import timezone, UTC
import datetime
from datetime import datetime as dt
from odoo.exceptions import UserError, ValidationError
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
import json
import math


DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period')

class CustomerPortal(CustomerPortal):
    LEAVE_MANDATORY_BILLING_FIELDS = ["holiday_status_id", "request_date_from", "request_date_to"]

    LEAVE_OPTIONAL_BILLING_FIELDS = ["name"]

    def leave_details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.LEAVE_MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.LEAVE_MANDATORY_BILLING_FIELDS + self.LEAVE_OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

            values['leave_count'] = request.env['hr.leave'].search_count([
                ('employee_id', '=', employee_id.id)
            ])
            values['employee_id'] = employee_id
        return values

    def _leave_get_page_view_values(self, leave, access_token, **kwargs):
        values = {
            'leave': leave,
        }
        return self._get_page_view_values(leave, access_token, values, 'my_leave_history', True, **kwargs)

    @http.route(['/my/leave', '/my/leave/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_leaves(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')
        leave_types = request.env['hr.leave.type'].with_context(employee_id=employee_id.id).search([('valid', '=', True)])
        HrLeave = request.env['hr.leave']

        domain = []

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('employee_id', '=', employee_id.id)]},
            'approve': {'label': _('Approved'), 'domain': [('employee_id', '=', employee_id.id), ('state', '=', 'validate')]},
            'refuse': {'label': _('Refused'), 'domain': [('employee_id', '=', employee_id.id), ('state', '=', 'refuse')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        leave_count = HrLeave.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/leave",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=leave_count,
            page=page,
            step=self._items_per_page
        )
        # search the records to display, according to the pager data
        leaves = HrLeave.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_leave_history'] = leaves.ids[:100]
        # with_context(employee_id=employee_id.id)
        leave_types = request.env['hr.leave.type'].with_context(employee_id=employee_id.id).search(
            [('valid', '=', True)])
        types = []
        for type in leave_types.filtered(lambda type: type.allocation_type in ['fixed', 'fixed_allocation']):
            vals = {
                'id': type.id,
                'name': type.name,
                'max_leaves': int(type.with_context(employee_id=employee_id.id).max_leaves),
                'remaining_leaves': int(type.with_context(employee_id=employee_id.id).remaining_leaves),
                'leaves_taken': int(type.with_context(employee_id=employee_id.id).leaves_taken),
            }

            types.append(vals)
        values.update({
            'date': date_begin,
            'leaves': leaves,
            'page_name': 'leave',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employee_id': employee_id,
            'types': leave_types,
            'type_allocations': types,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/leave',
        })
        return request.render("hr_holidays_portal.portal_my_leaves", values)

    @http.route(['/my/leave/<int:leave_id>'], type='http', auth="public", website=True)
    def portal_my_leave(self, leave_id=None, access_token=None, **kw):
        try:
            leave_sudo = self._document_check_access('hr.leave', leave_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._leave_get_page_view_values(leave_sudo, access_token, **kw)
        return request.render("hr_holidays_portal.portal_my_leave", values)

    def _check_date(self, employee_id, date_from, date_to, leave=False):

        domain = [
            ('date_from', '<=', date_to),
            ('date_to', '>', date_from),
            ('employee_id', '=', employee_id.id),
            ('state', 'not in', ['cancel', 'refuse']),
        ]
        if leave:
            domain += [('id', '!=', leave.id)]
        nholidays = request.env['hr.leave'].search_count(domain)
        error = False
        if nholidays:
            error = 'You can not have 2 leaves that overlaps on the same day.'
        return error

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        date_from = fields.Datetime.from_string(date_from)
        date_to = fields.Datetime.from_string(date_to)

        time_delta = date_to - date_from
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    def _check_holidays(self, employee_id, holiday_status_id, days):
        error = False

        if holiday_status_id.allocation_type == 'no':
            return False
        leave_days = holiday_status_id.get_days(employee_id.id)[holiday_status_id.id]

        if float_compare(leave_days['remaining_leaves'], days, precision_digits=2) == -1 or float_compare(
                leave_days['virtual_remaining_leaves'], days, precision_digits=2) == -1:
            error = _('The number of remaining time off is not sufficient for this time off type.\n Please also check the time off waiting for validation.')
        return error

    def _check_leave_type_validity(self, holiday_status_id, date_from, date_to):
        error = False

        holiday_status_id = request.env['hr.leave.type'].browse(holiday_status_id)
        dfrom = fields.Datetime.from_string(date_from)
        dto = fields.Datetime.from_string(date_to)
        if date_from > date_to:
            error = ("The start date must be anterior to the end date.")
            return error
        if holiday_status_id.validity_start or holiday_status_id.validity_stop:

            vstart = holiday_status_id.validity_start
            vstop = holiday_status_id.validity_stop

            if holiday_status_id.validity_start and holiday_status_id.validity_stop and (dfrom.date() < vstart or dto.date() > vstop):
                error = (
                        _('You can take %s only between %s and %s') % (
                    holiday_status_id.display_name, holiday_status_id.validity_start,
                    holiday_status_id.validity_stop))

            elif holiday_status_id.validity_start:
                if dfrom and (dfrom.date() < vstart):
                    error = (
                        _('You can take %s from %s') % (
                            holiday_status_id.display_name, holiday_status_id.validity_start))
            elif holiday_status_id.validity_stop:
                if dto and (dto.date() > vstop):
                    error = (
                        _('You can take %s until %s') % (
                            holiday_status_id.display_name, holiday_status_id.validity_stop))
        return error

    @http.route(['/my/leave/edit'], type='http', auth="public", website=True)
    def update_leave(self, redirect=None, **post):

        leave_id = False
        if post.get('id'):
            leave_id = int(post.get('id'))
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

        values.update({
            'error': {},
            'error_message': [],
        })

        leave_types = request.env['hr.leave.type'].with_context(employee_id=employee_id.id).search(
            [('valid', '=', True)])

        types = []
        for type in leave_types:
            vals = {
                'id': type.id,
                'name': type.with_context(employee_id=employee_id.id).display_name,
            }

            types.append(vals)

        leave_types = types

        HrLeave = request.env['hr.leave']

        leave = False
        if leave_id:
            leave = request.env['hr.leave'].browse(leave_id)
        post.pop('id', None)

        if post:
            error, error_message = self.leave_details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            values = {key: post[key] for key in self.LEAVE_MANDATORY_BILLING_FIELDS}
            values.update({key: post[key] for key in self.LEAVE_OPTIONAL_BILLING_FIELDS if key in post})

            values.update(
                {
                    'employee_id': employee_id.id,
                    'holiday_status_id': int(values.get('holiday_status_id')),
                })

            leave_type = request.env['hr.leave.type'].browse(int(values.get('holiday_status_id')))

            err = self._check_date(employee_id, values.get('request_date_from'), values.get('request_date_to'), leave)
            if err:
                error_message.append(err)
            days = self._get_number_of_days(values.get('request_date_from'), values.get('request_date_to'),
                                            employee_id)

            err = self._check_holidays(employee_id, leave_type, days)
            if err:
                error_message.append(err)

            err = self._check_leave_type_validity(values.get('holiday_status_id'), values.get('request_date_from'), values.get('request_date_to'))
            if err:
                error_message.append(err)

            if error_message:
                values.update({
                    'employee_id': employee_id,
                    'leave': leave,
                    'types': types,
                    'redirect': redirect,
                    'page_name': 'leave',
                    'error_message': error_message,
                    'leave_name': '/',
                })

                response = request.render("hr_holidays_portal.edit_leave_details", values)
                response.headers['X-Frame-Options'] = 'DENY'
                return response

            if not leave_id:

                domain = [('calendar_id', '=', employee_id.resource_calendar_id.id or request.env.user.company_id.resource_calendar_id.id)]
                attendances = request.env['resource.calendar.attendance'].sudo().read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'dayofweek', 'day_period'], ['dayofweek', 'day_period'], lazy=False)

                # Must be sorted by dayofweek ASC and day_period DESC
                attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

                default_value = DummyAttendance(0, 0, 0, 'morning')

                # find first attendance coming after first_day
                attendance_from = next((att for att in attendances if int(att.dayofweek) >= fields.Datetime.from_string(values.get('request_date_from')).weekday()), attendances[0] if attendances else default_value)
                # find last attendance coming before last_day
                attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= fields.Datetime.from_string(values.get('request_date_to')).weekday()), attendances[-1] if attendances else default_value)

                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)

                tz = request.env.user.tz if request.env.user.tz else 'UTC'  # custom -> already in UTC
                values['date_from'] = timezone(tz).localize(
                    dt.combine(fields.Datetime.from_string(values.get('request_date_from')), hour_from)).astimezone(UTC).replace(tzinfo=None)
                values['date_to'] = timezone(tz).localize(
                    dt.combine(fields.Datetime.from_string(values.get('request_date_to')), hour_from)).astimezone(
                    UTC).replace(tzinfo=None)
                leave = HrLeave.sudo().create(values)
            else:
                leave.update(values)


            if redirect:
                return request.redirect(redirect)
            return request.redirect('/my/leave')

        values.update({
            'employee_id': employee_id,
            'leave': leave,
            'types': types,
            'redirect': redirect,
            'page_name': 'leave',
            'leave_name': '/',
        })

        response = request.render("hr_holidays_portal.edit_leave_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/my/leave/delete/<int:leave_id>'], type='http', auth="public", website=True)
    def delete_leave(self, leave_id=None, access_token=None, **kw):
        if not leave_id:
            return request.redirect('/my/leave')
        leave = request.env['hr.leave'].browse(leave_id)
        leave.unlink()

        return request.redirect('/my/leave')

    @http.route(['/my/leave/json'], type='http', auth="public", website=True)
    def get_leave_json(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return
        HrLeave = request.env['hr.leave']
        leaves = HrLeave.search([('employee_id', '=', employee_id.id)])

        leave_list = []
        for leave in leaves:
            vals = {
                'title': leave.display_name,
                'start': str(leave.request_date_from),
                'end': str(leave.request_date_to),
                'url': '/my/leave/%s' % leave.id
            }

            leave_list.append(vals)

        return json.dumps(leave_list)