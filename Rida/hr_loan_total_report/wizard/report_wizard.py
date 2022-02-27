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

class LoanReportButton(models.TransientModel):
    _name = 'wizard.balance.report'

    department_id = fields.Many2one('hr.department', "Department")
    date_from = fields.Date("From")
    date_to = fields.Date("To")

    def print_report(self):
        self.ensure_one()
        [data] = self.read()

        datas = {
            'ids': [],
            'model': 'hr.loan',
            'form': data,
        
        }
        return self.env.ref('hr_loan_total_report.loan_report_pdf_id').with_context(from_transient_model=True).report_action(self, data=datas)
            