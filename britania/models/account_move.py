# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from . import letras
from datetime import date,timedelta
import logging
import pytz
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
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
                combustible = {'gasoline':'Gasolina','diesel':'Diesel','lpg':'GLP','electric':'Electrico','hybrid':'Hibrido'}
                resultado = {
                'Tipo vehiculo':'Tipo vehiculo : {}'.format(vehiculo.tipo_vehiculo.capitalize() if vehiculo.tipo_vehiculo else ''),
                'Transmision':'Transmision : {}'.format('Automatica' if vehiculo.transmission == 'automatic' else 'Manual'),
                'Marca':'Marca : {}'.format(vehiculo.model_id.brand_id.name if vehiculo.model_id and vehiculo.model_id.brand_id else ''),
                'Modelo':'Modelo : {}'.format(vehiculo.model_year),
                'CC':'CC : {}'.format(vehiculo.cc),
                'Asientos':'Asientos : {}'.format(vehiculo.seats),
                'Linea':'Linea : {}'.format(vehiculo.model_id.name if vehiculo.model_id else ''),
                'VIN/CHASIS':'VIN/CHASIS : {}'.format(vehiculo.vin_sn),
                'Motor':'Motor : {}'.format(vehiculo.motor),
                'Cilindros':'Cilindros : {}'.format(vehiculo.cilindros),
                'Color':'Color : {}'.format(vehiculo.color),
                'Combustible':'Combustible : {}'.format(combustible[vehiculo.fuel_type]),
                'Puertas':'Puertas : {}'.format(vehiculo.doors),
                'Ejes':'Ejes : {}'.format(str(vehiculo.ejes) if vehiculo.ejes else ''),
                'Tonelaje':'Tonelaje : {}'.format(str(vehiculo.tonelaje) if vehiculo.tonelaje else 0),
                }
                if vehiculo.aduana and vehiculo.aduana != '':
                    resultado['Aduana'] = 'Aduana: {}'.format(vehiculo.aduana if vehiculo.aduana else False)

                if vehiculo.poliza and vehiculo.poliza != '':
                    resultado['Poliza'] = 'Poliza: {}'.format(vehiculo.poliza if vehiculo.poliza else False)
                if tipo==1:
                    return resultado
                elif tipo!=1:
                    return '\n'.join(str(x) for x in resultado.values())

    #Funcion encargada de devolver un monto dado numericamente a un monto en letras
    def monto_letras(self,importe):
        #Verificar el tipo de moneda
        enletras = letras
        cantidadenletras = enletras.to_word(importe)
        if self.company_id.currency_id.name == 'USD':
            cantidadenletras = cantidadenletras.replace('QUETZALES','DOLARES')
        elif self.company_id.currency_id.name == 'EUR':
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

    def generate_qr(self):
        if qrcode and base64:
            if self.fel_firma:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                if self.partner_id.vat:
                    nit_emisor = self.partner_id.vat
                else:
                    nit_emisor = 'CF'
                if self.fel_url:
                    qr.add_data(self.fel_url)
                else:
                    qr.add_data('https://felpub.c.sat.gob.gt/verificador-web/publico/vistas/verificacionDte.jsf?tipo=autorizacion&numero={}&emisor={}&receptor={}&monto={}'.format(self.fel_firma,self.company_id.vat.replace('-',''),nit_emisor.replace('-',''),self.amount_total))
                qr.make(fit=True)

                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                return qr_image
            else:
                return False
        else:
            return False

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
        pagina = {}
        detalle = []
        total = {}
        i=0
        nlinea = 0
        linea={}
        gran_total = gran_subtotal = gran_total_impuestos = total_descuento = total_sin_descuento = 0
        get_fac_doc = self.get_detalle_factura()

        for linea_factura in get_fac_doc['detalle']:
            l = linea_factura['dato_linea']
            if l.quantity > 0:
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
                        linea['quantity'] = '{0:,.2f}'.format(l.quantity) if mostrar_contenido else ''
                        linea['nombre_sin_codigo'] = l.product_id.name
                        linea['product_uom_name'] = (l.product_uom_id.name if l.product_uom_id.name != 'Unidades' else 'U') if mostrar_contenido else ''
                        linea['name'] = descripcion[d]
                        linea['price_unit'] = o.company_id.currency_id.symbol + ' ' + '{0:,.2f}'.format(linea_factura['precio_sin_descuento']) if mostrar_contenido else ''
                        linea['price_total'] = o.company_id.currency_id.symbol + ' ' + '{0:,.2f}'.format(linea_factura['total_linea_sin_descuento']) if mostrar_contenido else ''
                        linea['discount'] = str('{0:,.2f}'.format(l.discount))+"%" if mostrar_contenido else ''
                        lineas.append(linea)
                        nlinea = i % num_linea_x_pagina
                        if nlinea == 0:
                            detalle.append(lineas)
                            lineas = []
                        mostrar_contenido = False

                else:
                    for nueva_linea_desc in self.nueva_linea(l.name, largo_lineas):
                        linea = {}
                        i += 1
                        linea['linea'] = i
                        linea['blanco'] = False
                        linea['default_code'] = l.product_id.default_code  if mostrar_contenido else ''
                        linea['quantity'] = '{0:,.2f}'.format(l.quantity) if mostrar_contenido else ''
                        linea['product_uom_name'] = (l.product_uom_id.name if l.product_uom_id.name != 'Unidades' else 'U') if mostrar_contenido else ''
                        linea['name'] = nueva_linea_desc
                        linea['nombre_sin_codigo'] = l.product_id.name
                        linea['price_unit'] = o.company_id.currency_id.symbol + ' ' + '{0:,.2f}'.format(linea_factura['precio_sin_descuento']) if mostrar_contenido else ''
                        linea['price_total'] = o.company_id.currency_id.symbol + ' ' + '{0:,.2f}'.format(linea_factura['total_linea_sin_descuento']) if mostrar_contenido else ''
                        linea['discount'] = str('{0:,.2f}'.format(l.discount))+"%" if mostrar_contenido else ''
                        lineas.append(linea)
                        nlinea = i % num_linea_x_pagina
                        #self.nueva_linea(linea['name'])
                        #print("Numero de linea (%s)  ---   (%s)   texto-largo(%s)(%s)" % (str(i), str(nlinea), len(linea['name']), linea['name']))
                        if nlinea == 0:
                            detalle.append(lineas)
                            lineas = []
                        mostrar_contenido = False
        tot = get_fac_doc['totales']
        total['gran_total'] = tot['total_sin_descuento']
        total['gran_subtotal'] = tot['total_descuento']
        total['gran_total_impuestos'] = tot['total_total']
        if len(lineas) >= 0:
            detalle.append(lineas)


        for x in range(nlinea, num_linea_x_pagina):
            i += 1
            lineas.append(self.linea_blanco(i))


        # for p in pagina:
        #     print("------------------------------------")
        #
        #     for a in p:
        #         print(a)
        pagina['detalle'] = detalle
        pagina['total'] = total

        return pagina



    def _compute_no_linea(self):
        self.no_linea = 0
