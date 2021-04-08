# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Formulario de contacto',
    'category': 'Website/Website',
    'summary': 'Formulario de contacto(prueba)',
    'version': '1.0',
    'description': "Prueba formulario de contacto",
    'depends': [
        'web',
        'web_editor',
        'http_routing',
        'portal',
        'crm',
        'social_media',
        'auth_signup',
        'website', 'sale', 'website_payment', 'website_mail', 'website_form', 'website_rating', 'digest',
    ],
    'data': [
        'views/contact_page.xml',
        'views/crm_lead_view.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
