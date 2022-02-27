# -*- coding: utf-8 -*-

{
    'name': 'Expensess workflow',
    'description': '',
    'author': 'Appness Technology',
    'depends': ['base','hr_expense'],
    'data': [
        'security/ir.model.access.csv',  
        'security/securit_rules.xml' ,
        'views/expenses_workflow_view.xml'
    ],
    'application': True,
}