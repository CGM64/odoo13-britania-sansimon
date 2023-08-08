# -*- coding: utf-8 -*-
{
    'name': "Tasa de cambio banco de Guatemala",

    'summary': """
        Modulo encargado de sincronizar la tasa de cambio con el banco de Guatemala""",

    'description': """
        Actualiza la tasa de cambio de USD
    """,

    'author': "Integratec S.A.",
    'website': "http://www.integratec.com.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/cron_update_currency_rate.xml',
        'views/res_company.xml',
        'views/res_currency_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
