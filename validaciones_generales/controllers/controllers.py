# -*- coding: utf-8 -*-
# from odoo import http


# class ValidacionesGenerales(http.Controller):
#     @http.route('/validaciones_generales/validaciones_generales/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/validaciones_generales/validaciones_generales/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('validaciones_generales.listing', {
#             'root': '/validaciones_generales/validaciones_generales',
#             'objects': http.request.env['validaciones_generales.validaciones_generales'].search([]),
#         })

#     @http.route('/validaciones_generales/validaciones_generales/objects/<model("validaciones_generales.validaciones_generales"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('validaciones_generales.object', {
#             'object': obj
#         })
