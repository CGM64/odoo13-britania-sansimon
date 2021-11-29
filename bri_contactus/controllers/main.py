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
#from odoo.addons.base.models.ir_attachment import IrAttachment

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

        company = request.env.company
        
        values = {
            'medios': lista_medio,
            'depto' : lista_dp,
            'fleet' : lista_fleet,
            'medio_c' : lista_medios_c,
            'name': company.name,
            'phone': company.phone,
        }

        return request.render("bri_contactus.bri_contactenos", values)

    @http.route('/website_form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        return_value = super(WebsiteForm, self).website_form(model_name, **kwargs)
        #print("########################################## PRINT")
        #print(return_value)
        #print(type(return_value))
        ## print(return_value.read().decode('utf-8'))
        #rs = return_value.decode('utf-8')
        #print(rs)
        #j = json.loads(return_value)
        #print(j)
        template = request.env.ref('bri_contactus.confirmate_data_user_email')
        if template:
            model_record = request.env['ir.model'].sudo().search([('model','=',model_name),('website_form_access','=',True)])
            if model_record and hasattr(request.env[model_name], 'phone_format'):
                try:
                    data = self.extract_data(model_record, request.params)
                except:
                    pass
                else:
                    # print(data)
                    record = data.get('record', {})
                    company = request.env.company
                    print(company.id)
                    '''
                        ## RECORDATORIO ##
                        Obtener la oportunidad de una manera mas eficiente
                    '''
                    # Token en la oportunidad
                    leads = request.env["crm.lead"].sudo()
                    lead = leads.search([
                        ("contact_name", "=", record.get('contact_name')),
                        ("email_from", "=", record.get('email_from')),
                        ("type", "=", record.get('type')),
                        ("phone", "=", record.get('phone')),
                        ("won_status", "=", 'pending'),
                        ("medio_conocio", "=", record.get('medio_conocio')),
                        ("modelo", "=", record.get('modelo')),
                        ("medio_contacto", "=", record.get('medio_contacto')),
                    ])

                    lead.write({'opp_token': leads._generate_token()})
                    
                    # Envio de correos
                    #mail_body = request.env['mail.thread']._replace_local_links(render_template)
                    email = request.env['ir.mail_server'].sudo().search([('name','=','correo.contacto')])
                    
                    mail_values = {
                        #'email_from': request.env.user.email_formatted,
                        'email_from': email.smtp_user,
                    }
                    template.write(mail_values)
                    template.with_context().send_mail(lead.id, force_send=True, raise_exception=True)
                    lead.message_post(subject="Correo de confirmación enviado", body="Envío de correo de confirmación de datos validos")
                    pass
        
        return return_value #super(WebsiteForm, self).website_form(model_name, **kwargs)

    @http.route('/lead_verify/', type='http', auth="public", methods=['GET'], website=True)
    def lead_verify(self, *args):
        leads = request.env["crm.lead"].sudo()
        lead = leads.search([
            ("opp_token", "=", request.params.get('token')),
        ])
        if lead:
            lead.write({ "opp_token": 'COMPLETED'})
            lead.message_post(subject="Confirmación recibida", body="Confirmación de datos validos por parte del cliente")
        #lead.message_post(subject="Confirmación recibida", body="Confirmación de datos validos por parte del cliente")
        return request.render("bri_contactus.validation_page")
