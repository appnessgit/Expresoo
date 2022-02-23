# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, time
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import time


class ServiceRequisition(models.Model):
    _name = 'service.requisition'
    _inherit = ['mail.thread']

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('service.requisition') or '/'


    name = fields.Char('Name',default=_get_default_name,
        copy=False, readonly=True, required=True,
        states={'done': [('readonly', True)]})
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancelled'), ('done', 'Done')], 'State', default='draft', track_visibility='onchange')
    request_ids = fields.Many2many('purchase.request', string='Material Requests', track_visibility='always')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order', track_visibility='always')
    sale_id = fields.Many2one('sale.order', 'Sales Order')
    user_id = fields.Many2one('res.users', 'Requested By', track_visibility='always')
    schedule_date = fields.Date('Scheduled Date', track_visibility='always')
    description = fields.Char('Description')
    line_ids = fields.One2many('service.requisition.line', 'service_id')
    company_id = fields.Many2one('res.company', 'Company')
    backorder_id = fields.Many2one('service.requisition', 'Backorder of')
    job_completion = fields.Binary('Job Completion')

    def unlink(self):
        for rec in self:
            if True:
                raise UserError("Sorry. cannot delete service entries!")

        return super(ServiceRequisition, self).unlink()

    def button_confirm(self):
        if all(line.service_qty_done == 0 for line in self.line_ids):
            raise UserError("Please add some quantity before validating!")
        if self.purchase_id:
            self.purchase_id.is_service_receipt = True
            for line in self.line_ids:
                for po_line in self.purchase_id.order_line:
                    if line.service_qty_done > line.product_qty:
                        raise UserError('You cannot receive service amount more than requested!!')
                    if line.line_id.id == po_line.id:
                        # po_line.service_qty_done = line.service_qty_done
                        po_line.qty_received = po_line.qty_received + line.service_qty_done

        if self.sale_id:
            for line in self.line_ids:
                if line.service_qty_done > line.product_qty:
                    raise UserError('You cannot receive service amount more than requested!!')
                line.sale_line_id.qty_delivered += line.service_qty_done

        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        return self.write({'state': 'done'})

    def button_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            for line in rec.line_ids:
                purchase_line = line.line_id
                if not self.env.user.has_group('base.group_no_one') and purchase_line.qty_invoiced:  # == purchase_line.qty_received:
                    raise UserError(_("Canceling a service entry is not allowed if a bill is created."))
                line.line_id.qty_received -= line.service_qty_done

    def _create_service_backorder(self, pick_id):
        for pick in pick_id:
            if pick.request_ids:
                requested_by = pick.request_ids[0].requested_by
            service = {
                'purchase_id': pick.purchase_id.id or False,
                'request_ids':pick.request_ids or False,
                'user_id': pick.user_id.id or False,
                'schedule_date':pick.schedule_date,
                'company_id':pick.company_id.id,
                'backorder_id':pick.id, #check if requested by or created by    
            }
            service_picking = pick.create(service)
            service_orderline = pick.line_ids.filtered(lambda r: r.product_qty > r.service_qty_done).create_service_backorder_lines(service_picking)
    
    def action_generate_backorder_wizard(self):
        view = self.env.ref('procurement.view_backorder_confirmation')
        wiz = self.env['service.backorder.confirmation'].create({'pick_ids': [(4, p.id) for p in self]})
        return {
            'name': _('Create Backorder?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.backorder.confirmation',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

    def _check_backorder(self):
        quantity_todo = {}
        quantity_done = {}
        for move in self.mapped('line_ids'):
            quantity_todo.setdefault(move.product_id.id, 0)
            quantity_done.setdefault(move.product_id.id, 0)
            quantity_todo[move.product_id.id] += move.product_qty
            quantity_done[move.product_id.id] += move.service_qty_done
        return any(quantity_done[x] < quantity_todo.get(x, 0) for x in quantity_done)

    def button_reset(self):
        self.ensure_one()
        if not self.purchase_id.state == 'purchase':
            raise UserError(_("Related purchase order should be confirmed to set this record to draft."))
        self.purchase_id.is_service_receipt = False
        return self.write({'state': 'draft'})


class ServiceRequisition(models.Model):
    _name = "service.requisition.line"

    service_id = fields.Many2one('service.requisition')
    product_id = fields.Many2one('product.product','Proudct')
    name = fields.Char('Description')
    product_uom_id = fields.Many2one('uom.uom','Uom')
    product_qty = fields.Float('Ordered Qty',digits=(16, 4))
    service_qty_done = fields.Float('Done',digits=(16, 4))
    company_id = fields.Many2one('res.company','Company')
    line_id = fields.Many2one('purchase.order.line')
    sale_line_id = fields.Many2one('sale.order.line')
    amount = fields.Monetary(compute='get_line_amount', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id)

    @api.depends('service_qty_done', 'line_id.price_subtotal', 'line_id.product_qty')
    def get_line_amount(self):
        for line in self:
            unit_price = 0
            if line.line_id:
                unit_price = line.line_id.price_subtotal / line.line_id.product_uom_qty
            elif line.sale_line_id:
                unit_price = line.sale_line_id.price_subtotal / line.sale_line_id.product_qty
            line.amount = unit_price * line.service_qty_done

    def create_service_backorder_lines(self, service):
        moves = self
        done = self.browse()
        for line in self:
            if line.product_uom_id:
                uom = line.product_uom_id
            qty = line.product_qty - line.service_qty_done
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_qty':qty,
                'product_uom_id': uom.id or False,
                'service_id': service.id,
                'company_id': service.company_id.id,
                'line_id':line.line_id.id,
            }
            done += moves.create(template)
        return done


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    service_delivery = fields.Boolean('Service Delivered')
    item_type = fields.Selection([('material', 'Material'), ('service', 'Service')], 'Item Type', readonly=False)
    service_count = fields.Integer(compute="compute_service_count")
    is_service_receipt = fields.Boolean('Done')

    def compute_service_count(self):
        self.service_count = self.env['service.requisition'].search_count([('purchase_id','=',self.id)])

    def button_confirm(self):
        for order in self:
            order._add_supplier_to_product()
            order.button_approve()
            # if order.item_type == 'service':
            self._create_service_delivery()
        return True

    def _create_service_delivery(self):
        self.ensure_one()
        if not self.order_line:
            raise UserError(_('Please create Purchase Order Lines.'))
        # if self.order_type == 'replacement':
        requested_by = False
        service_lines =  self.order_line.filtered(lambda r: r.product_id.type in ['service'])
        if not service_lines:
            return True
        if self.request_ids:
            requested_by = self.request_ids[0].requested_by
        service = {
            'purchase_id': self.id or False,
            'request_ids': self.request_ids,
            'user_id': requested_by.id if requested_by else False,
            'schedule_date': self.date_planned,
            'company_id': self.env.user.company_id.id, #check if requested by or created by
        }
        service_picking = self.env['service.requisition'].create(service)
        service_orderline = service_lines.create_service_orderline(service_picking)

    def action_view_service_delivery(self):
        return{
        'name':"Service Delivery",
        'type':'ir.actions.act_window',
        'res_model':'service.requisition',
        'view_id':False,
        'view_mode':'tree,form',
        'view_type':'form',
        'target':'current',
        'domain':[('purchase_id','=',self.id)],
        }


class PurchaseOrderLine(models.Model):
    _inherit="purchase.order.line"

    service_qty_done = fields.Float('Service Deliverd') #invalid field

    def create_service_orderline(self, service):
        moves = self.env['service.requisition.line']
        done = self.env['service.requisition.line'].browse()
        for line in self:
            if line.product_uom:
                uom = line.product_uom
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_qty':line.product_uom_qty,
                'product_uom_id': uom.id or False,
                'service_id': service.id,
                'company_id': service.company_id.id,
                'line_id':line.id,
                'currency_id': line.currency_id.id
            }
            done += moves.create(template)
        return done
