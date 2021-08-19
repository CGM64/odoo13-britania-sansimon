# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class TriProductGroup(models.Model):
    _name = "tri.product.group"
    _description = "Grupos"

    name = fields.Char('Grupo', required=True)
    group_uti = fields.Many2one('product.grupoutilidad', string='Grupo de utilidad')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre."),
    ]

class TriProduct(models.Model):
    _name = "tri.product"
    _description = "Productos Triumph."

    name = fields.Char('Nombre del producto', required=True)
    default_code = fields.Char('Referencia interna', required=True)
    standard_price = fields.Float(string="Precio")
    group = fields.Many2one('tri.product.group', string='Grupo')
    nacionalizacion = fields.Selection(selection=[
        ('mar','Marítimo'),
        ('aer','Aéreo'),
        ('cour','Courier'),
        ], string='Medio de transporte', help='Nacionalización')
    
    price = fields.Float(string="Precio de venta", compute="_precio_total")

    @api.depends('group.group_uti', 'standard_price', 'nacionalizacion')
    def _precio_total(self):
        
        for product in self:
            nacionalizacion = 0
            if product.nacionalizacion == 'mar':
                nacionalizacion = 20 / 100 * product.standard_price
            elif product.nacionalizacion == 'aer':
                nacionalizacion = 30 / 100 * product.standard_price
            elif product.nacionalizacion == 'cour':
                nacionalizacion = 40 / 100 * product.standard_price
            
            if product.group:
                if product.group.group_uti:
                    group_uti = product.group.group_uti.porcentaje / 100 * product.standard_price
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.update({
                'price': product.standard_price+nacionalizacion+group_uti
            })

    _sql_constraints = [
        ('name_uniq', 'unique (default_code)', "Ya existe un registro con estos datos."),
    ]