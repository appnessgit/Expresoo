# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akshay Babu(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time


class PurchaseDashboardWizard(models.TransientModel):
    _name = 'purchase.dashboard.wizard'

    date_from = fields.Date(string='From', help='Report Start Date', required=True,
                            default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date(string='To', help='Report End Date', required=True,
                          default=lambda *a: time.strftime('%Y-%m-%d'))
    data = fields.Selection([('confirm', 'Confirmed POs'), ('all', 'All')], string="Show", default="confirm")

    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        date_from = data['date_from']
        date_to = data['date_to']
        data_get = data['data']
        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to)]
        if data_get == 'confirm':
            domain += [('state', '=', 'purchase')]

        orders = self.env['purchase.order'].search(domain)
        today = fields.Date.today()

        datas = {
            'orders': orders.ids,
            'today': today,
            'form': data,
        }
        report = self.env.ref('procurement.purchase_pdf')
        landscape_paperformat_id = self.env['report.paperformat'].search([('orientation', '=', 'Landscape')], limit=1)
        if landscape_paperformat_id:
            report.paperformat_id = landscape_paperformat_id
        return report.report_action(self, data=datas)

    def print_report_xls(self):
        self.ensure_one()
        [data] = self.read()

        return self.env.ref('procurement.purchase_xlsx').report_action(self, data=data)
