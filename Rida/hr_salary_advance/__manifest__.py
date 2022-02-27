
{
    'name': 'Rida HR: Advance Salary',
    'version': '15.0.1',
    'sequence': 12,
    'summary': 'Advance Salary In HR',
    'description': """Helps you to manage Advance Salary Request of your company's staff.""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Appness Technology',
    'website': 'https://www.appness.net',
    'depends': ['hr_payroll','hr','hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/salary_rule.xml',
        'views/salary_advance.xml',
        'views/res_config_settings_view.xml',
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

