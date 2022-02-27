# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ExpensesWorkflow(models.Model):
    _inherit  = 'hr.expense.sheet'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('lm', 'Line Manager Approval'),
        ('hr_officer', 'Hr Officer Approval'),
        ('ccso', 'CCSO'),
        ('accountant', ' Accountant Approval'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True, help='Expense Report State')


# draft buttons
    def submit(self):  
        self.write({                
        'state': 'lm'        })

# line_manager buttons
    def lm_approve(self):  
        self.write({                
        'state': 'hr_officer'        })

    def lm_approve_reject(self):  
        self.write({    
        'state': 'draft'        })  


# hr_officer buttons
    def hr_approve(self):  
        self.write({                
        'state': 'ccso'        })

    def hr_approve_reject(self):  
        self.write({    
        'state': 'lm'        })  

# ccso buttons
    def ccso_approve(self):  
        self.write({                
        'state': 'accountant'        })

    def ccso_approve_reject(self):  
        self.write({    
        'state': 'hr_officer'        })  

# accountant buttons
    def accountant_approve(self):  
        self.write({                
        'state': 'done'        })

    def accountant_approve_reject(self):  
        self.write({    
        'state': 'cancel'        })  


# cancel and set to draft buttons
    def cancel(self):  
        self.write({                
        'state': 'cancel'        })

    def set_to_draft(self):  
        self.write({    
        'state': 'draft'        })  
