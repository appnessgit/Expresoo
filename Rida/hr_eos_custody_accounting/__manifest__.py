# -*- coding: utf-8 -*-
{
    'name': "Appness HR: EOS with Custody Accounting",
    'summary': """This Module to integrated between Eos and Custody Accounting""",
    'description': """This Module to integrated between Eos and Custody Accounting""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['base','account','hr_eos_custody','hr_eos_accounting'],

    # always loaded
    'data': [
        'views/hr_end_service.xml',
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}