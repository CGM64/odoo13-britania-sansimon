# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
           
class RepairType(models.Model):
    _name = "repair.type"
    _description = "Tipos de ordenes de reparación"

    name = fields.Char('Tipo de orden', required=True)
    sequence = fields.Integer(help='Used to order repair types in the dashboard view', default=10)
    active = fields.Boolean(string ="Activo",default=True, help="Activa o desctiva tipos de orden")
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Conversión.")
    
    @api.onchange('active')
    def _update_active(self):
        return

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre!"),
    ]

class repairOrder(models.Model):
    _inherit = "repair.order"

    @api.model
    def _get_default(self):
        type = self.env['repair.type'].search([('active', '=',True)])
        tipos = []
        if type:
            for tipo in type:
                tipos.append(tipo.sequence)
            minimo = min(tipos)
            t = self.env['repair.type'].search([('sequence', '=',minimo)]).id
            return t
        else:
            return
    
    tipo_orden = fields.Many2one('repair.type', 'Tipo de orden', index=True, default=_get_default)

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