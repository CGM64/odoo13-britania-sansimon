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
        ('confirm', 'Confirmado'),
        ('cancel', 'Cancelado'),
    ], default='draft', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Transferencia.")

    name = fields.Char(string='Number', required=True, copy=False,  readonly=True, index=True, default=lambda self: _('New'))
   
    partner_id = fields.Many2one('res.partner', string='Proveedor', index=True, readonly=True, states={'draft': [(
        'readonly', False)]}, domain=lambda self: [("id", "in", self.env['account.payment'].search([('state', '=', 'posted'),
                                                                                                    ('payment_type', '=', 'outbound'),
                                                                                                    ('payment_method_id.code', '=', 'manual')]).mapped("partner_id").ids)])

    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.uid)

    

    fecha_inicio = fields.Date(string='Fecha inicio', index=True, readonly=True, states={
                               'draft': [('readonly', False)]},required=True)
    fecha_fin = fields.Date(string='Fecha fin', index=True, readonly=True, states={
                            'draft': [('readonly', False)]},required=True)
    journal_id = fields.Many2one('account.journal', string='Diario de Pago')


    #Relaciones
    corte_caja_ids = fields.One2many('corte.caja.detalle', 'corte_caja_id',
                                                 'Detalle', copy=True, readonly=True, states={'draft': [('readonly', False)]})
    
    corte_caja_resumen_ids = fields.One2many('corte.caja.resumen', 'corte_caja_resumen_id',
                                                 'Resumen', copy=True, readonly=True, states={'draft': [('readonly', False)]})


    corte_caja_factura_ids = fields.One2many('corte.caja.factura', 'corte_caja_factura_id',
                                                 'Resumen', copy=True, readonly=True, states={'draft': [('readonly', False)]})


    total_corte=fields.Float(string='Total', compute="_total_corte", store=True)
    total_facturas=fields.Float(string='Total', compute="_total_facturas", store=True)



    @api.onchange('corte_caja_ids','corte_caja_resumen_ids',)
    def _total_corte(self):
        suma=0
        for linea in self.corte_caja_resumen_ids:
            suma+=linea.amount
        self.total_corte=suma

    @api.onchange('corte_caja_factura_ids')
    def _total_facturas(self):
        suma=0
        for linea in self.corte_caja_factura_ids:
            suma+=linea.amount_total
        self.total_facturas=suma

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
        return lista_diario

    def _sumar_por_diario(self,consulta_account_payment):
        lista_diario=self._obtener_lista_diario()
        listado_sumatoria=[]

        for diario in lista_diario:
            sumatoria = sum(calculo.amount for calculo in consulta_account_payment.filtered(lambda journal: journal.journal_id.id in (diario,)))
            dic_sumatoria={'journal_id':diario, 'amount':sumatoria}
            listado_sumatoria.append(dic_sumatoria)
        return listado_sumatoria

    def _borrar_lineas(self):
        for rec in self: rec.corte_caja_ids = [(5,0,0)]
        for rec in self: rec.corte_caja_resumen_ids = [(5,0,0)]
        for rec in self: rec.corte_caja_factura_ids = [(5,0,0)]

    def action_procesar(self):
        self._borrar_lineas()   
        self._buscar_pagos()
        self._buscar_facturas()
    

    def action_confirm(self):
        cont=0
        for rec in self.corte_caja_ids:
            cont+=1
        for rec in self.corte_caja_resumen_ids:
            cont+=1
        for rec in self.corte_caja_factura_ids:
            cont+=1
        
        if cont ==0:
            raise Warning("Existen líneas en blanco, por favor valide.")
        else:
            self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def _buscar_facturas(self):  
        dominio = [
            ('state', '=', 'posted'),
            ('type', '=', 'out_invoice'),      
        ]

        if self.user_id:
            dominio += ('create_uid', '=', self.user_id.id),
        if self.fecha_inicio:
            dominio += ('invoice_date', '>=', self.fecha_inicio),
        if self.fecha_fin:
            dominio += ('invoice_date', '<=', self.fecha_fin),

        consulta_account_move = request.env['account.move'].search(dominio)

        for factura in consulta_account_move:
            self.corte_caja_factura_ids=[(0,0,{'account_move_line_id':factura.id})]
        
        self._total_facturas()


    def _buscar_pagos(self): 
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

        lista_suma_diario=self._sumar_por_diario(consulta_account_payment)
        for suma_diario in lista_suma_diario:
            self.corte_caja_resumen_ids=[(0,0,suma_diario)]

        self._total_corte()
        
class CorteCajaDetalle(models.Model):
    _name = "corte.caja.detalle"
    _description = "Detalle"

    # referencias a tablas
    corte_caja_id = fields.Many2one('corte.caja', string='Corte de Caja', ondelete='cascade')
    account_payment_line_id = fields.Many2one('account.payment', string='Pago',ondelete='cascade')

    # campos relacionados
    journal_id = fields.Many2one(string='Diario de Pago',related='account_payment_line_id.journal_id',store=True)
    circular = fields.Char(string='Circular',related='account_payment_line_id.communication',store=True)
    partner_id = fields.Many2one(string='Cliente', related='account_payment_line_id.partner_id', store=True)

    amount = fields.Monetary(string='Monto', related='account_payment_line_id.amount', store=True)
    currency_id = fields.Many2one(string='Currency', related='account_payment_line_id.currency_id', store=True)

class CorteCajaResumen(models.Model):
    _name = "corte.caja.resumen"
    _description = "Resumen"

    # referencias a tablas
    corte_caja_resumen_id = fields.Many2one('corte.caja', string='Corte de Caja', ondelete='cascade')
    journal_id = fields.Many2one('account.journal', string='Diario',ondelete='cascade')
    amount = fields.Float(string='Monto', store=True)

class CorteCajaFactura(models.Model):
    _name = "corte.caja.factura"
    _description = "Facturas"

    # referencias a tablas
    corte_caja_factura_id = fields.Many2one('corte.caja', string='Corte de Caja', ondelete='cascade')
    account_move_line_id = fields.Many2one('account.move', string='Facturas',ondelete='cascade')

    # campos relacionados
    name = fields.Char(string='Factura',related='account_move_line_id.name',store=True)
    partner_id = fields.Many2one(string='Cliente', related='account_move_line_id.partner_id', store=True)
    ref = fields.Char(string='Referencia',related='account_move_line_id.ref',store=True)

    invoice_date = fields.Date(string='Fecha Factura',related='account_move_line_id.invoice_date',store=True)
    amount_total = fields.Monetary(string='Monto', related='account_move_line_id.amount_total', store=True)
    currency_id = fields.Many2one(string='Currency', related='account_move_line_id.currency_id', store=True)


class AccountMovetInherit(models.Model):
    _inherit = "account.move"

    corte_caja_id = fields.One2many('corte.caja.factura', 'account_move_line_id',
                                   'Facturas', copy=True, readonly=True, states={'draft': [('readonly', False)]})


class AccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    move_raw_ids = fields.One2many('corte.caja.detalle', 'account_payment_line_id',
                                   'Detalle', copy=True, readonly=True, states={'draft': [('readonly', False)]})
