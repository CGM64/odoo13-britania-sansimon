# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Britania formulario de contacto',
    'author': "Integratec",
    'category': 'Website',
    'summary': 'Formulario de contacto',
    'version': '1.0',
    'description': "Modulo para el formulario de contacto Britania",
    'depends': [
        'web',
        'web_editor',
        'http_routing',
        'portal',
        'crm',
        'social_media',
        'auth_signup',
        'website', 'sale', 'website_payment', 'website_mail', 'website_form', 'website_rating', 'digest','britania',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/britania_email_data.xml',
        'views/contact_page.xml',
        'views/crm_lead_view.xml',
        'data/britania_crm_data.xml',
        'views/website_view.xml',
        'views/crm_views.xml',
        'data/crm_medio_data.xml',

        'views/validation_page.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'application': True,
}
