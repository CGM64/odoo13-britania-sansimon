# -*- coding: utf-8 -*-
{
    'name': "cambio_presentacion",

    'summary': """
        Cambiar Presentación""",

    'description': """
        Cambia la presentación de un producto a otro.
        Puede cambiarse de un tamño a otro.
        Ej: Tonel <- Galón -> Litro.
    """,

    'author': "Integratec",
    'website': "http://www.integratec.com.gt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','report_xlsx','stock',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/conversion_producto_data.xml', 
        'data/conversion_producto_sequence.xml',

        'views/product_template_inherit.xml',
        'views/conversion_producto_views.xml',
        'report/conversion_producto_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
