# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request


class CorteCaja(models.Model):
    _name = "corte.caja"
    _description = "Corte de Caja"

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('transfered', 'Transferido'),
        ('cancel', 'Cancelado'),
    ], default='draft', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Transferencia.")

    name = fields.Char(string='Number', required=True, copy=False,  readonly=True, index=True, default=lambda self: _('New'))
   
    partner_id = fields.Many2one('res.partner', string='Proveedor', index=True, readonly=True, states={'draft': [(
        'readonly', False)]}, domain=lambda self: [("id", "in", self.env['account.payment'].search([('state', '=', 'posted'),
                                                                                                    ('payment_type', '=', 'outbound'),
                                                                                                    ('payment_method_id.code', '=', 'manual')]).mapped("partner_id").ids)])

    user_id = fields.Many2one('res.users', string='Usuario', )
    # domain=lambda self: [("id", "in", self.env['account.payment'].search([
    #     ('state', '=', 'posted'),
    #     ('payment_type', '=', 'inbound'),]).mapped("partner_id").ids)])

    fecha_inicio = fields.Date(string='Fecha inicio', index=True, readonly=True, states={
                               'draft': [('readonly', False)]},required=True)
    fecha_fin = fields.Date(string='Fecha fin', index=True, readonly=True, states={
                            'draft': [('readonly', False)]},required=True)

    corte_caja_ids = fields.One2many('corte.caja.detalle', 'corte_caja_id',
                                                 'Linea Transferencia', copy=True, readonly=True, states={'draft': [('readonly', False)]})

    journal_id = fields.Many2one('account.journal', string='Diario de Pago')



    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'corte.caja') or 'New'
            result = super(CorteCaja, self).create(vals)
            self.write({'state': 'confirm'})
            return result


    def _obtener_lista_diario(self):
        lista_diario=[]
        for linea in self.corte_caja_ids:
            if linea.journal_id.id not in lista_diario:
                lista_diario.append(linea.journal_id.id)
        print("lista_diario-->",lista_diario)
        return lista_diario

    def sumar_por_diario(self):
        lista_diario=self._obtener_lista_diario()
        listado_sumatoria=[]

        dominio = [
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),         
        ]

        if self.user_id:
            dominio += ('create_uid', '=', self.user_id.id),
        if self.journal_id:
            dominio += ('journal_id', '=', self.journal_id.id),
        if self.fecha_inicio:
            dominio += ('payment_date', '>=', self.fecha_inicio),
        if self.fecha_fin:
            dominio += ('payment_date', '<=', self.fecha_fin),
        consulta_account_payment = self.env['account.payment'].search(dominio)

        for diario in lista_diario:
            print("Diario-->",diario)
            sumatoria = sum(calculo.amount for calculo in consulta_account_payment.filtered(lambda journal: journal.journal_id.id in (diario,)))
            dic_sumatoria={'journal_id':diario, 'total':sumatoria}
            listado_sumatoria.append(dic_sumatoria)
        print('listado_sumatoria-->',listado_sumatoria)
        return listado_sumatoria


    def bucar_pagos(self):
        for rec in self:
            rec.corte_caja_ids = [(5,0,0)]

        dominio = [
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),      
        ]

        if self.user_id:
            dominio += ('create_uid', '=', self.user_id.id),
        if self.journal_id:
            dominio += ('journal_id', '=', self.journal_id.id),
        if self.fecha_inicio:
            dominio += ('payment_date', '>=', self.fecha_inicio),
        if self.fecha_fin:
            dominio += ('payment_date', '<=', self.fecha_fin),


        consulta_account_payment = request.env['account.payment'].search(dominio)

        for pago in consulta_account_payment:
            self.corte_caja_ids=[(0,0,{'account_payment_line_id':pago.id})]

class CorteCajaDetalle(models.Model):
    _name = "corte.caja.detalle"
    _description = "Transferido"

    # referencias a tablas
    corte_caja_id = fields.Many2one('corte.caja', string='Corte de Caja', ondelete='cascade')
    account_payment_line_id = fields.Many2one('account.payment', string='Pago',ondelete='cascade')

    # campos relacionados
    journal_id = fields.Many2one(string='Diario de Pago',related='account_payment_line_id.journal_id',store=True)
    circular = fields.Char(string='Circular',related='account_payment_line_id.communication',store=True)
    partner_id = fields.Many2one(string='Cliente', related='account_payment_line_id.partner_id', store=True)

    amount = fields.Monetary(string='Monto', related='account_payment_line_id.amount', store=True)
    currency_id = fields.Many2one(string='Currency', related='account_payment_line_id.currency_id', store=True)


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    move_raw_ids = fields.One2many('corte.caja.detalle', 'account_payment_line_id',
                                   'Components', copy=True, readonly=True, states={'draft': [('readonly', False)]})
