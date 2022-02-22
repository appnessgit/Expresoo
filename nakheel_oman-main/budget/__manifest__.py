# -*- coding: utf-8 -*-
{
    'name': "Budget Customizations (Nakheel Oman)",
    'summary': """Budget Customizations""",
    'description': """This module will manage the Budget as budget control and add features,""",
    'author': "Appness Technology Co.Ltd.",
    'website': "https://www.appness.net",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '15.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_no', 'account_accountant', 'account_budget'],

    # always loaded
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/account_budget_views.xml',
        'views/account_budget_amendment_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
