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
        conciliacion_bancaria=self._procesar_conciliacion(account_bank_statement)
        return conciliacion_bancaria

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
                        documentos.append(('ND',line))
                    else:
                        documentos.append(('NC',line))
        return documentos


    def _procesar_conciliacion(self,account_bank_statement):
        account_bank_statement_lines=self._tipo_documentos(account_bank_statement)

        conciliacion={
                'banco':account_bank_statement.journal_id.bank_id.name,
                'diario':account_bank_statement.journal_id.name,
                'cuenta':account_bank_statement.journal_id.bank_account_id.acc_number,
                'fecha':account_bank_statement.date.strftime('%d/%m/%Y'),
                'saldo_inicial':account_bank_statement.balance_start,
                'saldo_final':account_bank_statement.balance_end_real,
                'moneda':account_bank_statement.currency_id.symbol,
            }

        saldo_inicial=account_bank_statement.balance_start
        conciliacion_bancaria=[]
        cheques_circulacion=[]
        suma_circulacion=0
        suma_pagados=0
        total=0
        contador=0
        for documento in DOCUMENTOS_BANCARIOS:
            lista_documento=[]
            suma_documento=0
            lines=filter(lambda d: d[0] ==documento, account_bank_statement_lines)
            for line in lines:
                total+=line[1].amount
                account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line[1].id),('date','<=',account_bank_statement.date)])
                fecha=line[1].date.strftime('%d/%m/%Y')
                if account_move_line.date==False:
                    if documento=='CH':
                        suma_circulacion+=line[1].amount
                        cheques_circulacion.append({'line_fecha':fecha,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
                    else:
                        suma_documento+=line[1].amount
                        lista_documento.append({'line_fecha':fecha,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'N'})
                else:
                    if documento=='CH':
                        suma_pagados+=line[1].amount
                        suma_documento+=line[1].amount
                        lista_documento.append({'line_fecha':fecha,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'S'})
                    else:
                        suma_documento+=line[1].amount
                        lista_documento.append({'line_fecha':fecha,'line_name':line[1].name,'line_amount':line[1].amount,'conciliado':'S'})
                
            conciliacion[documento]=lista_documento
            conciliacion['SUM_'+documento]=suma_documento
            conciliacion['SUM_CHC']=suma_circulacion
            conciliacion['CHC']=cheques_circulacion
            conciliacion['SALDO_CONTABLE']=total+saldo_inicial

        conciliacion_bancaria.append(conciliacion)

        print("TOTAL--->",total)
        for conciliacion in conciliacion_bancaria:
            print(conciliacion['banco'],'\n', conciliacion['diario'],'\n',conciliacion['fecha'],'\n',conciliacion['saldo_inicial'],'\n',conciliacion['saldo_final'])
            for doc in DOCUMENTOS_BANCARIOS:
                print(' DOCUMENTO>',doc)
                for documento in conciliacion[doc]:
                    contador+=1
                    print(contador,' >', documento['line_fecha'],'',documento['line_name'],'',documento['line_amount'],'',documento['line_fecha'],'',documento['conciliado'])
        
        return conciliacion_bancaria

    def lista_documentos_bancarios(self):
        DOCUMENTOS_BANCARIOS=[('CH','CHEQUES'),('CHC','CHEQUES EN CIRCULACION'),('DP','DEPOSITOS'),('NC','NOTAS DE CREDITO'),('ND','NOTAS DE DEBITO')]
        return DOCUMENTOS_BANCARIOS
