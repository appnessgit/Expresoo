# -*- coding: utf-8 -*-
{
    'name': "purchase_custom",

    'summary': """
        account_custom""",

    'description': """
       Rida account_custom
    """,

    'author': "Appness Technologt",
    'website': "http://appness.net",


    'category': 'Uncategorized',
    'version': '15.0.1',

    # any module necessary for this one to work correctly

    'depends': ['base','base_rida', 'account',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/mail_template_data.xml',
        # 'data/ir_cron_data.xml'
        'views/new.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
