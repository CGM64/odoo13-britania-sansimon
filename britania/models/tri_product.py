# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class TriProductGroup(models.Model):
    _name = "tri.product.group"
    _description = "Grupos"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Grupo', required=True,tracking=1)
    group_uti = fields.Many2one('product.grupoutilidad', string='Grupo de utilidad',tracking=1)
    product_category = fields.Many2one('product.category', string='Categoria del producto',tracking=1)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre."),
    ]

class TriProduct(models.Model):
    _name = "tri.product"
    _description = "Productos Triumph."
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre del producto', required=True)
    default_code = fields.Char('Referencia interna', required=True)
    standard_price = fields.Float(string="Precio",tracking=1)
    group = fields.Many2one('tri.product.group', string='Grupo')
    price_mar = fields.Float(string="Marítimo", compute="_precios_compute",tracking=True)
    price_aer = fields.Float(string="Aéreo", compute="_precios_compute",tracking=True)
    price_cour = fields.Float(string="Courier", compute="_precios_compute",tracking=True)
    product_template = fields.Many2one('product.template', string='Producto en inventario Odoo')
    #CAMPO PARA SABER SI ESTA CREADO EN PRODUCT.PRODUCT
    is_created = fields.Boolean(default=False)

    _sql_constraints = [
        ('name_uniq', 'unique (default_code)', "Ya existe un registro con estos datos."),
    ]

    @api.depends('group.group_uti', 'standard_price')
    def _precios_compute(self):

        maritimo_porc = 120
        aereo_porc = 130
        courier_porc = 220
        
        for product in self:
            
            if product.group:
                if product.group.group_uti:
                    group_uti = (product.group.group_uti.porcentaje / 100)+1
                else:
                    group_uti = 0
            else:
                group_uti = 0
            
            product.price_mar = self.calcular_totales(maritimo_porc, product.standard_price, group_uti)
            product.price_aer = self.calcular_totales(aereo_porc, product.standard_price, group_uti)
            product.price_cour = self.calcular_totales(courier_porc, product.standard_price, group_uti)

    def calcular_totales(self, porcentaje, precio_standard, group):
        #TASA DE CAMBIO
        tasa_cambio = self.env['res.currency'].search([('name','=','USV')], limit=1)
        nacionalizacion = (porcentaje / 100)
        totales = precio_standard*tasa_cambio.tipo_cambio*nacionalizacion*group
        iva = (12 / 100)+1
        total = totales*iva
        return total

    def create_product(self):
        if not self.group.group_uti:
            raise ValidationError(_("El grupo de este producto no tiene asignado un grupo de utilidad."))
        #CREANDO PRODUCTO EN PRODUCT_PRODUCT
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
            "standard_price": self.standard_price,
            "list_price": self.price_mar,
        })
        product_product = self.env['product.template'].search([('name','=',self.name)], limit=1)
        self.update({
            'is_created': True,
            'product_template': product_product.id,
        })
        #LLAMADNDO METODO PARA CREAR PRODUCTO EN PRODUCT_PRICELIST_ITEM(TARIFA)
        self.create_pricelist_line(self.name,tipo_tarifa="Maritimo")
        self.create_pricelist_line(self.name,tipo_tarifa="Aereo")
        self.create_pricelist_line(self.name,tipo_tarifa="Courier")

    #METODO PARA CREAR PRODUCTO EN PRODUCT PRODUCT
    def create_pricelist_line(self,name,tipo_tarifa):
        product_p = self.env['product.template'].search([('name','=',name)], limit=1)
        pricelist = self.env['product.pricelist'].search([('name','=',tipo_tarifa)], limit=1)
        if tipo_tarifa == "Maritimo":
            price = self.price_mar
        elif tipo_tarifa == "Aereo":
            price = self.price_aer
        elif tipo_tarifa == "Courier":
            price = self.price_cour
        product_pricelist = self.env['product.pricelist.item'].create({
            "pricelist_id": pricelist.id,
            "base": "list_price",
            "applied_on": "1_product",
            "product_tmpl_id": product_p.id,
            "currency_id": 170,
            "compute_price": "fixed",
            "fixed_price": price,
        })