# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class EmployeeAppraisal(models.Model):
    _name = 'employee.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='sequence'
    _description = 'Employee Appraisal'

    sequence = fields.Char( index= True, default='New')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', required=True )
    date_from = fields.Date(string='Start Date' , required=True )
    date_to = fields.Date(string='End Date' , required=True )
    rate = fields.Float(string='Rate' , required=True )
    state = fields.Selection(string='Status', default='draft' ,selection=[('draft', 'Draft'), ('waiting', 'Waiting for approval'),('second_approval', 'Second Approval'),('done', 'Approved'),('reject', 'Rejected')])
    notes = fields.Text(string='Notes')
    

    @api.model
    def create(self,vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('seq.appraisal')
        vals['state'] = 'waiting'
        return super(EmployeeAppraisal, self).create(vals)


    def first_submit(self):  
        self.write({                
        'state': 'waiting'        })
        



    def first_approval(self):  
        self.write({                
        'state': 'second_approval'        })
        self.activity_unlink(['employee_appraisal.mail_probation_reminder_appraisal'])


    def first_approval_reject(self):  
        self.write({    
        'state': 'draft'        })  




    def second_approval(self):  
        self.write({                
        'state': 'done'        })

    def second_approval_reject(self):  
        self.write({    
        'state': 'reject'        })  




