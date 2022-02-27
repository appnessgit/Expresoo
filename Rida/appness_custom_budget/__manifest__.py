# -*- coding: utf-8 -*-
{
    'name': "Appness Custom  Budget",


    'author': "Appness Technology",
    'website': "http://www.appness.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['account_accountant', 'account_budget', 'hr', 'budget'],
    'depends': ['account_accountant', 'account_budget', 'hr'],

    # always loaded
    'data': [
        'data/mail_activity_data.xml',
        'data/sequence.xml',
        'security/groups.xml',
        'security/budget_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/account_budget_views.xml',
        'views/account_budget_amendment_views.xml',
        'views/account_budget_department_form_views.xml',
        'views/hr_views.xml',
        'views/res_config_setting.xml',
        'wizard/generate_budget_department_form.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
