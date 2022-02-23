# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Procurement (Nakheel Oman)',
    'version': '14.0.1',
    'category': 'Purchases & Inventory',
    'author': 'Appness Tech',
    'description': """
    supply chain management for oman post
    """,
    'summary': 'Supply Chain Management',
    'website': 'http://app-ness.com',
    'images': ['static/description/icon.png'],
    'data': [
        'data/service_data.xml',
        'data/ir_groups.xml',
        'data/purchase_request_data.xml',
        'data/mail_data.xml',
        'security/purchase_request_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        #'data/ir_menu.xml',
        'wizard/purchase_order_reject_wizard.xml',
        'wizard/purchase_requisition_reject_wizard.xml',
        'wizard/stock_backorder_confirmation_views.xml',
        'wizard/purchase_dashboard_report_wizard.xml',
        'views/purchase_request_view.xml',
        'views/service.xml',
        'views/product_view.xml',
        'views/purchase_views.xml',
        'views/account_budget_views.xml',
        'views/purchase_requisition_views.xml',
        'views/stock_views.xml',
        'views/user_views.xml',
        'views/account_invoice_views.xml',
        'report/material_request_report_template.xml',
        'report/procurement_report.xml',
        'report/purchase_agreement_report.xml',
        'report/report_views.xml',
    ],

    'depends': ['mail', 'base_no', 'purchase_stock', 'purchase_requisition', 'hr','stock', 'stock_account', 'budget', 'stock_analytic', 'report_xlsx'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 105,
    'license': 'AGPL-3',
}
