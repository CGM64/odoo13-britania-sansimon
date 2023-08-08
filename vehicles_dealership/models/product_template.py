# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

class ProductTemplate(models.Model):
    
    _inherit = 'product.template'

    model_ids = fields.Many2many('fleet.vehicle.model', string='Modelos', help="Modelos para la asignacion de producto.")
    is_vehicle = fields.Boolean(string="Vehiculo")
    vehicle_product_qty = fields.Float(compute='_compute_vehicle_product_qty', string='Vehiculos')

    chasis = fields.Char(string='Chasis', defult="_compute_chasis", search=True)

    def _compute_chasis(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.chasis = template.product_variant_ids.chasis
            return template.product_variant_ids.chasis
        for template in (self - unique_variants):
            template.chasis = False

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

    chasis = fields.Char(string="Chasis", defult="_compute_chasis", search=True)

    def _compute_chasis(self):
        for product in self:
            vehiculo = self.env['fleet.vehicle'].sudo().search([('product_id','=',product.id)])
            if vehiculo:
                product.chasis = vehiculo.chasis
                #return vehiculo.chasis

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
    
    # FUNCION PARA QUE SE PUEDA BUSCAR CON EL CAMPO CHASIS
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
                if not product_ids:
                    product_ids = self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = self._search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = self._search([('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, access_rights_uid=name_get_uid)
            
            # IF que sirve si en dado caso no hay conincidiendencias anteriores, busque en chasis
            if not product_ids:
                product_ids = self._search([("chasis",'ilike',name)], limit=limit, access_rights_uid=name_get_uid)
            

        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))
