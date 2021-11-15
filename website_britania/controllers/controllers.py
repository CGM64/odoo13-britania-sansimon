# -*- coding: utf-8 -*-
# from odoo import http

from odoo import http

class WebsiteBritania(http.Controller):
    
    @http.route('/sitio/prueba/', type='http', auth='public', website=True)
    def sitio_prueba(self, **kw):
        
        return http.request.render('website_britania.presentacion')
