# -*- coding: utf-8 -*-
{
    'name': "Appness HR: Leaves - Self Service",
    'summary': """Employee leaves self service """,
    'author': "Appness Technology",
    'website': "http://www.appness.net",
    'category': 'hr',
    'version': '15.0.1',
    'sequence': 22,
    # any module necessary for this one to work correctly
    'depends': ['hr_portal', 'hr_holidays'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/leave_portal_templates.xml',
    ]
}
