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
        'social_media',
        'auth_signup',
        'website', 'sale', 'website_payment', 'website_mail', 'website_form', 'website_rating', 'digest'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/website_sale.xml',
        'data/data.xml',
        'data/mail_template_data.xml',
        'data/digest_data.xml',
        'views/product_views.xml',
        'views/account_views.xml',
        'views/onboarding_views.xml',
        'views/sale_report_views.xml',
        'views/sale_order_views.xml',
        'views/crm_team_views.xml',
        'views/templates.xml',
        'views/snippets.xml',
        'views/res_config_settings_views.xml',
        'views/digest_views.xml',
        'views/website_sale_visitor_views.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
    'data': [
        'views/contact_page.xml',
    ],
   
    'application': True,
}