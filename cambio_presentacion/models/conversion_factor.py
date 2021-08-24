# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp


class ConversionFactor(models.Model):
    _name = "conversion.factor"
    _description = "Factor"

    conversion_factor_id = fields.Many2one('product.template', string='Linea Detalle')

    product_id = fields.Many2one('product.template', string='Artículo')

    factor_id = fields.Selection([
        ('bigger', 'Bigger than the reference Unit of Measure'),
        ('reference', 'Reference Unit of Measure for this category'),
        ('smaller', 'Smaller than the reference Unit of Measure')], string='Tipo',
        default='reference', required=1)

    factor_amount = fields.Float(string="Factor")

    _sql_constraints = [('factor_zero', 'CHECK (factor!=0)',
                         'The conversion factor cannot be 0!'), ]
                
class ProductTemplateInherit(models.Model):
    _inherit = "product.template"

    conversion_factor_ids = fields.One2many('conversion.factor', 'conversion_factor_id', 'Factor', copy=True)
        


