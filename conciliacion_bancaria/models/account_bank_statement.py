# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request
import datetime


DOCUMENTOS_BANCARIOS=['CH','DP','NC','ND']

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

    def conciliacion_bancaria(self):
        account_bank_statement=request.env['account.bank.statement'].search([('id','=',self.id)])
        account_move_line=request.env['account.move.line'].search([('id','=',self.id)])

        self._procesar_conciliacion(account_bank_statement)

        return 

    def _tipo_documentos(self,account_bank_statement):
        _depositos=['DEP','DEPOSITO','DP','DE']
        _notas_credito=['NC','N/C','N/CREDITO']
        _notas_debito=['ND','N/D','N/DEBITO']
        _cheques=['CH','CHQ','CHEQUE','CQ']
       
        documentos=[]
        lines=[]
        for line in account_bank_statement.line_ids:
            cadena=line.name.split(' ')
            documento=str(cadena[0]).replace(':','')
            if line not in lines:
                lines.append(line)

                if documento in _depositos:
                    documentos.append(('DP',line))
                elif documento in _notas_credito:
                    documentos.append(('NC',line))
                elif documento in _notas_debito:
                    documentos.append(('ND',line))
                elif documento in _cheques:
                    documentos.append(('CH',line))
                else:
                    if line.amount < 0:
                        documentos.append(('NC',line))
                    else:
                        documentos.append(('ND',line))
        return documentos


    def _procesar_conciliacion(self,account_bank_statement):
        account_bank_statement_lines=self._tipo_documentos(account_bank_statement)

        conciliacion={
                'banco':account_bank_statement.name,
                'diario':account_bank_statement.journal_id.name,
                'fecha':account_bank_statement.date,
                'saldo_inicial':account_bank_statement.balance_start,
                'saldo_final':account_bank_statement.balance_end_real,
                'moneda':account_bank_statement.currency_id.symbol,
            }

        cheques_circulacion=[]
        suma_circulacion=0
        suma_pagados=0
        for documento in DOCUMENTOS_BANCARIOS:
            lista_documento=[]
            suma_documento=0
            print("DOCUMENTO",documento)
            lines=filter(lambda d: d[0] ==documento, account_bank_statement_lines)
            for line in lines:
                print('     lines> ',line[0], line[1].name)
                account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line[1].id),('date','<=',line[1].date)])

                if account_move_line.date==False:
                    if documento=='CH':
                        suma_circulacion+=line[1].amount
                        cheques_circulacion.append({'line_fecha':line[1].date,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
                    else:
                        lista_documento.append({'line_fecha':line[1].date,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
                else:
                    if documento=='CH':
                        suma_pagados+=line[1].amount
                        lista_documento.append({'line_fecha':line[1].date,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
                    else:
                        lista_documento.append({'line_fecha':line[1].date,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
            
            conciliacion[documento]=lista_documento


        return


    

    # def _conciliacion_BAM(self,account_bank_statement,account_move_line):
    #     BAM=['CHEQUE','NC','ND','DEPOSITO']
        
    #     conciliacion={
    #             'banco':account_bank_statement.name,
    #             'diario':account_bank_statement.journal_id.name,
    #             'fecha':account_bank_statement.date,
    #             'saldo_inicial':account_bank_statement.balance_start,
    #             'saldo_final':account_bank_statement.balance_end_real,
    #             'moneda':account_bank_statement.currency_id.symbol,
    #         }
        
    #     lista_ids=[]
    #     lista_otros=[]
    #     lista_conciliacion=[]
    #     cheques_circulacion=[]
    #     circulacion=0
    #     pagados=0
    #     for documento in BAM:
    #         lista_documento=[]
    #         suma_documento=0

    #         for line in account_bank_statement.line_ids.filtered(lambda l: l.name.startswith(documento)):
    #             account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line.id),('date','<=',line.date)])                   
    #             if account_move_line.date==False:
    #                 suma_documento+=line.amount
    #                 if documento=='CHEQUE':
    #                     circulacion+=line.amount
    #                     cheques_circulacion.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
    #                 else:
    #                     lista_documento.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
    #             else:
    #                 suma_documento+=line.amount
    #                 if documento=='CHEQUE':
    #                     pagados+=line.amount 
    #                 lista_documento.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'S'})                                    

    #             if line.id not in lista_ids:
    #                 lista_ids.append(line.id)

    #         conciliacion[documento]=lista_documento
    #         conciliacion['ch_circulacion']=circulacion
    #         conciliacion['ch_pagados']=pagados
    #         conciliacion['CIRCULACION']=cheques_circulacion

    #     for line in account_bank_statement.line_ids.filtered(lambda l: l.id not in lista_ids):
    #         account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line.id)])
    #         if account_move_line.date==False:
    #             lista_otros.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'N'})
    #         else:
    #             lista_otros.append({'line_fecha':line.date,'line_name':line.name,'line_amount':line.amount,'conciliado':'S'})     
    #     conciliacion['otros']=lista_otros
    #     lista_conciliacion.append(conciliacion)
    #     # print('conciliacion>',conciliacion)

    #     return lista_conciliacion
