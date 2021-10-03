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
                'estado':account_bank_statement.state,
            }

        saldo_inicial=account_bank_statement.balance_start
        conciliacion_bancaria=[]
        cheques_circulacion=[]
        suma_circulacion=0
        suma_pagados=0
        total=0
        for documento in DOCUMENTOS_BANCARIOS:
            lista_documento=[]
            suma_documento=0
            lines=filter(lambda d: d[0] ==documento, account_bank_statement_lines)
            for line in lines:
                account_move_line=request.env['account.move.line'].search([('statement_line_id','=',line[1].id)])

                if len(account_move_line)==0:
                    fecha=line[1].date
                    move_name=line[1].name
                    monto=line[1].amount
                    if documento=='CH':
                            suma_circulacion+=line[1].amount
                            cheques_circulacion.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'N'})
                    else:
                        suma_documento+=line[1].amount
                        lista_documento.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'N'})
                else:
                    for move_line in account_move_line:
                        if move_line.amount_currency !=0:
                            monto=move_line.amount_currency
                        else:
                            monto=move_line.balance

                        referencia=None
                        if line[1].ref !=False:
                            referencia=line[1].ref 

                        total+=monto
                        fecha=move_line.date.strftime('%d/%m/%Y')
                        move_name=move_line.move_name +' - '+ move_line.name +' REF - '+referencia

                        mes_movimiento=int(move_line.date.strftime('%m'))
                        mes_conciliacion=int(account_bank_statement.date.strftime('%m'))

                        #rev
                        if mes_movimiento > mes_conciliacion: 
                            if documento=='CH':
                                suma_pagados+=move_line.balance
                                suma_documento+=move_line.balance
                                lista_documento.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'R'})
                            else:
                                suma_documento+=move_line.balance
                                lista_documento.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'R'})
                        else:
                            if documento=='CH':
                                suma_pagados+=move_line.balance
                                suma_documento+=move_line.balance
                                lista_documento.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'S'})
                            else:
                                suma_documento+=move_line.balance
                                lista_documento.append({'line_fecha':fecha,'line_name':move_name,'line_amount':monto,'conciliado':'S'})
            
            conciliacion[documento]=lista_documento
            conciliacion['SUM_'+documento]=suma_documento
            conciliacion['SUM_CHC']=suma_circulacion
            conciliacion['CHC']=cheques_circulacion
            conciliacion['SALDO_CONTABLE']=saldo_inicial+total

        conciliacion_bancaria.append(conciliacion)

        # print("TOTAL--->",total)
        # for conciliacion in conciliacion_bancaria:
        #     print(conciliacion['banco'],'\n', conciliacion['diario'],'\n',conciliacion['fecha'],'\n',conciliacion['saldo_inicial'],'\n',conciliacion['saldo_final'])
        #     for doc in DOCUMENTOS_BANCARIOS:
        #         print(' DOCUMENTO>',doc)
        #         for documento in conciliacion[doc]:
        #             contador+=1
        #             print(contador,' >', documento['line_fecha'],'',documento['line_name'],'',documento['line_amount'],'',documento['line_fecha'],'',documento['conciliado'])
        
        return conciliacion_bancaria

    def lista_documentos_bancarios(self):
        DOCUMENTOS_BANCARIOS=[('CH','CHEQUES'),('CHC','CHEQUES EN CIRCULACION'),('DP','DEPOSITOS'),('NC','NOTAS DE CREDITO'),('ND','NOTAS DE DEBITO')]
        return DOCUMENTOS_BANCARIOS


    @api.model
    def _get_bank_rec_report_data(self, options, journal):
        # General data + setup
        rslt = {}

        accounts = journal.default_debit_account_id + journal.default_credit_account_id
        company = journal.company_id
        amount_field = 'balance' if (not journal.currency_id or journal.currency_id == journal.company_id.currency_id) else 'amount_currency'
        states = ['posted']
        states += options.get('all_entries') and ['draft'] or []

        # Get total already accounted.
        self._cr.execute('''
            SELECT SUM(aml.''' + amount_field + ''')
            FROM account_move_line aml
            LEFT JOIN account_move am ON aml.move_id = am.id
            WHERE aml.date <= %s AND aml.company_id = %s AND aml.account_id IN %s
            AND am.state in %s
        ''', [self.env.context['date_to'], journal.company_id.id, tuple(accounts.ids), tuple(states)])
        rslt['total_already_accounted'] = self._cr.fetchone()[0] or 0.0

        # Payments not reconciled with a bank statement line
        self._cr.execute('''
            SELECT
                aml.id,
                aml.name,
                aml.ref,
                aml.date,
                aml.''' + amount_field + '''                    AS balance,
                aml.payment_id
            FROM account_move_line aml
            LEFT JOIN res_company company                       ON company.id = aml.company_id
            LEFT JOIN account_account account                   ON account.id = aml.account_id
            LEFT JOIN account_account_type account_type         ON account_type.id = account.user_type_id
            LEFT JOIN account_bank_statement_line st_line       ON st_line.id = aml.statement_line_id
            LEFT JOIN account_payment payment                   ON payment.id = aml.payment_id
            LEFT JOIN account_journal journal                   ON journal.id = aml.journal_id
            LEFT JOIN account_move move                         ON move.id = aml.move_id
            WHERE aml.date <= %s
            AND aml.company_id = %s
            AND CASE WHEN journal.type NOT IN ('cash', 'bank')
                     THEN payment.journal_id
                     ELSE aml.journal_id
                 END = %s
            AND account_type.type = 'liquidity'
            AND full_reconcile_id IS NULL
            AND (aml.statement_line_id IS NULL OR st_line.date > %s)
            AND (company.account_bank_reconciliation_start IS NULL OR aml.date >= company.account_bank_reconciliation_start)
            AND move.state in %s
            ORDER BY aml.date DESC, aml.id DESC
        ''', [self._context['date_to'], journal.company_id.id, journal.id, self._context['date_to'], tuple(states)])
        rslt['not_reconciled_payments'] = self._cr.dictfetchall()

        # Bank statement lines not reconciled with a payment
        rslt['not_reconciled_st_positive'] = self.env['account.bank.statement.line'].search([
            ('statement_id.journal_id', '=', journal.id),
            ('date', '<=', self._context['date_to']),
            ('journal_entry_ids', '=', False),
            ('amount', '>', 0),
            ('company_id', '=', company.id)
        ])

        rslt['not_reconciled_st_negative'] = self.env['account.bank.statement.line'].search([
            ('statement_id.journal_id', '=', journal.id),
            ('date', '<=', self._context['date_to']),
            ('journal_entry_ids', '=', False),
            ('amount', '<', 0),
            ('company_id', '=', company.id)
        ])

        # Final
        last_statement = self.env['account.bank.statement'].search([
            ('journal_id', '=', journal.id),
            ('date', '<=', self._context['date_to']),
            ('company_id', '=', company.id)
        ], order="date desc, id desc", limit=1)
        rslt['last_st_balance'] = last_statement.balance_end
        rslt['last_st_end_date'] = last_statement.date

        return rslt
