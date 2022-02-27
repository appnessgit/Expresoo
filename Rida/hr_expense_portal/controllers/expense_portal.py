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

    EXPENSE_MANDATORY_BILLING_FIELDS = ["name", "product_id", "unit_amount", "quantity", "payment_mode"]

    EXPENSE_OPTIONAL_BILLING_FIELDS = ["reference", "date", "currency_id", "description", "attachment"]

    def expense_details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.EXPENSE_MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.EXPENSE_MANDATORY_BILLING_FIELDS + self.EXPENSE_OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

            values['expense_count'] = request.env['hr.expense'].search_count([
                ('employee_id', '=', employee_id.id)
            ])
            values['employee_id'] = employee_id
        return values

    def _expense_get_page_view_values(self, expense, access_token, **kwargs):

        values = {
            'expense': expense,
        }
        return self._get_page_view_values(expense, access_token, values, 'my_expense_history', True, **kwargs)

    @http.route(['/my/expense', '/my/expense/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expenses(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]
        else:
            return request.redirect('/my')

        HrExpense = request.env['hr.expense']

        domain = [('employee_id', '=', employee_id.id)]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'date desc, id desc'},
            'date_old': {'label': _('Oldest'), 'order': 'date asc, id asc'},
            'name': {'label': _('Description'), 'order': 'name asc, id asc'},
            'payment_mode': {'label': _('Paid By'), 'order': 'payment_mode asc, id asc'},
            'total_amount': {'label': _('Total'), 'order': 'total_amount desc, id desc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'reported': {'label': _('Submited'), 'domain': [('state', '=', 'reported')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            'done': {'label': _('Paid'), 'domain': [('state', '=', 'done')]},
            'refuesed': {'label': _('Refused'), 'domain': [('state', '=', 'refuesed')]},
        }

        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        expense_count = HrExpense.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/expense",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=expense_count,
            page=page,
            step=self._items_per_page
        )
        # search the records to display, according to the pager data
        expenses = HrExpense.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_expense_history'] = expenses.ids[:100]

        values.update({
            'date': date_begin,
            'expenses': expenses,
            'page_name': 'expense',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'employee_id': employee_id,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/expense',
        })

        return request.render("hr_expense_portal.portal_my_expenses", values)

    @http.route(['/my/expense/<int:expense_id>'], type='http', auth="public", website=True)
    def portal_my_expense(self, expense_id=None, access_token=None, **kw):
        try:
            expense_sudo = self._document_check_access('hr.expense', expense_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._expense_get_page_view_values(expense_sudo, access_token, **kw)
        return request.render("hr_expense_portal.portal_my_expense", values)

    @http.route(['/my/expense/edit'], type='http', auth="public", website=True)
    def update_expense(self, redirect=None, **post):
        attachment = False

        expense_id = False
        if post.get('id'):
            expense_id = int(post.get('id'))
        values = self._prepare_portal_layout_values()
        employee_id = False
        if request.env.user.employee_ids:
            employee_id = request.env.user.employee_ids[0]

        values.update({
            'error': {},
            'error_message': [],
        })

        products = request.env['product.product'].sudo().search([('can_be_expensed', '=', True)])
        currencies = request.env['res.currency'].sudo().search([])

        HrExpense = request.env['hr.expense']

        company_currency = request.env.user.company_id.currency_id

        expense = False
        if expense_id:
            expense = request.env['hr.expense'].browse(expense_id)
        attachment = post.get('attachment', False)
        post.pop('attachment', None)
        post.pop('id', None)

        if post:
            error, error_message = self.expense_details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)

            if error:
                values.update({
                    'employee_id': employee_id,
                    'expense': expense,
                    'products': products,
                    'currencies': currencies,
                    'company_currency': company_currency,
                    'redirect': redirect,
                    'page_name': 'expense',
                    'error_message': error_message,
                    'expense_name': '/',
                })

                response = request.render("hr_expense_portal.edit_expense_details", values)
                response.headers['X-Frame-Options'] = 'DENY'
                return response

            values = {key: post[key] for key in self.EXPENSE_MANDATORY_BILLING_FIELDS}
            values.update({key: post[key] for key in self.EXPENSE_OPTIONAL_BILLING_FIELDS if key in post})

            product_id = request.env['product.product'].browse(int(values.get('product_id')))
            accounts = product_id.sudo().product_tmpl_id.get_product_accounts()
            account_id = accounts['expense']
            currency_id = request.env['res.currency'].browse(int(values.get('currency_id')))

            values.update(
                {
                    'employee_id': employee_id.id,
                    'account_id': account_id.id
                })

            expense_sheet_sudo = request.env['hr.expense.sheet'].sudo()

            expense_sheet = False
            if not expense_id:
                values.update({
                    'product_id': int(values.get('product_id')),
                    'currency_id': int(values.get('currency_id')),
                })
                expense = HrExpense.create(values)
                if attachment:
                    attachment_value = {
                        'name': attachment.filename,
                        'datas': base64.encodestring(attachment.read()),
                        'datas_fname': attachment.filename,
                        'res_model': 'hr.expense',
                        'res_id': expense.id,
                    }
                    attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
                    expense.attachment_ids = [(4, attachment_id)]
                    expense.message_main_attachment_id = attachment_id

                expense_sheet = expense_sheet_sudo.search([
                    ('employee_id', '=', employee_id.id),
                    ('state', 'in', ['draft', 'submit']),
                    ('payment_mode', '=', expense.payment_mode)
                ], limit=1)

                if not expense_sheet:
                    expense_sheet = expense_sheet_sudo.create({
                        'name': expense.name,
                        'payment_mode': expense.payment_mode,
                        'employee_id': employee_id.id
                    })

                expense.sheet_id = expense_sheet.id
                expense_sheet.state = 'draft'

                expense_sheet.sudo().action_submit_sheet()

            else:
                expense.update(values)

            if redirect:
                return request.redirect(redirect)
            return request.redirect('/my/expense')

        values.update({
            'employee_id': employee_id,
            'expense': expense,
            'products': products,
            'currencies': currencies,
            'company_currency': company_currency,
            'redirect': redirect,
            'page_name': 'expense',
            'expense_name': '/',
        })

        response = request.render("hr_expense_portal.edit_expense_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
