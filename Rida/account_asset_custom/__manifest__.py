# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Rida custom Assets Management',
    'description': """
Assets management
=================
Manage assets owned by a company or a person.
Keeps track of depreciations, and creates corresponding journal entries.

    """,
    'author': "appnesss Technology",
    'website': "http://www.appnesss.net",

    'category': 'Accounting/Accounting',
    'version': '15.0.1',
    'sequence': 32,
    'depends': ['hr','base_address_city','account_asset'],
    'data': [
        # 'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'views/account_assets_category.xml',        
        'views/account_asset_views.xml',
        'report/asset_badge.xml',
        'wizard/asset_transfer_wizard.xml'

        # 'wizard/asset_modify_views.xml',
        # 'wizard/asset_pause_views.xml',
        # 'wizard/asset_sell_views.xml',
        # 'views/account_account_views.xml',
        # 'views/account_deferred_revenue.xml',
        # 'views/account_deferred_expense.xml',
        # 'views/account_move_views.xml',
        # 'views/account_asset_templates.xml',
        # 'report/account_assets_report_views.xml',
    ],
    
}
