# -*- coding: utf-8 -*-
{
    'name': "Appness HR: EOS with Custody",
    'summary': """This Module to integrated between Eos and Custody""",
    'description': """This Module to integrated between Eos and Custody""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",

    # any module necessary for this one to work correctly
    'depends': ['base','hr_employee_main','hr_eos_main'],

    # always loaded
    'data': [
        'views/eos_custody.xml',
        # 'security/ir.model.access.csv',
        'report/eos_report.xml',
        'report/certificate_service_template.xml', 
        'report/certificate_service_report.xml', 
        'report/certificate_service_template_ar.xml',
        'report/certificate_service_report_ar.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',

    ],
}