# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    no_linea = fields.Integer('Numero de Linea', compute='_compute_no_linea')

    sat_importa_in_ca = fields.Monetary(string="Importacion In CA", compute='_compute_libro_fiscal')
    sat_importa_out_ca = fields.Monetary(string="Importacion Out CA", compute='_compute_libro_fiscal')

    sat_exportacion_in_ca = fields.Monetary(string="Exportacion In CA", compute='_compute_libro_fiscal')
    sat_exportacion_out_ca = fields.Monetary(string="Exportacion Out CA", compute='_compute_libro_fiscal')

    sat_servicio = fields.Monetary(string="Servicio", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_bien = fields.Monetary(string="Bien", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_exento = fields.Monetary(string="Exento", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_peq_contri = fields.Monetary(string="Pequeño Contribuyente", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_iva = fields.Monetary(string="IVA", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_subtotal = fields.Monetary(string="Subtotal", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_amount_total = fields.Monetary(string="Sat Total", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_combustible = fields.Monetary(string="Combustible", compute='_compute_libro_fiscal', currency_field='company_currency_id')
    sat_base = fields.Monetary(string="Base", compute='_compute_libro_fiscal', currency_field='company_currency_id')


    sat_valor_transaccion = fields.Float(string="Valor de transaccion", digits=(8, 2), readonly=True, states={'draft': [('readonly', False)]},)
    sat_gastos_transporte = fields.Float(string="Gastos de Transporte", digits=(8, 2), readonly=True, states={'draft': [('readonly', False)]},)
    sat_gastos_seguros = fields.Float(string="Gastos de Seguro", digits=(8, 2), readonly=True, states={'draft': [('readonly', False)]},)
    sat_gastos_otros = fields.Float(string="Otros Gastos", digits=(8, 2), readonly=True, states={'draft': [('readonly', False)]},)
    sat_tasa_cambio = fields.Float(string="Tasa de cambio", digits=(8, 5), readonly=True, states={'draft': [('readonly', False)]},)

    sat_invoice_id = fields.Many2one('account.move', string='Factura Relacionada')
    sat_invoice_name = fields.Char(related='sat_invoice_id.name', readonly=True, string='Invoice name')
    sat_invoice_child_ids = fields.One2many('account.move', 'sat_invoice_id', string='Invoice Links', domain=[('state', '=', 'posted')], readonly=True, states={'draft': [('readonly', False)]})

    #Estoy trabajando en solo linkiar los documentos y no utilizarlos para la carga


    fac_numero = fields.Char('Numero', copy=False, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]},)
    fac_serie = fields.Char('Serie', copy=False, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]},)

    sat_fac_numero = fields.Char(string="Numero Factura", compute='_compute_libro_fiscal')
    sat_fac_serie = fields.Char(string="Serie Factura", compute='_compute_libro_fiscal')

    journal_tipo_operacion = fields.Selection('Tipo de Operacion', related='journal_id.tipo_operacion', readonly=True)

    def _compute_no_linea(self):
        self.no_linea = 0

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_libro_fiscal(self):
        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            iva_importacion = 0.0
            iva = 0.0
            currencies = set()

            total_servicio = total_servicio_iva = 0.0
            total_bien = total_bien_iva = 0.0
            sat_peq_contri = sat_exento = sat_combustible = 0.0
            sat_importa_in_ca = 0

            sat_exportacion_in_ca = sat_exportacion_out_ca = 0

            if move.fac_serie:
                move.sat_fac_serie = move.fac_serie
            else:
                if move.name:
                    move.sat_fac_serie = move.name[move.name.rfind("/")+1:move.name.find("-")]

            if move.fac_numero:
                move.sat_fac_numero = move.fac_numero
            else:
                if move.name:
                    move.sat_fac_numero = move.name[move.name.find("-")+1:len(move.name)]

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

                for impuesto in line.tax_line_id:
                    if impuesto.impuesto_sat == 'ipeq':
                        sat_peq_contri += line.balance
                    elif impuesto.impuesto_sat == 'iva':
                        iva += line.balance
                    elif impuesto.impuesto_sat == 'idp':
                        sat_exento += line.balance
                    elif impuesto.impuesto_sat == 'inguat':
                        sat_exento += line.balance


                if line.product_id:
                    es_peq_contribuyente = False
                    for line_imp in line.tax_ids:
                        if line_imp.impuesto_sat == 'ipeq':
                            es_peq_contribuyente = True
                    if es_peq_contribuyente:
                        sat_peq_contri += line.balance
                    elif line.product_id.sat_tipo_producto == 'gas':
                        sat_combustible += line.balance
                    elif line.product_id.sat_tipo_producto == 'exp_in_ca_bien':
                        sat_exportacion_in_ca += line.balance
                    elif line.product_id.sat_tipo_producto == 'imp_out_ca_bien':
                        iva_importacion += line.balance
                    elif line.product_id.type in ('service'):
                        total_servicio += line.balance
                    else:
                        total_bien += line.balance


            if move.type == 'out_invoice':
                sign = -1
            elif move.type == 'out_refund':
                sign = -1
            else:
                sign = 1
            #move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            #move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            #move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            #move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            #move.amount_untaxed_signed = -total_untaxed
            #move.amount_tax_signed = -total_tax
            #move.amount_total_signed = abs(total) if move.type == 'entry' else -total
            #move.amount_residual_signed = total_residual
            move.sat_exento = 0
            move.sat_servicio = 0
            move.sat_bien = 0
            move.sat_iva = 0
            move.sat_subtotal = 0
            move.sat_amount_total = 0
            move.sat_peq_contri = 0
            move.sat_combustible = 0
            move.sat_base = 0
            move.sat_importa_in_ca = 0
            move.sat_importa_out_ca = 0
            move.sat_exportacion_in_ca = 0

            if move.state == 'cancel':
                move.sat_exento = 0

            elif move.journal_id.tipo_operacion == 'DUCA_IN':
                move.sat_iva = iva_importacion
                move.sat_importa_in_ca = move.sat_iva / 0.12
                move.sat_exportacion_in_ca = sign * sat_exportacion_in_ca
                move.sat_amount_total = move.sat_importa_in_ca + move.sat_iva + move.sat_exportacion_in_ca

            elif move.journal_id.tipo_operacion == 'DUCA_OUT':
                move.sat_iva = iva_importacion
                move.sat_importa_out_ca = move.sat_iva / 0.12
                move.sat_amount_total = move.sat_importa_out_ca + move.sat_iva
            else:

                move.sat_servicio = sign * total_servicio
                move.sat_bien = sign * total_bien
                move.sat_exento = sign * sat_exento
                move.sat_combustible = sign * sat_combustible
                move.sat_iva = iva
                move.sat_subtotal = move.sat_servicio + move.sat_bien



                move.sat_amount_total = sign * total
                move.sat_peq_contri = sat_peq_contri
                move.sat_base = move.sat_servicio + move.sat_bien + move.sat_combustible

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual
