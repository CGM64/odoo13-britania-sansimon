# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request

ALMACEN_TALLER_DEFAULT = 30


class RepairType(models.Model):
    _name = "repair.type"
    _description = "Tipos de ordenes de reparación"

    name = fields.Char('Tipo de orden', required=True)
    sequence = fields.Integer(
        help='Used to order repair types in the dashboard view', default=10)
    active = fields.Boolean(string="Activo", default=True,
                            help="Activa o desctiva tipos de orden")

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
    def _default_stock_location(self):
        return ALMACEN_TALLER_DEFAULT

    location_id = fields.Many2one(
        'stock.location', 'Location',
        default=_default_stock_location,
        index=True, readonly=True, required=True,
        help="This is the location where the product to repair is located.",
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    @api.model
    def _get_default(self):
        type = self.env['repair.type'].search([('active', '=', True)])
        tipos = []
        if type:
            for tipo in type:
                tipos.append(tipo.sequence)
            minimo = min(tipos)
            t = self.env['repair.type'].search([('sequence', '=', minimo)]).id
            return t
        else:
            return

    def unlink(self):
        for move in self:
            if move.name != '/' and not self._context.get('force_delete'):
                raise UserError(_("No se puede eliminar."))
            move.line_ids.unlink()
        return super(repairOrder, self).unlink()

    tipo_orden = fields.Many2one(
        'repair.type', 'Tipo de orden', index=True, default=_get_default)

    def update_detail(self, search=''):

        Fleet = request.env['fleet.vehicle']
        lista_fleet = Fleet.search(
            [('product_tmpl_id', '=', self.product_id.id)], limit=1)

        for i in self.fees_lines:
            product = request.env['fleet.model.repair']
            lista_product = product.search(
                [('model_id', '=', lista_fleet.model_id.id), ('product_id', '=', i.product_id.id)], limit=1)

            if lista_product.labour_time != 0.0:
                if i.product_uom_qty > 1.0:
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
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)

    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not self.type:
            self.location_id = False
            self.location_dest_id = False
        elif self.type == 'add':
            self.onchange_product_id()
            args = self.repair_id.company_id and [
                ('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_id = ALMACEN_TALLER_DEFAULT
            self.location_dest_id = self.env['stock.location'].search(
                [('usage', '=', 'production')], limit=1).id
        else:
            self.price_unit = 0.0
            self.tax_id = False
            self.location_id = self.env['stock.location'].search(
                [('usage', '=', 'production')], limit=1).id
            self.location_dest_id = self.env['stock.location'].search(
                [('scrap_location', '=', True)], limit=1).id

    def _get_amount_total(self):
        for line in self:
            line.amount_total = line.price_unit * line.product_uom_qty
