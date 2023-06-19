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


class FleetVehicle(models.Model):
    """Fleet Vehicle model."""

    _inherit = 'fleet.vehicle'

    def actualizar_ficha_vehiculos(self):
        vehiculos = self.env["fleet.vehicle"].sudo().search([])
        for vehiculo in vehiculos:
            if vehiculo.product_id:
                vehiculo.product_id.chasis = vehiculo.chasis
                vehiculo.product_id.product_tmpl_id._compute_chasis()
    
    @api.onchange('chasis')
    def _onchangechasis(self):
        for vehiculo in self:
            if vehiculo.product_id:
                vehiculo.product_id.chasis = vehiculo.chasis
                vehiculo.product_id.product_tmpl_id._compute_chasis()
        pass

    # @api.model
    # def create(self, vals):
    #     print("$$$$$$$")
    #     print("$$$$$$$")
    #     print("$$$$$$$")
    #     print("$$$$$$$")
    #     print(vals)
    #     res = super(FleetVehicle, self).create(vals)
    #     print(vals.get('chasis', False))
    #     print(self.product_id)
    #     if vals.get('chasis', False):
    #         if self.product_id:
    #             self.product_id.chasis = self.chasis
    #             self.product_id.product_tmpl_id._compute_chasis()
    #     return res
    
    def write(self, vals):
        res = super(FleetVehicle, self).write(vals)
        if vals.get('chasis', False):
            if self.product_id:
                self.product_id.chasis = self.chasis
                self.product_id.product_tmpl_id._compute_chasis()
        return res