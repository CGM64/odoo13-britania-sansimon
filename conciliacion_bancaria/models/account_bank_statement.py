# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request
import datetime


class PrintBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def print_bank_statement(self):
        return self.env.ref('conciliacion_bancaria.action_statement_report').report_action(self)

    @api.depends('line_ids', 'balance_start', 'line_ids.amount', 'balance_end_real')
    def _cargos_abonos_balance(self):
        for statement in self:
            statement.balance_abonos = sum([line.amount for line in statement.line_ids if line.amount<0])
            statement.balance_cargos = sum([line.amount for line in statement.line_ids if line.amount>0])


    balance_abonos = fields.Monetary('Abonos', compute='_cargos_abonos_balance')
    balance_cargos = fields.Monetary('Cargos', compute='_cargos_abonos_balance')


    def conciliacion_bancaria(self,):
        account_bank_statement=request.env['account.bank.statement'].search([('id','=',self.id)])
        account_move_line=request.env['account.move.line'].search([('id','=',self.id)])

        if account_bank_statement.journal_id.bank_id.template_extractos =='BAM':
            conciliacion=self._conciliacion_BAM(account_bank_statement,account_move_line)

        return conciliacion

    def _conciliacion_BAM(self,account_bank_statement,account_move_line):
        BAM=['CHEQUE','NC','ND','DEPOSITO']
        
        conciliacion={
                'banco':account_bank_statement.name,
                'diario':account_bank_statement.journal_id.name,
                'fecha':account_bank_statement.date,
                'saldo_inicial':account_bank_statement.balance_start,
                'saldo_final':account_bank_statement.balance_end_real,
                'moneda':account_bank_statement.currency_id.symbol,
            }
        
        lista_ids=[]
        lista_otros=[]
        lista_conciliacion=[]
        cheques_circulacion=[]
        circulacion=0
        pagados=0
        for documento in BAM:
            lista_documento=[]
            suma_documento=0

            for line in account_bank_statement.line_ids.filtered(lambda l: l.name.startswith(documento)):
                account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line.id),('date','<=',line.date)])                   
                if account_move_line.date==False:
                    suma_documento+=line.amount
                    if documento=='CHEQUE':
                        circulacion+=line.amount
                        cheques_circulacion.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
                    else:
                        lista_documento.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
                else:
                    suma_documento+=line.amount
                    if documento=='CHEQUE':
                        pagados+=line.amount 
                    lista_documento.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'S'})                                    

                if line.id not in lista_ids:
                    lista_ids.append(line.id)

            conciliacion[documento]=lista_documento
            conciliacion['ch_circulacion']=circulacion
            conciliacion['ch_pagados']=pagados
            conciliacion['CIRCULACION']=cheques_circulacion

        for line in account_bank_statement.line_ids.filtered(lambda l: l.id not in lista_ids):
            account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line.id)])
            if account_move_line.date==False:
                lista_otros.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
            else:
                lista_otros.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'S'})     
        conciliacion['otros']=lista_otros
        lista_conciliacion.append(conciliacion)
        print('conciliacion>',conciliacion)

        return lista_conciliacion
