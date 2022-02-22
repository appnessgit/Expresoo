# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Company(models.Model):
    _inherit = "res.company"

#   procurement Limit
    po_committee_limit = fields.Monetary("Need to upload attachment for PO committee approval", default=500.0, readonly=False)


    @api.model
    def send_approval_email(self, model, object, emails):
        mail = self.env['mail.mail']
        vals = {}
        try:
            action_id = self.env['ir.actions.act_window'].search([('res_model', '=', model)], limit=1).id
            base_url = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')], limit=1).value
            link = '%s/mail/view?model=%s&res_id=%s' % (base_url, model, object.id)

            body = """
                    <div style="margin: 0px; padding: 0px; font-size: 13px;">
                    <p style="margin: 0px; padding: 0px; font-size: 13px;">
                        Hello <br /><br />
                        Please approve this document: <b>%s</b>
                        <div style="margin: 16px 0px 16px 0px;">
                            <a href="%s"
                                style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">
                                Link
                            </a>
                        </div>
                        <br />
                        Thank you for your participation.
                    </p>
                </div>
            """ % (object.name, link)

            vals['subject'] = "Approval Request " + object.name
            vals['email_from'] = object.company_id.email
            vals['email_to'] = emails
            vals['body_html'] = body
            vals['state'] = 'outgoing'

            email = mail.create(vals).send()

        except:
            raise UserError("Cannot send emails!")
