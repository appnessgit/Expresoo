# -*- coding: utf-8 -*-
{
    'name': "Base (Nakheel Oman)",

    'summary': """
        - Branches \n
        - Access Rights
        """,

    'description': """
        Nakheel Oman
    """,

    'author': "Appness Tech.",
    'website': "http://www.app-ness.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_automation', 'hr', 'account', 'analytic', 'stock', 'purchase_requisition'],

    # always loaded
    'data': [
        'data/mail_data.xml',
        'data/base_automation.xml',
        'data/ir_cron.xml',
      #  'security/hr_security.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_branch_views.xml',
        'views/res_users_views.xml',
        'views/hr_views.xml',
        'views/res_config_settings_views.xml',
        'views/delegation_views.xml'
        #'views/account_button_access.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
