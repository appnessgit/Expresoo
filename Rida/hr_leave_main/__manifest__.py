# -*- coding: utf-8 -*-
{
    'name': "Rida HR: Employee Leaves Management",
    'summary': """Employee Leaves Main """,
    'description': """Employee Leaves Main """,
    'author': "Appness Technology",
    'website': "http://www.appness.net",
    'category': 'HR',
    'version': '15.1.0',
    # any module necessary for this one to work correctly
    'depends': ['base','base_rida','hr_holidays','hr_payroll'],
    # always loaded
    'data': [
      
      'security/ir.model.access.csv',
      'security/securit_rules.xml',
      'wizard/justification.xml',
      'views/holidays_inherit.xml',
      'views/public_holiday.xml',
      'views/hr_leave_extended.xml',
      # 'views/leave_plan.xml',
      # 'views/leave_transfer.xml',
      'views/autoallocate.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
   #     'demo.xml',
    ],
}