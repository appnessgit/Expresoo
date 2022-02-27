# -*- coding: utf-8 -*-
from odoo import http

# class HrInstallAll(http.Controller):
#     @http.route('/hr_install_all/hr_install_all/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_install_all/hr_install_all/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_install_all.listing', {
#             'root': '/hr_install_all/hr_install_all',
#             'objects': http.request.env['hr_install_all.hr_install_all'].search([]),
#         })

#     @http.route('/hr_install_all/hr_install_all/objects/<model("hr_install_all.hr_install_all"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_install_all.object', {
#             'object': obj
#         })