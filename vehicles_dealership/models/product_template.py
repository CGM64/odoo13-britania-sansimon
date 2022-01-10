# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    
    _inherit = 'product.template'

    model_ids = fields.Many2many('fleet.vehicle.model', string='Modelos', help="Modelos para la asignacion de producto.")
    is_vehicle = fields.Boolean(string="Vehiculo")
    vehicle_product_qty = fields.Float(compute='_compute_vehicle_product_qty', string='Vehiculos')

    def _compute_vehicle_product_qty(self):
        for template in self:
            product_product = self.env['product.product'].search([('product_tmpl_id','=',template.id)])
            product_ids = [ product_id.id for product_id in product_product]
            vehicles = self.env['fleet.vehicle'].search([('product_id','in',product_ids)])            
            template.vehicle_product_qty = sum([1 for p in vehicles])

    @api.model
    def _get_action_view_related_vehicle(self, domain):
        return {
            'name': _('Vehicle Rules'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle',
            'view_mode': 'tree,form',
            'domain': domain,
        }

    def action_view_vehiculos(self):
        self.ensure_one()
        product_product = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        products = [product_id.id for product_id in product_product]
        domain = [
                ('product_id', 'in', products),
        ]
        return self._get_action_view_related_vehicle(domain)
            

class ProductProduct(models.Model):
    """Product model."""

    _inherit = 'product.product'

    is_vehicle = fields.Boolean(string="Vehicle")

    @api.model
    def create(self, vals):
        """Overrridden method to update the product information."""
        if not vals.get('name', False) and self._context.get('create_fleet_vehicle', False):
            vals.update({'name': 'NEW VEHICLE',
                         'type': 'product',
                         'is_vehicle': True})

        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        """Overrridden method to update the vehicle information."""
        ctx = dict(self.env.context)
        res = super(ProductProduct, self).write(vals)

        for product in self:
            if ctx and not ctx.get("from_vehicle_create", False) and not ctx.get("from_vehicle_write", False):
                vehicles = self.env['fleet.vehicle'].search([('product_id', '=', product.id)])
                update_vehicle_vals = {}
                if vals.get('image_1920', False):
                    update_vehicle_vals.update({'image_1920': product.image_1920})
                if vals.get('name', False):
                    update_vehicle_vals.update({'name': product.name})
                if update_vehicle_vals and vehicles:
                    for vehicle in vehicles:
                        vehicle.write(update_vehicle_vals)
        return res
