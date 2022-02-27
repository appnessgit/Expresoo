# -*- coding: utf-8 -*-
{
    'name': 'Appness HR: Payroll Total Report ',
    'version': '15.0.1',
    'sequence': 25,
    "category": "hr",
    'author': 'Apness Technology',
    'website': "https://www.appness.net",
    'company': 'Appness Tech',
    'summary': """Advanced PDF Reports Employee Reports""",
    'depends': ['base', 'hr','hr_employee_main','report_xlsx', 'hr_payroll'],
    'license': 'AGPL-3',
    'data': [
            'security/ir.model.access.csv', 
             'wizard/hr_payroll_config.xml',
             'wizard/payroll_annual_report_wizard_view.xml',
             'report/payroll_annual_report.xml',
             'report/payroll_annual_report_pdf_view.xml',
             'report/payroll_bank_report_pdf.xml',
             ],

    'installable': True,
    'auto_install': False,
}
