from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError





class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    eos_id = fields.Many2one('hr.end.service', string='EOS')

    def unlink(self):
        for rec in self:
            if rec.eos_id:
                rec.eos_id.payslip_count = 0
            else:
                pass
        return super(HrPayslip, self).unlink()



class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    

    eos_id = fields.Many2one('hr.end.service', string='EOS')