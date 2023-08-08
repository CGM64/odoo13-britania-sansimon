# -*- coding: utf-8 -*-
from odoo import http

# class CurrencyUpdateRate(http.Controller):
#     @http.route('/currency_update_rate/currency_update_rate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/currency_update_rate/currency_update_rate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('currency_update_rate.listing', {
#             'root': '/currency_update_rate/currency_update_rate',
#             'objects': http.request.env['currency_update_rate.currency_update_rate'].search([]),
#         })

#     @http.route('/currency_update_rate/currency_update_rate/objects/<model("currency_update_rate.currency_update_rate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('currency_update_rate.object', {
#             'object': obj
#         })