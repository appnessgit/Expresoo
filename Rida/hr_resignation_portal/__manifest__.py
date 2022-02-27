# -*- coding: utf-8 -*-
{
    'name': "Appness HR: Resignation - Self Service",
    'summary': """Employee resignations self service """,
    'author': "Appness Technology",
    'website': "http://www.appness.net",
    'category': 'hr',
    'version': '15.0.1',
    'sequence': 28,
    'depends': ['hr_portal', 'hr_resignation'],
    'data': [
        'security/ir.model.access.csv',
        'views/resignation_portal_templates.xml',
    ]
}
