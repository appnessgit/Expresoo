# -*- coding: utf-8 -*-
{
    'name': "Rida HR :Employee Promotion",
    'summary': """Appness HR : Employee Promotion """,
    'description': """Appness HR : Employee Promotion""",
    'author': "Appness Technology",
    'website': "http://www.appness.net",
    'category': 'HR',
    'version': '15.1.0',
    # any module necessary for this one to work correctly
    'depends': ['hr','hr_contract','hr_salary_increment','hr_employee_rotation','hr_contract_grade_base'],
    # always loaded
    'data': [
      'security/ir.model.access.csv',
      'views/employee_promotion.xml',
      'data/mail_activity_data.xml',
      # 'report/report_views.xml',
      'report/employee_promotion_report.xml',
      'views/employee_promotion_extended.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}