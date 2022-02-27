# -*- coding: utf-8 -*-
{
    'name': "Appness HR :Salary Increment",
    'summary': """Salary Increment For Appness HR""",
    'description': """Salary Increment For Appness HR""",
    'category': 'HR',
    'version': '15.0.1',
    'sequence': 8,
    'author': 'Appness Technology',
    'website': "https://www.appness.net",
    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_contract','hr_payroll'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/hr_increament_by_employees_views.xml',
        'views/hr_salary_increase_views.xml',
        'views/hr_payroll_view.xml',
        'data/mail_data.xml',
        'data/hr_payroll_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
     #   'demo.xml',
    ],
}
