# -*- coding: utf-8 -*-
{
    'name': "Appness HR: EOS with Loan accounting",
    'summary': """This Module to integrated between Eos and Laon and accounting""",
    'description': """This Module to integrated between Eos and Laon and accounting""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['base','hr_eos_loan','hr_eos_accounting'],

    # always loaded
    'data': [
        'views/hr_loan_accounting_eos.xml',
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}