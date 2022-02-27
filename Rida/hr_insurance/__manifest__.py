# -*- coding: utf-8 -*-

{
    'name': 'Appness HR: Employee Insurance',
    'summary': """Employee Insurance Management for Appness HR.""",
    'description': """Manages insurance amounts for employees to be deducted from salary""",
    'category': 'HR',
    'version': '15.0.1',
    'sequence': 15,
    'author': 'Appness Technology',
    'maintainer': 'Appness Technology',
    'company': 'Appness Technology',
    'website': 'https://www.appness.net',
    'depends': ['base', 'hr', 'hr_payroll',],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_insurance_security.xml',
        'views/employee_insurance_view.xml',
        'views/insurance_salary_stucture.xml',
        'views/policy_management.xml',
              ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
