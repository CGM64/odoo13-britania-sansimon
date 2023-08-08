# -*- coding: utf-8 -*-
# from odoo import http


# class UpdateListprice(http.Controller):
#     @http.route('/update_listprice/update_listprice/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/update_listprice/update_listprice/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('update_listprice.listing', {
#             'root': '/update_listprice/update_listprice',
#             'objects': http.request.env['update_listprice.update_listprice'].search([]),
#         })

#     @http.route('/update_listprice/update_listprice/objects/<model("update_listprice.update_listprice"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('update_listprice.object', {
#             'object': obj
#         })
