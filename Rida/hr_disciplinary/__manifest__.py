# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Appness HR: HR Disciplinary',
    'summary': 'This Module Manage  Violation and Sanction per employee ',
    'version': '15.0.1',
    'author': 'Appness Technology',
    'website': 'https://www.appness.net',
    'category': 'HR',
    'sequence': 6,

    'depends': ['hr','hr_contract','hr_payroll'],
    'data': [
        'data/hr_payroll_data.xml',
        'security/ir.model.access.csv',
        'wizard/displine_employee_wizard.xml',
        'wizard/displine_violation_wizard.xml',
        'views/discipline_views.xml',
        'views/hr_payroll_view.xml',
        'views/cron_check_discpline.xml',
        'data/ir_sequence_data.xml',
        'data/hr_payroll_data.xml',
        'report/displine_employee_template.xml',
        'report/displine_violation_template.xml',
        'report/snaction_template.xml',
        'report/reports_view.xml',
    ],
    'installable': True,

}
