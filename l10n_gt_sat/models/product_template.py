# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductDai(models.Model):
    _name = 'product.dai'
    _description = 'Arancel'

    name = fields.Char(string='Codigo', required=True)
    descripcion = fields.Char(string='Descripcion', required=True)
    porcentaje = fields.Integer(string='Porcentaje', required=True)

class ProductGrupoUtilidad(models.Model):
    _name = 'product.grupoutilidad'
    _description = 'Arancel'

    name = fields.Char(string='Descripcion', required=True)
    porcentaje = fields.Integer(string='Porcentaje', required=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dai_id = fields.Many2one('product.dai', string='DAI', help='Select a DAI for this product')
    grupo_utilidad_id = fields.Many2one('product.grupoutilidad', string='Grupo de Utilidad')
