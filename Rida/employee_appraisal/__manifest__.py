# -*- coding: utf-8 -*-

{
    'name': 'Rida HR: Employee Appraisal',
    'description': '',
    'author': 'Appness Technology',
    'depends': ['hr_contract', 'base','hr_eos_main'],
    'data': [
        'security/ir.model.access.csv', 
        'data/seq.xml',      
        'data/cron.xml',      
        'views/employee_appraisal_view.xml',
        'views/contract_extend.xml',
        'views/menu_item.xml',
        'views/contract_notification.xml'
    ],
    'application': True,
}