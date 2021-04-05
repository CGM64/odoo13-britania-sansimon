# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from datetime import datetime
from werkzeug.exceptions import Forbidden, NotFound

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression

class WebsiteSale(http.Controller):

    @http.route(
        [
            '''/contact_prueba'''
        ],type='http',auth="public",website=True)
    def britcontactenos(self,page=0, category=None, search='', ppg=False, **post):

        Product = request.env['product.template']
        lista_product = Product.search([])

        ProductAttribute = request.env['product.attribute']
        lista_attribute = ProductAttribute.search([])

        Category = request.env['product.public.category']
        lista_cat = Category.search([])

        values = {
            'var_prueba': "¡Hola mundo!",
            'products': lista_product,
            'attrib' : lista_attribute,
            'categorias' : lista_cat,
        }

        return request.render("bri_contactus.bri_contactenos", values)