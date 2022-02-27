
{
    'name': 'Appness HR: Advance Salary Accounting',
    'version': '15.0.1',
    'sequence': 13,
    'summary': 'Advance Salary link with Account ',
    'description': """This module help to integrate Advance salary with accounting""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Appness Technology',
    'website': 'https://www.appness.net',
    'depends': [
        'hr_salary_advance', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/salary_advance_account.xml',
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

