# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class repairOrder(models.Model):
    _inherit = "repair.order"

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