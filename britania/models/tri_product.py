# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class TriProductGroup(models.Model):
    _name = "tri.product.group"
    _description = "Grupos"

    name = fields.Char('Grupo', required=True)
    group_uti = fields.Many2one('product.grupoutilidad', string='Grupo de utilidad')
    product_category = fields.Many2one('product.category', string='Categoria del producto')

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
    price_mar = fields.Float(string="Marítimo", compute="_precios_compute")
    price_aer = fields.Float(string="Aéreo", compute="_precios_compute")
    price_cour = fields.Float(string="Courier", compute="_precios_compute")

    _sql_constraints = [
        ('name_uniq', 'unique (default_code)', "Ya existe un registro con estos datos."),
    ]

    def calcular_totales(self, porcentaje, precio_standard, group):
        nacionalizacion = porcentaje / 100 * precio_standard
        total = precio_standard+nacionalizacion+group
        return total

    @api.depends('group.group_uti', 'standard_price')
    def _precios_compute(self):
        
        for product in self:
            
            if product.group:
                if product.group.group_uti:
                    group_uti = product.group.group_uti.porcentaje / 100 * product.standard_price
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.price_mar = self.calcular_totales(20, product.standard_price, group_uti)
            product.price_aer = self.calcular_totales(30, product.standard_price, group_uti)
            product.price_cour = self.calcular_totales(40, product.standard_price, group_uti)

    def create_product(self):
        tri_group = self.env['tri.product.group'].search([('id','=',self.group.id)], limit=1)
        product = self.env['product.product'].create({
            "name": self.name,
            "sale_ok": True,
            "purchase_ok": True,
            "categ_id": tri_group.product_category.id,
            "type": "product",
            "default_code": self.default_code,
            "grupo_utilidad_id": tri_group.group_uti.id,
            "marca_id": 1,
            "standard_price": 0.00,
            "list_price": self.price_mar,
        })