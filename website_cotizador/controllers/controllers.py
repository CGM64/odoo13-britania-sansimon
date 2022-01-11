# -*- coding: utf-8 -*-
from datetime import date
#import random

from odoo import http, fields, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv import expression
from odoo.addons.sale.controllers.portal import CustomerPortal #, pager as portal_pager, get_records_page



class WebsiteCotizador(CustomerPortal):

    @http.route('/my/orders/<int:order_id>', type='http', auth='public', methods=['GET'], website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        
        order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        
        if order_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_quote_%s' % order_sudo.id)
            if isinstance(session_obj_date, date):
                session_obj_date = session_obj_date.isoformat()
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_quote_%s' % order_sudo.id] = now
                body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
                _message_post_helper(
                    "sale.order",
                    order_sudo.id,
                    body,
                    token=order_sudo.access_token,
                    message_type="notification",
                    subtype="mail.mt_note",
                    partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                )
        company = request.env.company

        base_url = request.env ['ir.config_parameter'].sudo().get_param('web.base.url')

        producto = request.env["product.product"].sudo().search([
            ("product_tmpl_id", "=", order_sudo.order_line[0].product_id.product_tmpl_id.id)
        ])

        tarifa_dolar = ''
        tarifa_publica = ''
        signo_t_dolar = ''
        signo_t_publica = ''
        nombre_producto = order_sudo.order_line[0].product_id.name

        for price in producto[0].sale_pricelists:
            context = price._context.copy()
            context.update({'product_id' : producto.id})
            price.with_context(context)._get_product_price()
            if price.name == 'Tarifa en Dolares':
                tarifa_dolar = price.product_price.replace(' ', '')
                signo_t_dolar = price.product_price[0]
                tarifa_dolar = price.product_price.replace(signo_t_dolar, '')
            elif price.name == 'Tarifa pública':
                tarifa_publica = price.product_price.replace(' ', '')
                signo_t_publica = price.product_price[0]
                tarifa_publica = price.product_price.replace(signo_t_publica, '')
            #print(price.name, price.product_price)

        fleet_vehicle = request.env["fleet.vehicle"].sudo().search([
            ("product_id","=",producto[0].id)
        ])

        for fleet in fleet_vehicle:
            if fleet.model_id.id:
                fleet_vehicle = fleet
                break

        fleet_vehicle_model = False
        ficha_tecnica_url = '#'

        if fleet_vehicle.model_id.id:
            fleet_vehicle_model = request.env["fleet.vehicle.model"].sudo().search([
                ("id","=",fleet_vehicle[0].model_id.id)
            ])
            fleet_vehicle_model = fleet_vehicle_model[0]
            ficha_tecnica_url = '/web/binary/ficha_tecnica?model=fleet.vehicle.model&field=ficha_tecnica&id='+ str(fleet_vehicle_model[0].id)
        
        caracteristicas = []
        f_m_descripcion_vehiculo = ""
        f_m_titulo_vehiculo = ""
        if fleet_vehicle_model and fleet_vehicle_model[0].informacion:
            string_raw = fleet_vehicle_model[0].informacion
            if string_raw != "":
                temp_caracteristicas = string_raw.split("<nuevo>")
                for t in temp_caracteristicas:
                    if t != "":
                        c = t.split("<separador>")
                        if len(c) > 1:
                            caracteristicas.append({ "titulo": c[0], "descripcion": c[1] })
                        else:
                            caracteristicas.append({ "titulo": c[0], "descripcion": "" })
            
            if fleet_vehicle_model[0].descripcion_vehiculo:
                str_raw = fleet_vehicle_model[0].descripcion_vehiculo
                if string_raw != "":
                    temp_caracteristicas = str_raw.split("<separador>")
                    if len(temp_caracteristicas) == 2:
                        f_m_titulo_vehiculo = temp_caracteristicas[0]
                        f_m_descripcion_vehiculo = temp_caracteristicas[1]
        
        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'action': order_sudo._get_portal_return_action(),
            'focus': order_sudo.order_line[0],
            'fleet_vehicle': fleet_vehicle_model,
            'caracteristicas': caracteristicas,
            'ficha_tecnica_url': ficha_tecnica_url,
            'company_id': company,
            'base_url': base_url,
            'tarifa_dolar': tarifa_dolar,
            'signo_t_dolar': signo_t_dolar,
            'tarifa_publica': tarifa_publica,
            'signo_t_publica': signo_t_publica,
            'nombre_producto': nombre_producto,
            'f_m_descripcion_vehiculo': f_m_descripcion_vehiculo,
            'f_m_titulo_vehiculo': f_m_titulo_vehiculo
        }

        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        
        return request.render('website_cotizador.bri_view_cotizador',values)
        pass