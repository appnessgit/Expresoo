# -*- coding: utf-8 -*-
from odoo import http

# class SickLeaveEuropoles(http.Controller):
#     @http.route('/sick_leave_europoles/sick_leave_europoles/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sick_leave_europoles/sick_leave_europoles/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sick_leave_europoles.listing', {
#             'root': '/sick_leave_europoles/sick_leave_europoles',
#             'objects': http.request.env['sick_leave_europoles.sick_leave_europoles'].search([]),
#         })

#     @http.route('/sick_leave_europoles/sick_leave_europoles/objects/<model("sick_leave_europoles.sick_leave_europoles"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sick_leave_europoles.object', {
#             'object': obj
#         })