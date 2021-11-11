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
from odoo.addons.website_crm.controllers.main import WebsiteForm
from odoo.tools import ustr, pycompat

class WebsiteSale(WebsiteForm):

    @http.route(
        [
            '''/contactanos'''
        ],type='http',auth="public",website=True)
    def britcontactenos(self,page=0, category=None, search='', ppg=False, **post):

        #Se declara el nombre del objeto 'Fleet' junto con que modelo pertenece.
        Fleet = request.env['fleet.vehicle.model']
        #Se llena la lista 'lista_fleet' y con el modelo declarado previemante 'Fleet' con search
        lista_fleet = Fleet.sudo().search([('brand_id', '=',67),('is_publish','=',True)])

        Medio = request.env['utm.medium']
        lista_medio = Medio.sudo().search([])

        Departamentos =  request.env['res.country.state']
        lista_dp = Departamentos.sudo().search([('country_id','=',90)])

        medio_c =  request.env['crm.medio.contacto']
        lista_medios_c = medio_c.sudo().search([])

        values = {
            'medios': lista_medio,
            'depto' : lista_dp,
            'fleet' : lista_fleet,
            'medio_c' : lista_medios_c,
        }

        return request.render("bri_contactus.bri_contactenos", values)

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        #super(WebsiteForm, self).website_form(model_name, **kwargs)

        template = request.env.ref('bri_contactus.mail_template_cotizacion')
        print("TEMPLATE**********************************")
        print(template)
        if template:
            model_record = request.env['ir.model'].sudo().search([('model','=',model_name),('website_form_access','=',True)])
            if model_record and hasattr(request.env[model_name], 'phone_format'):
                try:
                    data = self.extract_data(model_record, request.params)
                except:
                    pass
                else:
                    #print(data)
                    record = data.get('record', {})
                    company = request.env['res.company'].sudo().search([])
                    #print("COMPANY***************",company)
                    Fleet = request.env['fleet.vehicle.model']
                    fleet = Fleet.sudo().search([('brand_id', '=',67),('is_publish','=',True), ('id','=',record.get('modelo'))])
                    render_template = template.render({
                        'contact_name': record.get('contact_name'),
                        'company_name': company[0].name,
                        'product_name': fleet.name,
                    }, engine='ir.qweb')
                    #mail_body = request.env['mail.thread']._replace_local_links(render_template)
                    email = request.env['ir.mail_server'].sudo().search([('name','=','pruebas')])
                    print(email.smtp_user)
                    mail_values = {
                        'body_html': render_template,# mail_body,
                        'subject': _('Confirmación de la cotización.'),
                        'email_from': email.smtp_user,
                        'email_to': record.get('email_from')
                    }
                    request.env['mail.mail'].sudo().create(mail_values).send()
                    #print("***********************ACA ES**************************")
                    pass
        
        return super(WebsiteForm, self).website_form(model_name, **kwargs)
