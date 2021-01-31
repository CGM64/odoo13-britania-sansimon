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
    ref = fields.Char(string='Referencia', readonly=True, states={'draft': [('readonly', False)]})
    narration = fields.Text(string='Comentarios', readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)
    state = fields.Selection(selection=[
            ('draft', 'Borrador'),
            ('confirm', 'Confirmado'),
            ('cancel', 'Cancelado')
        ], string='Estatus', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    applied_on = fields.Selection([
        ('0_categoria', 'Categoria'),
        ('1_factura_compra', 'Compra'),
        ('2_proveedor', 'Proveedor'),
        ('3_manual', 'Manual')], "Aplicar En",
        default='0_categoria', required=True,
        help='Indica a Odoo en que se basa para generar una lista de productos para el cambio de precios.', readonly=True, states={'draft': [('readonly', False)]})
    categ_id = fields.Many2one('product.category', string='Categoria Producto', readonly=True, states={'draft': [('readonly', False)]})
    vendor_bill_id = fields.Many2one('account.move', 'Factura Proveedor', domain=[('type', '=', 'in_invoice'),('state', '=', 'posted')], readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Proveedor', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", readonly=True, states={'draft': [('readonly', False)]})

    compute_price = fields.Selection([
        ('4_fixed', 'Precio Fijo'),
        ('5_percentage', 'Porcentaje'),
        ('6_utilidad', 'Grupo de Utilidad')], index=True, default='4_fixed', required=True, string="Calculo del Precio", readonly=True, states={'draft': [('readonly', False)]},
            help="Precio Fijo: le coloca un precio fijo al precio de lista\n"
            "Porcentaje: Le aumenta un porcentaje al precio de lista\n"
            "Grupo de Utilida: Le suma el grupo de utilidad al costo + el iva\n")
    fixed_price = fields.Float('Precio Fijo', digits='Product Price',readonly=True, states={'draft': [('readonly', False)]})
    percent_price = fields.Float('Porcentaje al Precio', readonly=True, states={'draft': [('readonly', False)]})

    line_ids = fields.One2many(
        'upd.listprice.line', 'listprice_id', string='Lineas',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)]})

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

    def action_anular(self):
        for item in self.line_ids:
            item.product_id.list_price = item.price_original
        self.state = 'cancel'

    def action_confirmar(self):
        for item in self.line_ids:
            item.product_id.list_price = item.price_nuevo
        self.state = 'confirm'

    def action_clean(self):
        self._clean()

    def action_calcular(self):
        if self.applied_on == "0_categoria":
            self._cargar_categorias()
        if self.applied_on == "1_factura_compra":
            self._cargar_factura_compra()
        self._aplicar_precio()

    def _aplicar_precio(self):
        for item in self.line_ids:
            item.price_nuevo
            if self.compute_price == "4_fixed":
                item.price_nuevo = self.fixed_price
            elif self.compute_price == "5_percentage":
                item.price_nuevo = (item.price_original + (item.price_original * (self.percent_price / 100))) or 0.0
            elif self.compute_price == "6_utilidad":
                item.price_nuevo = item.product_id.standard_price * (item.product_id.product_tmpl_id.grupo_utilidad_id.porcentaje / 100 + 1) * 1.12

    def _get_find_product_line(self, product_id):
        buscar_existe = self.env['upd.listprice.line'].search([('listprice_id','=',self.id),('product_id','=',product_id)])
        if not buscar_existe:
            return False
        return True

    def _cargar_categorias(self):
        products_template = self.env["product.template"].search([('categ_id','=',self.categ_id.id)])
        for product_template in products_template:
            product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])
            for product in product_product:
                detalle = {
                'product_id': product.id,
                'price_original': product.list_price,
                'price_nuevo': product.list_price,
                'listprice_id': self.id
                }
                if not self._get_find_product_line(product.id):
                    self.env['upd.listprice.line'].create(detalle)

    def _cargar_factura_compra(self):
        for item in self.vendor_bill_id.invoice_line_ids:

            detalle = {
            'product_id': item.product_id.id,
            'price_original': item.product_id.list_price,
            'price_nuevo': item.product_id.standard_price,
            'listprice_id': self.id
            }
            if not self._get_find_product_line(item.product_id.id):
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
            item.price_diferencia = item.price_nuevo - item.price_original
            item.percent_diferencia = item.price_diferencia * 100 / item.price_original
