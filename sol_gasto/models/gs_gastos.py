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

    def button_done(self):
        self.write({'state': 'done'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def button_draft(self):
        self.write({'state': 'draft'})

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('cancel', 'Cancelado'),
        ('approved', 'Aprobado'),
        ('done', 'Pagado'),
        ('refused', 'Rechazado'),
    ], default='draft', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Solicitud.")

    name = fields.Char('Descripción', readonly=True, required=True,
                       states={'draft': [('readonly', False)],
                               'cancel': [('readonly', True)],
                               'approved': [('readonly', True)],
                               'done': [('readonly', True)]})

    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True, required=True,
                                 help="Puedes buscar por Nombre, NIF, Email or Referencia.",
                                 states={'draft': [('readonly', False)],
                                         'cancel': [('readonly', True)],
                                         'approved': [('readonly', True)],
                                         'done': [('readonly', True)]})

    unit_amount = fields.Float("Monto", store=True, required=True, copy=True, digits='Product Price',
                               states={'draft': [('readonly', False)],
                                       'cancel': [('readonly', True)],
                                       'approved': [('readonly', True)],
                                       'done': [('readonly', True)]})

    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True, required=True,
                                  states={'draft': [('readonly', False)],
                                          'cancel': [('readonly', True)],
                                          'approved': [('readonly', True)],
                                          'done': [('readonly', True)]},
                                  default=lambda self: self.env.company.currency_id)

    description = fields.Text('Notas...', readonly=True,
                              states={'draft': [('readonly', False)],
                                      'cancel': [('readonly', True)],
                                      'approved': [('readonly', True)],
                                      'done': [('readonly', True)]})

    date = fields.Date(readonly=True, required=True,
                       states={'draft': [('readonly', False)],
                               'cancel': [('readonly', True)],
                               'approved': [('readonly', True)],
                               'done': [('readonly', True)]},
                       default=fields.Date.context_today, string="Fecha Entrega")

    reference = fields.Char("Referencia", required=True, readonly=True,
                            states={'draft': [('readonly', False)],
                                    'cancel': [('readonly', True)],
                                    'approved': [('readonly', True)],
                                    'done': [('readonly', True)]})

    AVAILABLE_PRIORITIES = [
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High'),
    ]
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Prioridad', index=True,
                                default=AVAILABLE_PRIORITIES[0][0],
                                states={'draft': [('readonly', False)],
                                        'cancel': [('readonly', True)],
                                        'approved': [('readonly', True)],
                                        'done': [('readonly', True)]})

    def open_window(self):
        view_id = self.env.ref(
            'account.view_account_payment_form'
        ).id
        context = self._context.copy()
        return {
            'name': 'Pagos',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'target': 'new',
        }
