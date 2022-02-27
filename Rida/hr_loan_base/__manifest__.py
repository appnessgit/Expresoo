
{

	'name': "Rida HR: Employee Loan",
    'summary': """This Module to handle Loan request and loan type and conditions""",
    'description': """This Module to handle Loan request and loan type and conditions""",
    'version': '15.0.1',
	'sequence': 9,
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

	'depends' : ['hr_payroll_account','hr','hr_contract','hr_payroll'],
	'data': [
		'security/ir.model.access.csv',
		'sequences/hr_loan_sequence.xml',
		'views/hr_loan_view.xml',
		'views/hr_loan_config_view.xml',
		'views/dashboard.xml',
		'views/hr_payroll_view.xml',
		'views/hr_loan_clear_view.xml',
		'views/hr_loan_recalculation_view.xml',
		'views/hr_loan_extent.xml',
		# 'views/res_config.xml',
		'datas/hr_payroll_data.xml',
		'datas/mail_activity_data.xml',
		'reports/hr_loan_report_pdf_view.xml',
		'reports/reports_view.xml',
	],

	'installable': True,
	'auto_install': False,
}

