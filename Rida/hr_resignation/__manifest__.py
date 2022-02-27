# -*- coding: utf-8 -*-
{
    'name': 'Appness HR: HR Resignation',
    'summary': 'Handle the resignation process of the employee',
    'version': '15.0.1',
    'sequence': 27,
    'author': 'Appness Technology',
    'website': "http://www.appness.net",
    'depends': ['hr', 'hr_employee_main','hr_eos_main'],
    'category': 'Human Resources',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/resignation_sequence.xml',
        'views/hr_employee.xml',
        'views/resignation_view.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}

