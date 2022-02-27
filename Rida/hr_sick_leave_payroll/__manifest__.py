# -*- coding: utf-8 -*-
{
    'name': "Appness HR: Sick Leave Payroll",
    'summary': """Sick Leave Integrated with Payroll For Appness HR""",
    'description': """Sick Leave Integrated with Payroll For Appness HR""",
    'author': "Appness Technology",
    'website': "http://www.appness.net",
    'category': 'HR',
    'version': '15.0.1',
    # any module necessary for this one to work correctly
    'depends': ['hr_holidays','hr_payroll'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/hr_employee.xml',
        # 'data/hr_rule_sick_leave.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}