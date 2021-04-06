# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from . import letras
from datetime import date,timedelta
import logging
class AccountMove(models.Model):
    _inherit = "account.move"

    def fecha(self):
        if self.invoice_date:
            EndDate = self.invoice_date + timedelta(days=30)
            return '{}/{}/{}'.format(EndDate.day,EndDate.month,EndDate.year)
        else:
            return False

    def obtener_tasa_cambio(self):
        tasa = rate = 1
        if self.currency_id.id != self.company_id.currency_id.id:
            rate = self.currency_id
            rate = rate.with_context(dict(self._context or {}, date=self.invoice_date)).rate
            if rate:
                tasa = tasa / rate
                rate = rate
            else:
                rate = self.env['res.currency'].search([('id','=',self.currency_id.id)])
                tasa = tasa/rate.rate
                rate = rate.rate
        return rate

    #Funcion encargada de retornar la descripcion de un producto
    def get_descripcion(self,line_id,tipo=1):
        if line_id:
            if line_id.product_id.is_vehicle:
                vehiculo = self.env['fleet.vehicle'].sudo().search([('product_id','=',line_id.product_id.id)])
                combustible = ''
                if vehiculo.fuel_type == 'gasoline':
                    combustible = 'Gasolina' 
                elif vehiculo.fuel_type == 'diesel':
                    combustible = 'Diesel'
                elif vehiculo.fuel_type == 'lpg':
                    combustible = 'GLP'
                elif vehiculo.fuel_type == 'electric':
                    combustible = 'Electrico'
                elif combustible == 'hybrid':
                    combustible = 'Hibrido'
                if vehiculo and tipo == 1:
                    resultado = {
                    'name':vehiculo.name,
                    'tipo_vehiculo':'Tipo vehiculo : {}'.format(vehiculo.tipo_vehiculo if vehiculo.tipo_vehiculo else ''),
                    'tonelaje':'Tonelaje :'.format(vehiculo.tonelaje if vehiculo.tonelaje else ''),
                    'transmision':'Transmision : {}'.format('Automatica' if vehiculo.transmission == 'automatic' else 'Manual'),
                    'tipo_combustible':'Combustible {}'.format(combustible),
                    'co2':'Emisiones de Co2: {}'.format(vehiculo.co2),
                    'potencia':'Potencia: {}'.format(vehiculo.power),
                    'vin':'VIN/CHASIS: {}'.format(vehiculo.vin_sn),
                    'asientos':'Asientos: {}'.format(vehiculo.seats),
                    'doors':'Puertas: {}'.format(vehiculo.doors),
                    'modelo':'Modelo: {}'.format(vehiculo.model_year),
                    'color':'Color: {}'.format(vehiculo.color),
                    'Placa':'Placa: {}'.format(vehiculo.license_plate),
                    'Aduana':'Aduana: {}'.format(vehiculo.aduana if vehiculo.aduana else ''),
                    'Poliza':'Poliza: {}'.format(vehiculo.poliza if vehiculo.poliza else ''),
                    }
                    return resultado
                elif vehiculo and tipo != 1:
                    resultado = """%s
TIPO VEHICULO   : %s
TONELAJE    : %s
TRANSMISION        : %s
COMBUSTIBLE       : %s
EMISIONES DE CO2           : %s
POTENCIA     : %s
VIN/CHASIS        : %s
ASIENTOS   : %s
PUERTAS     : %s
MODELO    : %s
COLOR        : %s
PLACA  : %s
ADUANA : %s
POLIZA : %s
"""
                return (resultado % (vehiculo.name
                    ,vehiculo.tipo_vehiculo if vehiculo.tipo_vehiculo else ''
                    ,vehiculo.tonelaje if vehiculo.tonelaje else ''
                    ,'Automatica' if vehiculo.transmission == 'automatic' else 'Manual'
                    ,combustible
                    ,vehiculo.co2
                    ,vehiculo.power
                    ,vehiculo.vin_sn
                    ,vehiculo.seats
                    ,vehiculo.doors
                    ,vehiculo.model_year
                    ,vehiculo.color
                    ,vehiculo.license_plate
                    ,vehiculo.aduana if vehiculo.aduana else ''
                    ,vehiculo.poliza if vehiculo.poliza else ''))



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
            if l.product_id.is_vehicle:
                descripcion = self.get_descripcion(l,1)
                for d in descripcion:
                    linea = {}
                    i += 1
                    linea['linea'] = i
                    linea['blanco'] = False
                    linea['default_code'] = l.product_id.default_code  if mostrar_contenido else ''
                    linea['quantity'] = '{0:,.0f}'.format(l.quantity) if mostrar_contenido else ''
                    linea['product_uom_name'] = (l.product_uom_id.name if l.product_uom_id.name != 'Unidades' else 'U') if mostrar_contenido else ''
                    linea['name'] = descripcion[d]
                    linea['price_unit'] = o.currency_id.symbol + ' ' + '{0:,.2f}'.format(l.price_unit) if mostrar_contenido else ''
                    linea['price_total'] = o.currency_id.symbol + ' ' + '{0:,.2f}'.format(l.price_total) if mostrar_contenido else ''
                    lineas.append(linea)
                    nlinea = i % num_linea_x_pagina
                    if nlinea == 0:
                        pagina.append(lineas)
                        lineas = []
                    mostrar_contenido = False

            else:
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