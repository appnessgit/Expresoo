# -*- coding: utf-8 -*-
{
    'name': "Appness HR: EOS with accounting",
    'summary': """This Module to integrated between Eos and accounting""",
    'description': """This Module to integrated between Eos and accounting""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['base','account','hr_eos_main'],

    # always loaded
    'data': [
        'views/hr_eos_accounting.xml',
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}