# -*- coding: utf-8 -*-
{
    'name': "Appness HR: Loan Total Report",
    'summary': """Appness HR : Loan Total Report""",
    'description': """Appness HR : Loan Total Report""",
    'version': '15.0.1',
    'sequence': 11,
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['hr_loan_base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/report_template.xml',
        'wizard/report_wizard_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}
