# -*- coding: utf-8 -*-
{
    'name': "Rida HR: End of service Management",
    'summary': """This Main Module to install basic eos modules""",
    'description': """This Main Module to install basic eos modules""",
    'version': '15.0.1',
    'category': 'HR',
    'author': 'Appness Technology',
    'website': "https://www.appness.net",
    # any module necessary for this one to work correctly
    # 'depends': ['base','hr','hr_payroll','hr_contract','hr_contract_benefit'],
    # 'depends': ['base','hr','hr_payroll','hr_contract_grade_base','hr_contract_benefit'],
    'depends': ['hr_overtime','base','hr','hr_payroll','hr_contract_grade_base','hr_contract_benefit'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/hr_end_service.xml',
        'views/hr_contract.xml',
        'views/res_config_settings_view.xml',
        'views/gratuity_configuration.xml',
        'data/eos_type_data.xml',
        'data/mail_activity_type.xml',
        'report/eos_report_template.xml',
        'report/eos_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}