# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from random import randint

from odoo import fields, models, api


class FleetModelRepair(models.Model):
    _name = "fleet.model.repair"
    _description = "Mano de obra para los modelos."

    labour_time = fields.Float(string='Tiempo')

    year_id = fields.Many2one('fleet.model.year', string='Año del modelo')
    model_id = fields.Many2one('fleet.vehicle.model', string='Modelo')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(string='Nombre')


    _sql_constraints = [
        ('name_uniq', 'unique (year_id, model_id, product_id)', "Ya existe un registro con este codigo."),
    ]

class FleetModelYear(models.Model):
    _name = "fleet.model.year"
    _description = "Model Year."

    name = fields.Char('Año del modelo', required=True, translate=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este año."),
    ]

