# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime


class SaleOrderLine(models.Model):
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

class SaleOrder(models.Model):
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

    def action_confirm(self):
        rslt=super(SaleOrder,self).action_confirm()
        if self.user_has_groups('britania.sale_group_acceso_desc'):
            porcentaje_maximo=self.team_id.porcentaje_maximo_lider
        else:
            porcentaje_maximo=self.team_id.porcentaje_maximo
        for line in self.order_line:
            if line.discount >porcentaje_maximo:
                raise UserError(_("El porcentaje de descuento es mayor al porcentaje permitido en la linea del producto %s.") % (line.product_id.name))
        return  rslt

    def obtener_variante(self,line_id1):
        
        co = " "
        
        vehiculo = self.env['fleet.vehicle'].sudo().search([('product_id','=',line_id1.id)])
        
        if line_id1.is_vehicle:
            for temporal in vehiculo:
                colorfinal = (temporal.color)
                co = " Color " + str(colorfinal.lower())

            return (co)
        
            
    
    def fechacot(self,fecha):
        
        fe = str(fecha)
        
        if fe[5] == "0" and fe[6] == "1":
            fe1 = fe[8] + fe[9] + " de enero de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "2":
            fe1 = fe[8] + fe[9] + " de febrero de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "3":
            fe1 = fe[8] + fe[9] + " de marzo de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "4":
            fe1 = fe[8] + fe[9] + " de abril de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "5":
            fe1 = fe[8] + fe[9] + " de abril de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "6":
            fe1 = fe[8] + fe[9] + " de junio de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "7":
            fe1 = fe[8] + fe[9] + " de julio de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "8":
            fe1 = fe[8] + fe[9] + " de agosto de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "0" and fe[6] == "9":
            fe1 = fe[8] + fe[9] + " de septiembre de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "1" and fe[6] == "0":
            fe1 = fe[8] + fe[9] + " de octubre de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "1" and fe[6] == "1":
            fe1 = fe[8] + fe[9] + " de noviembre de " + fe[0] + fe[1] + fe[2] + fe[3] 
        if fe[5] == "1" and fe[6] == "2":
            fe1 = fe[8] + fe[9] + " de diciembre de " + fe[0] + fe[1] + fe[2] + fe[3] 
            
        return fe1
        
        

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
