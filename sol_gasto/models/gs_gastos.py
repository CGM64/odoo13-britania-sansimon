# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp


class GsGastos(models.Model):
    _name = "gs.gastos"
    _description = "Gastos"

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

    unit_amount = fields.Monetary(currency_field="currency_id", string="Monto", store=True, required=True, copy=True,
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

    journal_id = fields.Many2one('account.journal', string='Diario', required=True, readonly=True,
                                 default=56,
                                 states={'draft': [('readonly', False)],
                                         'cancel': [('readonly', True)],
                                         'approved': [('readonly', True)],
                                         'done': [('readonly', True)]})

    def aplicar_pago(self):
        proveedor = int(self.partner_id[0])
        moneda = int(self.currency_id[0])
        monto = self.unit_amount
        diario = int(self.journal_id[0])
        self.ensure_one()
        self.write({'state': 'done'})
        return {
            'name': 'Registrar Pago',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': 'account.view_account_payment_form',
            'target': 'new',
            'context': {
                'readonly': True,
                'default_observaciones': self.name,
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_amount': monto,
                'default_partner_id': proveedor,
                'default_payment_method_id': 4,
                'default_journal_id': diario,
                'default_currency_id': moneda,
                'default_payment_date': self.date,
                'default_check_no_negociable': 1,
            },
            'view_type': 'form',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',

        }

    # Botones de estado

    def button_approved(self):
        self.write({'state': 'approved'})

    def button_done(self):
        self.write({'state': 'done'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def button_draft(self):
        self.write({'state': 'draft'})

    def aplicar_factura1(self):
        return {
            'name': 'Registrar Factura',
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_id': 'account.view_move_form',
            'target': 'new',
            'view_type': 'form',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',

        }


class AccountMove(models.Model):
    _inherit = "account.move"

    def aplicar_factura(self):
        return {
            'name': 'Registrar Factura',
            'res_model': 'account.move',
            'view_mode': 'form',
            'view_id': 'account.view_move_form',
            'target': 'new',
            'view_type': 'form',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',

        }
