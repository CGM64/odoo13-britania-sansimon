# -*- coding: utf-8 -*-
# from odoo import http


# class ConciliacionBancaria(http.Controller):
#     @http.route('/conciliacion_bancaria/conciliacion_bancaria/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/conciliacion_bancaria/conciliacion_bancaria/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('conciliacion_bancaria.listing', {
#             'root': '/conciliacion_bancaria/conciliacion_bancaria',
#             'objects': http.request.env['conciliacion_bancaria.conciliacion_bancaria'].search([]),
#         })

#     @http.route('/conciliacion_bancaria/conciliacion_bancaria/objects/<model("conciliacion_bancaria.conciliacion_bancaria"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('conciliacion_bancaria.object', {
#             'object': obj
#         })
