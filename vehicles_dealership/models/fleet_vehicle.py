# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

"""Fleet Vehicle and products models."""

from odoo import api, fields, models

class CodigoMarca(models.Model):
    """Fleet Vehicle model."""

    _name = 'codigo.marca'
    _description = 'Codigo Marca Vehiculo'
    name = fields.Char(string='Codigo de Marca',copy=False)

class FleetVehicle(models.Model):
    """Fleet Vehicle model."""

    _inherit = 'fleet.vehicle.model'
    codigo = fields.Char(string="Codigo")

class FleetVehicle(models.Model):
    """Fleet Vehicle model."""

    _inherit = 'fleet.vehicle'
    _inherits = {'product.product': 'product_id'}
    currency_id = fields.Many2one('res.currency',string="Moneda",readonly=False,related='')

    product_id = fields.Many2one('product.product', 'Product Vehicle',
                                 ondelete="cascade", delegate=True,
                                 required=True)
    image_128 = fields.Image(string="Image Small", readonly=False)
    tonelaje = fields.Char(string='Tonelaje',copy=True)
    tipo_vehiculo = fields.Selection([
        ('motocicleta','Motocilceta'),
        ('automovil','Automovil'),
        ('camion','Camion'),
        ('Camioneta','Camioneta'),
        ('cuatrimoto','Cuatrimoto'),
        ('rustico','Vehículo Rustico')],string="Tipo vehiculo",default='motocicleta')
    aduana = fields.Char(string='Aduana',copy=True)
    poliza = fields.Char(string='DUCA',copy=True)
    cilindros = fields.Char(string='Cilindros',copy=False)
    chasis = fields.Char(string='Chasis',copy=True)
    cc = fields.Char(string='C.C.',copy=True,help='Cilindrada total de motor')
    ejes = fields.Char(string='Ejes',copy=True,help='Ejes')
    motor = fields.Char(string='Motor',copy=True,help='Motor')
    codigo_marca = fields.Many2one('codigo.marca', 'Codigo de marca',
                                 ondelete="cascade", delegate=True,
                                 required=True,copy=True)
    pedido = fields.Char(string='No. Pedido',required=False,copy=True)


    @api.model
    def create(self, vals):
        """Overrridden method to update the product information."""
        ctx = dict(self.env.context)
        new_vehicle = super(FleetVehicle, self.with_context(create_fleet_vehicle=True)).create(vals)
        ctx.update({"from_vehicle_create": True})

        if new_vehicle.product_id:
            new_vehicle.product_id.with_context(ctx).write({
                'name': new_vehicle.name,
                'image_1920': new_vehicle.image_1920,
                'is_vehicle': True,
                'default_code':new_vehicle.pedido})
            new_vehicle.product_id.product_tmpl_id.write({'is_vehicle': True})
        return new_vehicle

    def write(self, vals):
        """Overrridden method to update the product information."""
        ctx = dict(self.env.context)
        res = super(FleetVehicle, self).write(vals)
        update_prod_vals = {}
        ctx.update({"from_vehicle_write": True})

        for vehicle in self:
            if vehicle.product_id:
                if vehicle.product_id.default_code != vehicle.pedido:
                    vehicle.product_id.default_code = vehicle.pedido
                if vals.get('image_1920', False):
                    update_prod_vals.update({'image_1920': vehicle.image_1920})
                if vals.get('model_id', False) or vals.get('license_plate', False):
                    update_prod_vals.update({'name': vehicle.name})
                if update_prod_vals:
                    vehicle.product_id.with_context(ctx).write(update_prod_vals)
        return res



