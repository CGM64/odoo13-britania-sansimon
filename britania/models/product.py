# -*- coding: utf-8 -*-
from odoo import models ,fields , api
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

class ProductProduct(models.Model):
    _inherit = 'product.product'

    chasis = fields.Char(string="Chasis", search=True)

class ProductProduct(models.Model):
    _inherit = 'product.template'

    chasis = fields.Char(
        'Chasis', compute='_compute_chasis',
        inverse='_set_chasis', store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.chasis')
    def _compute_chasis(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.chasis = template.product_variant_ids.chasis
        for template in (self - unique_variants):
            template.chasis = False
    
    def _set_chasis(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.chasis = template.chasis