# -*- coding: utf-8 -*-
# from odoo import http


# class CambioPresentacion(http.Controller):
#     @http.route('/cambio_presentacion/cambio_presentacion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cambio_presentacion/cambio_presentacion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cambio_presentacion.listing', {
#             'root': '/cambio_presentacion/cambio_presentacion',
#             'objects': http.request.env['cambio_presentacion.cambio_presentacion'].search([]),
#         })

#     @http.route('/cambio_presentacion/cambio_presentacion/objects/<model("cambio_presentacion.cambio_presentacion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cambio_presentacion.object', {
#             'object': obj
#         })
