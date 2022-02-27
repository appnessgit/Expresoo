# -*- coding: utf-8 -*-
{
    'name': "Appness HR: HR Dashboard",
    'summary': """Appness HR: HR Dashboard""",
    'description': """Appness HR: HR Dashboard""",
    'category': 'HR',
    'version': '15.0.1.0',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",
    'depends': ['hr', 'hr_holidays', 'hr_payroll', 'hr_recruitment', 'hr_resignation','hr_appraisal','hr_loan_base','hr_overtime'],
    'external_dependencies': {'python': ['pandas'],},
    'data': [
        'security/ir.model.access.csv',
        'report/broadfactor.xml',
        'views/dashboard_views.xml',
    ],
    # 'qweb': ["static/src/xml/hrms_dashboard.xml"],
    'images': ["static/description/banner.gif"],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            '/hrms_dashboard/static/src/css/hrms_dashboard.css',
            '/hrms_dashboard/static/src/js/hrms_dashboard.js',
            '/hrms_dashboard/static/src/css/lib/nv.d3.css',
            '/hrms_dashboard/static/src/js/lib/d3.min.js',
        ],
        'web.assets_qweb': [
            'hrms_dashboard/static/src/xml/hrms_dashboard.xml',
        ],
    }
}
