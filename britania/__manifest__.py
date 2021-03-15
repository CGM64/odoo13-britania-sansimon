# -*- coding: utf-8 -*-
{
    'name': "britania",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Integratec",
    'website': "http://www.integratec.com.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #'data/account_chart_template_data.xml',
        #'data/product_dai_data.xml',
        'report/reporte_invoice.xml',
        'views/account_journal.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',

    ],
}
