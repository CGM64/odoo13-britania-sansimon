# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class repairOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    total_undiscounted = fields.Monetary(string="Total sin descuento", compute="_total_sin_descuento")

    @api.depends('price_subtotal')
    def _total_sin_descuento(self):
        
        for order in self:
            total = 0.0
            total = order.price_unit * order.product_uom_qty
            order.update({
                'total_undiscounted': total,
            })

class repairOrder(models.Model):
    _inherit = "sale.order"
    
    total_discount = fields.Monetary(string="Descuento", compute="_amount_discount")

    @api.depends('order_line.price_total')
    def _amount_discount(self):
        
        for order in self:
            total_desc = 0.0
            total = 0.0
            for line in order.order_line:
                total += line.total_undiscounted
                total_desc += line.price_subtotal
            order.update({
                'total_discount': total - order.amount_total,
            })