# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from . import letras
from datetime import date,timedelta
class AccountMove(models.Model):
    _inherit = "account.move"

    def fecha(self):
        if self.invoice_date:
            EndDate = self.invoice_date + timedelta(days=30)
            return '{}/{}/{}'.format(EndDate.day,EndDate.month,EndDate.year)
        else:
            return False

    #Funcion encargada de devolver un monto dado numericamente a un monto en letras
    def monto_letras(self,importe):
        #Verificar el tipo de moneda
        enletras = letras
        cantidadenletras = enletras.to_word(importe)
        if self.currency_id.name == 'USD':
            cantidadenletras = cantidadenletras.replace('QUETZALES','DOLARES')
        elif self.currency_id.name == 'EUR':
            cantidadenletras = cantidadenletras.resultado('QUETZALES','EUROS')
        else:
            cantidadenletras = cantidadenletras
        return cantidadenletras

    def _referencia_interna(self):
        largo = 25
        for d in self:
            if d.ref:
                if len(d.ref) > largo:
                    d.referencia_interna = d.ref[0:largo]
                else:
                    d.referencia_interna = d.ref
            else:
                d.referencia_interna = ''

    def get_info_document(self):
        resultado = {'fecha_emision':'','numero_autorizacion':'','motivo':'','fel_serie':'','fel_numero':''}
        factura_referencia = None
        if self.journal_id.tipo_documento in ['NDEB']:
            factura_referencia = self.fel_factura_referencia_id
        else:
            factura_referencia = self.reversed_entry_id

        if factura_referencia:
            resultado['fecha_emision'] = factura_referencia.fecha_certificacion
            resultado['numero_autorizacion'] = factura_referencia.fel_firma
            resultado['motivo'] = self.fel_motivo
            resultado['fel_serie'] = factura_referencia.fac_serie
            resultado['fel_numero'] = factura_referencia.fac_numero
        return resultado

    def linea_blanco(self, contador):
        linea_blanco = {
            'linea': contador,
            'blanco': True,
        }
        return linea_blanco

    def nueva_linea(self, cadena, largo_lineas):
        largo = largo_lineas
        nueva_desc = []

        while True:
            if len(cadena) > largo:
                nueva_cadena = cadena[0:largo]
                x = nueva_cadena.rfind(' ')
                #El siguiente codigo es para validar si no existe un espacion que encontrar entonces lo corta por el largo
                if x < 0:
                    x = largo
                nueva_cadena = cadena[0:x]
                nueva_desc.append(nueva_cadena)
                cadena = cadena[x+1:len(cadena)]
            else:
                nueva_desc.append(cadena)
                break
        return nueva_desc

    def detalle_factura(self):
        num_linea_x_pagina = 35
        largo_lineas = 90
        o = self

        lineas = []
        pagina = []
        i=0
        nlinea = 0
        for l in o.invoice_line_ids.filtered(lambda l: l.price_total > 0):
            #El siguiente ciclo es para cepara la descripcion en varias lineas si supera la logintud de 30 caracteres
            mostrar_contenido = True #Variable que me sirve solo para mostrar contenido en la primera linea, cuando la descripcion supera la linea
            for nueva_linea_desc in self.nueva_linea(l.name, largo_lineas):
                linea = {}
                i += 1
                linea['linea'] = i
                linea['blanco'] = False
                linea['default_code'] = l.product_id.default_code  if mostrar_contenido else ''
                linea['quantity'] = '{0:,.0f}'.format(l.quantity) if mostrar_contenido else ''
                linea['product_uom_name'] = (l.product_uom_id.name if l.product_uom_id.name != 'Unidades' else 'U') if mostrar_contenido else ''
                linea['name'] = nueva_linea_desc
                linea['price_unit'] = o.currency_id.symbol + ' ' + '{0:,.2f}'.format(l.price_unit) if mostrar_contenido else ''
                linea['price_total'] = o.currency_id.symbol + ' ' + '{0:,.2f}'.format(l.price_total) if mostrar_contenido else ''
                lineas.append(linea)
                nlinea = i % num_linea_x_pagina
                #self.nueva_linea(linea['name'])
                #print("Numero de linea (%s)  ---   (%s)   texto-largo(%s)(%s)" % (str(i), str(nlinea), len(linea['name']), linea['name']))
                if nlinea == 0:
                    pagina.append(lineas)
                    lineas = []
                mostrar_contenido = False
        if len(lineas) >= 0:
            pagina.append(lineas)


        for x in range(nlinea, num_linea_x_pagina):
            i += 1
            lineas.append(self.linea_blanco(i))


        # for p in pagina:
        #     print("------------------------------------")
        #
        #     for a in p:
        #         print(a)
        return pagina



    def _compute_no_linea(self):
        self.no_linea = 0