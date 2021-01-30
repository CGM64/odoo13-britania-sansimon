# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class UdpListPrice(models.Model):
    _name = "upd.listprice"
    _description = "Actualizar lista de precios"

    name = fields.Char(string='Nombre', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    date = fields.Datetime(string='Fecha', required=True, index=True, readonly=True,
        default=fields.Datetime.now())
    ref = fields.Char(string='Referencia', copy=False)
    narration = fields.Text(string='Comentarios')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('send', 'Enviado'),
            ('cancel', 'Cancelled')
        ], string='Estatus', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    applied_on = fields.Selection([
        ('0_categoria', 'Categoria'),
        ('1_factura_compra', 'Compra'),
        ('2_proveedor', 'Proveedor'),
        ('3_manual', 'Manual')], "Aplicar En",
        default='0_categoria', required=True,
        help='Indica a Odoo en que se basa para generar una lista de productos para el cambio de precios.')
    categ_id = fields.Many2one('product.category', string='Categoria Producto')
    vendor_bill_id = fields.Many2one('account.move', 'Factura Proveedor', domain=[('type', '=', 'in_invoice'),('state', '=', 'posted')])
    partner_id = fields.Many2one('res.partner', string='Proveedor', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    line_ids = fields.One2many(
        'upd.listprice.line', 'listprice_id', string='Lineas',
        copy=True, readonly=False,
        states={'done': [('readonly', True)]})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'udp.listprice', sequence_date=seq_date) or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('udp.listprice', sequence_date=seq_date) or _('New')
        result = super(UdpListPrice, self).create(vals)
        return result

    def _clean(self):
        for items in self:
            items.line_ids  = None

    def action_calcular(self):
        self._clean()
        if self.applied_on == "0_categoria":
            self._cargar_categorias()

    def _cargar_categorias(self):
        products_template = self.env["product.template"].search([('categ_id','=',self.categ_id.id)])
        for product_template in products_template:
            product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])
            for product in product_product:
                detalle = {
                'product_id': product.id,
                'price_original': product.list_price,
                'listprice_id': self.id
                }
                self.env['upd.listprice.line'].create(detalle)

class UdpListPriceLine(models.Model):
    _name = "upd.listprice.line"
    _description = "Actualizar lista de precios Line"
    _order = "product_id, listprice_id"

    listprice_id = fields.Many2one(
        'upd.listprice', 'Lista de Precios', check_company=True,
        index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        index=True, required=True)
    state = fields.Selection('Status', related='listprice_id.state')
    company_id = fields.Many2one(string='Company', related='listprice_id.company_id')

    price_original = fields.Float('Original', digits='Product Price', readonly=True)
    price_nuevo = fields.Float('Nuevo', digits='Product Price')
    percent_margen = fields.Float('% Margen', compute='_compute_new_price')
    price_diferencia = fields.Float('Diferencia', digits='Product Price', compute='_compute_new_price')
    percent_diferencia = fields.Float('% Diferencia', compute='_compute_new_price')

    @api.depends('price_original', 'price_nuevo')
    def _compute_new_price(self):
        for item in self:
            item.percent_margen = 1
            item.price_diferencia = 1
            item.percent_diferencia = 1
