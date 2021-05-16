# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    model_ids = fields.Many2many('fleet.vehicle.model', string='Modelos', help="Modelos para la asignacion de producto.")
