# -*- coding: utf-8 -*-
{
    'name': "corte_caja",

    'summary': """
        Corte de Caja""",

    'description': """
        Aplicaicón para corte de caja.
    """,

    'author': "Integratec",
    'website': "http://www.integratec.com.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_corte_caja_view.xml',
        'sequence/corte_caja_sequence.xml',  

        'report/corte_caja_report_pdf.xml',  
        'report/account_payment_corte_caja_report_views.xml',       
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
