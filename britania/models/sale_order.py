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
    amount_total_undiscounted = fields.Monetary(string="Total sin descuento", compute="_amount_total_undiscounted")

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

    @api.depends('total_discount')
    def _amount_total_undiscounted(self):
        
        for order in self:
            total = 0.0
            if order.total_discount == 0.0:
                total = order.amount_total
            else:
                total = order.amount_total + order.total_discount
            order.update({
                'amount_total_undiscounted': total,
            })

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    total_undiscounted = fields.Monetary(string="Total sin descuento", compute="_total_sin_descuento")
    total_undiscounted_dl = fields.Monetary(string="Total sin descuento USD", compute="_total_sin_descuento_dl")

    @api.depends('price_subtotal')
    def _total_sin_descuento_dl(self):
        
        for line in self:
            if line.move_id.currency_id.symbol == "$":
                total = 0.0
                if line.product_uom_id:
                    total = line.price_unit * line.sat_tasa_cambio
                    total_dl = total * line.quantity
                line.update({
                    'total_undiscounted_dl': total_dl,
                })
    
    @api.depends('price_subtotal')
    def _total_sin_descuento(self):
        
        for line in self:
            total = 0.0
            if line.product_uom_id:
                total = line.price_unit * line.quantity
            line.update({
                'total_undiscounted': total,
            })

class AccountMove(models.Model):
    _inherit = "account.move"
    
    total_discount = fields.Monetary(string="Descuento", compute="_amount_discount")
    amount_total_undiscounted = fields.Monetary(string="Total sin descuento", compute="_amount_total_undiscounted")
    total_discount_dl = fields.Monetary(string="Descuento USD", compute="_amount_discount_dl")
    amount_total_undiscounted_dl = fields.Monetary(string="Total sin descuento USD", compute="_amount_total_undiscounted_dl")

    @api.depends('invoice_line_ids.price_subtotal')
    def _amount_discount(self):
        
        for account in self:
            total_desc = 0.0
            total = 0.0
            for line in account.invoice_line_ids:
                total += line.total_undiscounted
                total_desc += line.price_subtotal
            account.update({
                'total_discount': total - account.amount_total,
            })

    @api.depends('total_discount')
    def _amount_total_undiscounted(self):
        
        for account in self:
            total = 0.0
            if account.total_discount == 0.0:
                total = account.amount_total
            else:
                total = account.amount_total + account.total_discount
            account.update({
                'amount_total_undiscounted': total,
            })

    @api.depends('invoice_line_ids.price_subtotal')
    def _amount_discount_dl(self):
        
        for account in self:
            total = 0.0
            if account.currency_id.symbol == "$":
                for line in account.invoice_line_ids:
                    precio_sin_descuento = line.price_unit * line.sat_tasa_cambio
                    precio_unitario = line.price_unit * (100-line.discount) / 100
                    precio_unitario = precio_unitario * line.sat_tasa_cambio
                    descuento = round(precio_sin_descuento * line.quantity - precio_unitario * line.quantity,4)
                    total += descuento
                account.update({
                    'total_discount_dl': total,
                })

    @api.depends('total_discount_dl')
    def _amount_total_undiscounted_dl(self):
        
        for account in self:
            total = 0.0
            if account.total_discount_dl == 0.0:
                total = account.amount_total
            else:
                gran_total = gran_subtotal = gran_total_impuestos = 0
                for line in account.invoice_line_ids:
                    precio_unitario = line.price_unit * (100-line.discount) / 100
                    precio_unitario = precio_unitario * line.sat_tasa_cambio
                    total_linea = round(precio_unitario * line.quantity,6)
                    total_linea_base = round(total_linea / (self.sat_iva_porcentaje/100+1),6)
                    total_impuestos = round(total_linea_base * (self.sat_iva_porcentaje/100),6)
                    gran_total += total_linea
                    gran_subtotal += total_linea_base
                    gran_total_impuestos += total_impuestos
                total = gran_total + self.total_discount_dl
            account.update({
                'amount_total_undiscounted_dl': total,
            })