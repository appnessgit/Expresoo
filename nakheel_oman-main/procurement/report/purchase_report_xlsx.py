# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo.exceptions import ValidationError, UserError
from odoo import models


class PurchaseReportXls(models.AbstractModel):
    _name = 'report.procurement.purchase_report_xlsx'
    _description = "Purchase Report"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self,workbook, data, lines):
        date_from = data['date_from']
        date_to = data['date_to']
        data_get = data['data']
        domain = [('date_order', '>=', date_from), ('date_order', '<=', date_to)]
        if data_get == 'confirm':
            domain += [('state', '=', 'purchase')]

        orders = self.env['purchase.order'].search(domain)
        format1 = workbook.add_format({'font_size': 12, 'bold': False, 'bg_color': '#005CB9', 'font_color': '#FFFFFF'})
        format2 = workbook.add_format({'bold': False})
        company_currency = self.env.user.company_id.currency_id
        format1.set_text_wrap()
        format2.set_text_wrap()

        sheet = workbook.add_worksheet("Purchase Orders")

        sheet.set_column("A:U", 30)

        sheet.write('A1', "MR Num", format1)
        sheet.write('B1', "MR Req. By", format1)
        sheet.write('C1', "MR Estimated Amount", format1)
        sheet.write('D1', "Product Category", format1)
        sheet.write('E1', "Proc. Officer", format1)
        sheet.write('F1', "MR Priority", format1)
        sheet.write('G1', "MR Created", format1)
        sheet.write('H1', "Inventory Checked", format1)
        sheet.write('I1', "LM Approval", format1)
        sheet.write('J1', "RFQ Created", format1)
        sheet.write('K1', "PO Created", format1)
        sheet.write('L1', "PO", format1)
        sheet.write('M1', "Supplier", format1)
        sheet.write('N1', "CR No.", format1)
        sheet.write('O1', "PO Date", format1)
        sheet.write('P1', "PO Title", format1)
        sheet.write('Q1', "PO Amount", format1)
        sheet.write('R1', "PO Amount ({})".format(company_currency.symbol), format1)
        sheet.write('S1', "Receiving Date", format1)
        sheet.write('T1', "GRN Status", format1)
        sheet.write('U1', "PO Status", format1)

        row = 0

        for order in orders:
            row += 1
            sheet.write(row, 0, order.request_id.name if order.request_id else '-', format2)
            sheet.write(row, 1, order.request_id.requested_by.name if order.request_id else '-', format2)
            sheet.write(row, 2, order.request_id.amount_total_purchase if order.request_id else '-', format2)
            sheet.write(row, 3, order.request_id.categ_id.display_name if order.request_id else '-', format2)
            sheet.write(row, 4, order.user_id.name, format2)
            sheet.write(row, 5, dict(order.request_id._fields['priority'].selection).get(order.request_id.priority) if order.request_id else '-', format2)
            sheet.write(row, 6, str(order.request_id.create_date)[:10] if order.request_id else '-', format2)
            sheet.write(row, 7, str(order.request_id.inventory_check_date)[:10] if order.request_id and order.request_id.inventory_check_date else '-', format2)
            sheet.write(row, 8, str(order.request_id.lm_approval_date)[:10] if order.request_id and order.request_id.lm_approval_date else '-', format2)
            sheet.write(row, 9, str(order.create_date)[:10], format2)
            sheet.write(row, 10, str(order.date_approve)[:10] if order.date_approve else "-", format2)
            sheet.write(row, 11, order.name, format2)
            sheet.write(row, 12, order.partner_id.name, format2)
            sheet.write(row, 13, order.partner_id.commercial_reg or "-", format2)
            sheet.write(row, 14, str(order.date_order)[:10], format2)
            sheet.write(row, 15, order.po_title or '-', format2)
            sheet.write(row, 16, str(order.amount_total) + " " + str(order.currency_id.symbol), format2)
            sheet.write(row, 17, order.currency_id.with_context(date=order.date_order).compute(order.amount_total, company_currency), format2)
            sheet.write(row, 18, str(order.date_planned)[:10], format2)
            sheet.write(row, 19, dict(order._fields['delivery_status'].selection).get(order.delivery_status), format2)
            sheet.write(row, 20, dict(order._fields['state'].selection).get(order.state), format2)
