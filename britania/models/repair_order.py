# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class repairOrder(models.Model):
    _inherit = "repair.order"
    
    tipo_orden = fields.Many2one('repair.type', 'Tipo de orden', index=True)

    def update_detail(self, search=''):

        Fleet = request.env['fleet.vehicle']
        lista_fleet = Fleet.search([('product_tmpl_id', '=',self.product_id.id)], limit=1)

        for i in self.fees_lines:
            product = request.env['fleet.model.repair']
            lista_product = product.search([('model_id', '=', lista_fleet.model_id.id),('product_id','=',i.product_id.id)], limit=1)

            if lista_product.labour_time != 0.0:
                if i.product_uom_qty > 1.0 :
                    i.product_uom_qty = i.product_uom_qty
                else:
                    i.product_uom_qty = lista_product.labour_time

class RepairFee(models.Model):
    _inherit = "repair.fee"

    amount_total = fields.Float(string="Total", compute="_get_amount_total")

    def _get_amount_total(self):
        for fee in self:
            fee.amount_total = fee.price_unit * fee.product_uom_qty

class RepairLine(models.Model):
    _inherit = "repair.line"

    amount_total = fields.Float(string="Total", compute="_get_amount_total")

    def _get_amount_total(self):
        for line in self:
            line.amount_total = line.price_unit * line.product_uom_qty

class RepairType(models.Model):
    _name = "repair.type"
    _description = "Tipos de ordenes de reparación"

    name = fields.Char('Tipo de orden', required=True)
    default_type = fields.Boolean(string="Tipo de orden por defecto", help="Tipo de orden por defecto")

    @api.onchange('default_type')
    def _check_unique_nit(self):
        tipos = request.env['repair.type'].search([('default_type', '=', True)])
        for i in tipos:
            if i.id == self.id:
                pass
            else:
                i.update({
                    'default_type': False,
                })
        
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Conversión.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre!"),
    ]

class Repair(models.Model):
    _inherit = "repair.order"

    def _default_type(self):
        return self.env['repair.type'].search([('default_type', '=', True)], limit=1).id
    
    tipo_orden = fields.Many2one('repair.type', 'Tipo de orden', index=True, default=_default_type)

