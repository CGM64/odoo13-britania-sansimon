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
    price_mar = fields.Float(string="Marítimo", compute="_precio_mar")
    price_aer = fields.Float(string="Aéreo", compute="_precio_aer")
    price_cour = fields.Float(string="Courier", compute="_precio_cour")

    @api.depends('group.group_uti', 'standard_price')
    def _precio_mar(self):
        
        for product in self:
            nacionalizacion = 0
            nacionalizacion = 20 / 100 * product.standard_price
            
            if product.group:
                if product.group.group_uti:
                    group_uti = product.group.group_uti.porcentaje / 100 * product.standard_price
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.update({
                'price_mar': product.standard_price+nacionalizacion+group_uti
            })

    @api.depends('group.group_uti', 'standard_price')
    def _precio_aer(self):
        
        for product in self:
            nacionalizacion = 0
            nacionalizacion = 30 / 100 * product.standard_price
            
            if product.group:
                if product.group.group_uti:
                    group_uti = product.group.group_uti.porcentaje / 100 * product.standard_price
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.update({
                'price_aer': product.standard_price+nacionalizacion+group_uti
            })

    @api.depends('group.group_uti', 'standard_price')
    def _precio_cour(self):
        
        for product in self:
            nacionalizacion = 0
            nacionalizacion = 40 / 100 * product.standard_price
            
            if product.group:
                if product.group.group_uti:
                    group_uti = product.group.group_uti.porcentaje / 100 * product.standard_price
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.update({
                'price_cour': product.standard_price+nacionalizacion+group_uti
            })

    _sql_constraints = [
        ('name_uniq', 'unique (default_code)', "Ya existe un registro con estos datos."),
    ]

    def create_product(self):
        tri_group = self.env['tri.product.group'].search([('id','=',self.group.id)], limit=1)
        product = self.env['product.product'].create({
            "name": self.name,
            "sale_ok": True,
            "purchase_ok": True,
            "categ_id": 12,
            "type": "product",
            "default_code": self.default_code,
            "grupo_utilidad_id": tri_group.group_uti.id,
            "marca_id": 1,
            "standard_price": self.standard_price,
            "list_price": self.price_mar,
        })