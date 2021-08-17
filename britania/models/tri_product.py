# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class TriProductGroup(models.Model):
    _name = "tri.product.group"
    _description = "Grupos"

    name = fields.Char('Grupo', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre."),
    ]

class TriProduct(models.Model):
    _name = "tri.product"
    _description = "Productos Triumph."

    name = fields.Char('Nombre del producto', required=True)
    default_code = fields.Char('Referencia interna', required=True)
    price = fields.Float(string="Precio")
    group = fields.Many2one('tri.product.group', string='Grupo')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con estos datos."),
    ]