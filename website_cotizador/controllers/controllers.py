# -*- coding: utf-8 -*-
from datetime import date
from odoo import http, fields, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv import expression
from odoo.addons.portal.controllers.portal import CustomerPortal #, pager as portal_pager, get_records_page

class WebsiteCotizador(CustomerPortal):

    @http.route('/cliente/cotizacion/<int:order_id>', type='http', auth='public', website=True)
    def cliente_cotizacion(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        # SaleOrder = request.env['sale.order']
        # qs = SaleOrder.search([])
        # for q in qs:
        #     print(dir(q))
        #quotation = SaleOrder.search([("order_id","=",str(order_id))])
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

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
            'focus': order_sudo.order_line[0]
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                                                     (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total, order_sudo.currency_id, order_sudo.partner_id.country_id.id)

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        #values.update(get_records_pager(history, order_sudo))

        return request.render('website_cotizador.index', values)
        #return http.request.render('cotizacion.index')

    @http.route('/sitio/prueba/', type='http', auth='public', website=True)
    def sitio_prueba(self, **kw):
        
        return request.render('website_cotizador.presentacion')

#     @http.route('/website_cotizador/website_cotizador/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('website_cotizador.listing', {
#             'root': '/website_cotizador/website_cotizador',
#             'objects': http.request.env['website_cotizador.website_cotizador'].search([]),
#         })

#     @http.route('/website_cotizador/website_cotizador/objects/<model("website_cotizador.website_cotizador"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('website_cotizador.object', {
#             'object': obj
#         })
