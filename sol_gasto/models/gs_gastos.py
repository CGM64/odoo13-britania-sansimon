# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class GsGastos(models.Model):
    _name = "gs.gastos"
    _description = "Gastos"

    def button_approved(self):
        self.write({'state': 'approved'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('approved', 'Aprobado'),
        ('done', 'Pagado'),
        ('refused', 'Rechazado'),
    ], default='draft', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Solicitud.")

    name = fields.Char('Descripción', readonly=True, required=True,
                       states={'draft': [('readonly', False)],
                               'refused': [('readonly', False)]})

    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True,
                                 help="Puedes buscar por Nombre, NIF, Email or Referencia.")

    unit_amount = fields.Float("Monto", store=True, required=True, copy=True, digits='Product Price',
                               states={'draft': [('readonly', False)],
                                       'refused': [('readonly', False)]})

    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True,
                                  states={'draft': [('readonly', False)],
                                          'refused': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id)

    description = fields.Text('Notas...', readonly=True,
                              states={'draft': [('readonly', False)],
                                      'refused': [('readonly', False)]})

    date = fields.Date(readonly=True, states={
        'draft': [('readonly', False)],
        'refused': [('readonly', False)]},
        default=fields.Date.context_today, string="Fecha Entrega")

    reference = fields.Char("Referencia", required=True, readonly=True, states={
        'draft': [('readonly', False)],
        'refused': [('readonly', False)]})

    AVAILABLE_PRIORITIES = [
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ]
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Prioridad', index=True,
                                default=AVAILABLE_PRIORITIES[0][0])
