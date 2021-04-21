# -*- coding: utf-8 -*-
# from odoo import http


# class SolGasto(http.Controller):
#     @http.route('/sol_gasto/sol_gasto/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sol_gasto/sol_gasto/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sol_gasto.listing', {
#             'root': '/sol_gasto/sol_gasto',
#             'objects': http.request.env['sol_gasto.sol_gasto'].search([]),
#         })

#     @http.route('/sol_gasto/sol_gasto/objects/<model("sol_gasto.sol_gasto"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sol_gasto.object', {
#             'object': obj
#         })
