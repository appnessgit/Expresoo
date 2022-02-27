# -*- coding: utf-8 -*-
{
    'name': "Appness HR: EOS with Loan",
    'summary': """This Module to integrated between Eos and Laon""",
    'description': """This Module to integrated between Eos and Laon""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['base','hr_loan_base','hr_eos_main','hr_eos_custody'],

    # always loaded
    'data': [
        'views/hr_loan_end_service.xml',
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}