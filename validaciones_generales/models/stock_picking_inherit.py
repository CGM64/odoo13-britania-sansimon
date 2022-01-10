# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request
import datetime
from odoo.tools.float_utils import float_compare


class StockPickingInherit(models.Model):
    _inherit = "stock.picking"
    _description = "Validaciones para el modelo stock.picking"

    def button_validate(self):
        self.ensure_one()
        ubicacion_origen=self.location_id.location_id.location_id.complete_name
        ubicacion_destino=self.location_dest_id.location_id.location_id.complete_name

        # print("Self",self.id, self.name)
        # print("Ubicación de origen: ",ubicacion_origen, self.location_id.name,self.location_id.id)
        # print("Ubicación destino: ",ubicacion_destino,self.location_dest_id.name,self.location_dest_id.id)
        # raise UserError(_('test') )

        if  ubicacion_origen=='Physical Locations' and ubicacion_destino=='Physical Locations' :
            # print("Entro a la validación de ubicaciones físicas")
            # raise UserError(_('entro al if for') )
            for picking in self:
                for line in picking.move_ids_without_package:
                    stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                    if len(stock_quant) == 0:
                        raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)  
                    for location in stock_quant:
                        if location.quantity < line.product_uom_qty:
                            raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)

                # VALIDA LA SOPERACIONES DETALLADAS
                for line in picking.move_line_ids_without_package:
                    stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                    if len(stock_quant) == 0:
                        raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)
                    
                    for location in stock_quant:
                        if location.quantity < line.qty_done:
                            raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)
        rslt = super(StockPickingInherit, self).button_validate()    
        return rslt
class StockBackorderConfirmation(models.TransientModel):
    _name = 'stock.backorder.confirmation'
    _description = 'Backorder Confirmation'

    pick_ids = fields.Many2many('stock.picking', 'stock_picking_backorder_rel')

    def _process(self, cancel_backorder=False):
        for confirmation in self:
            if cancel_backorder:
                for pick_id in confirmation.pick_ids:
                    moves_to_log = {}
                    for move in pick_id.move_lines:
                        if float_compare(move.product_uom_qty,
                                         move.quantity_done,
                                         precision_rounding=move.product_uom.rounding) > 0:
                            moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
                    pick_id._log_less_quantities_than_expected(moves_to_log)
            confirmation.pick_ids.with_context(cancel_backorder=cancel_backorder).action_done()

    def process(self):
        for picking in self.pick_ids:
            #VALIDA LAS OPERACIONES
            for line in picking.move_ids_without_package:
                stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                if len(stock_quant) == 0:
                    raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)
                
                for location in stock_quant:
                    if location.quantity < line.product_uom_qty:
                        raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)

            #VALIDA LA SOPERACIONES DETALLADAS
            for line in picking.move_line_ids_without_package:
                stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                if len(stock_quant) == 0:
                    raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)
                
                for location in stock_quant:
                    if location.quantity < line.qty_done:
                        raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)
        self._process()

    def process_cancel_backorder(self):
        for picking in self.pick_ids:
            #VALIDA LAS OPERACIONES
            for line in picking.move_ids_without_package:
                stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                if len(stock_quant) == 0:
                    raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)
            
                for location in stock_quant:
                    if location.quantity < line.product_uom_qty:
                        raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)

            #VALIDA LA SOPERACIONES DETALLADAS
            for line in picking.move_line_ids_without_package:
                stock_quant=self.env['stock.quant'].search([('location_id','=',picking.location_id.id),('product_id','=',line.product_id.id)])
                if len(stock_quant) == 0:
                    raise UserError(_('No hay stock para el producto: %s') % line.product_id.name)
                
                for location in stock_quant:
                    if location.quantity < line.qty_done:
                        raise UserError(_('No hay suficiente stock para el producto: %s') % line.product_id.name)
        self._process(cancel_backorder=True)




