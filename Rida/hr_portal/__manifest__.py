# -*- coding: utf-8 -*-
{
    'name': "Appness HR: Self Service",
    'summary': """Employee self service""",
    'author': "Appness Technology Co.Ltd.",
    'website': "http://appness.com",
    'category': 'hr',
    'version': '15.0.1',
    'sequence': 1,
    'depends': ['web','calendar', 'portal', 'hr_contract'],
    'price': 120,
    'currency': 'EUR',
    'data': [
        'security/ir.model.access.csv',
        'templates/website_assets.xml',
        'views/dashboard_portal_template.xml',
        'views/res_config_views.xml',
    ],
    'images': [
        'static/description/ss_sc_00.png',
    ],
    'assets': {
        'web.assets_frontend': [
            'hr_portal/static/src/js/scripts.js',
            'hr_portal/static/src/css/style.scs',
        ],
    }
}
