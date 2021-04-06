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
from odoo import api, models

class LineaVehicle(models.Model):
    """Fleet Vehicle model."""

    _name = 'linea.vehicle'
    name = fields.Char(string='Linea',copy=False)

class CodigoMarca(models.Model):
    """Fleet Vehicle model."""

    _name = 'codigo.marca'
    name = fields.Char(string='Codigo de Marca',copy=False)

class WebsiteSale(http.Controller):

    @http.route(
        [
            '''/contact_prueba'''
        ],type='http',auth="public",website=True)
    def britcontactenos(self,page=0, category=None, search='', ppg=False, **post):

        Fleet = request.env['fleet.vehicle.model']
        lista_fleet = Fleet.search([('brand_id', '=',67)])

        Medio = request.env['utm.medium']
        lista_medio = Medio.search([])

        Departamentos =  request.env['res.country.state']
        lista_dp = Departamentos.search([('country_id','=',90)])

        values = {
            'medios': lista_medio,
            'depto' : lista_dp,
            'fleet' : lista_fleet,
        }

        return request.render("bri_contactus.bri_contactenos", values)
