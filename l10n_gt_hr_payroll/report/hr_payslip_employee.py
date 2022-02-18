from odoo import api, fields, models, _
import logging
from . import letras


class Payslip(models.Model):
    # Heredo el modelo
    _inherit = 'hr.payslip'

    start_date_month = fields.Date(string="Fecha Inicial", compute='compute_start_date')

    # Defino la función que almacena la información en un dicionario.
    def datos_boleta(self):
        diccionario = {}
        lista = []

        moneda = self.currency_id.symbol
        moneda_nombre = self.currency_id.currency_unit_label
        diccionario["moneda_nombre"] = moneda_nombre
        diccionario["moneda"] = moneda
        diccionario["default"] = moneda + str(0.0)

        for d_trabajados in self.worked_days_line_ids:
            if d_trabajados.code=='WORK100':
                diccionario['D_LABORADOS']=d_trabajados.number_of_days

        for item in self.line_ids:
            diccionario[item.code] = moneda + str(format(round(item.amount,2),','))
            if item.code=="LIQRE":
                valor=item.amount
                if moneda_nombre=='Dolar' and letras.CENTIMOS_SINGULAR=='quetzal':
                    diccionario["letras"]= str(letras.numero_a_moneda(valor)).replace('quetzal','dolar').upper()
                if moneda_nombre=='Dolar' and letras.CENTIMOS_SINGULAR =='quetzales':
                    diccionario["letras"]= str(letras.numero_a_moneda(valor)).replace('quetzales','dolares').upper()
                else:
                    diccionario["letras"]= str(letras.numero_a_moneda(valor)).upper()
        lista.append(diccionario)

        return lista

    def compute_start_date(self):
        for rec in self:
            rec.start_date_month = rec.date_from.strftime('%Y-%m-01')
            if rec.contract_id.date_start > rec.start_date_month:
                rec.start_date_month = rec.contract_id.date_start
