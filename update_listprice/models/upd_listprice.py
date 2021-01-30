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
