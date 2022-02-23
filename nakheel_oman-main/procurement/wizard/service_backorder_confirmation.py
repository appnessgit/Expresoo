# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class ServiceBackorderConfirmation(models.TransientModel):
    _name = 'service.backorder.confirmation'
    _description = 'Backorder Confirmation'

    pick_ids = fields.Many2many('service.requisition', 'service_picking_backorder_rel')

    def _process(self, cancel_backorder=False):
        if cancel_backorder == False:
            # raise UserError(self.pick_ids)

            for pick_id in self.pick_ids:
                service_id = self.pick_ids.id
                pick_id._create_service_backorder(pick_id)
                pick_id.write({'state':'done'})
        if cancel_backorder:
            for pick_id in self.pick_ids:
                backorder_pick = self.env['service.requisition'].search([('backorder_id', '=', pick_id.id)])
                # backorder_pick.action_cancel()
                pick_id.write({'state':'done'})
                pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))

    def process(self):
        self._process()

    def process_cancel_backorder(self):
        self._process(cancel_backorder=True)
