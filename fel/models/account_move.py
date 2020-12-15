# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero
from . import fel

import logging
import pytz

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    fel_setting_id = fields.Many2one('fel.setting', string='Facturacion FEL', copy=False, readonly=True, track_visibility='onchange')
    fel_firma = fields.Char('Firma FEL', copy=False, readonly=True, track_visibility='onchange')

    fecha_certificacion = fields.Char(string='Fecha certificacion',copy=False,readonly=True)

    def getNitFelFormat(self, nit):
        if nit:
            nit = nit.upper()
            if nit == 'C/F':
                return 'CF'
            if nit == '':
                return 'CF'
            nit = nit.replace('-','')
            return nit
        return 'CF'

    def getListFactura(self):
        factura = self

        fel_setting = factura.journal_id.fel_setting_id
        tipo_documento = factura.journal_id.tipo_documento

        documento = {}
        documento["factura_id"] = str(factura.id)
        documento["CodigoMoneda"] = factura.currency_id.name
        documento["FechaHoraEmision"] = fields.Date.from_string(factura.invoice_date).strftime('%Y-%m-%dT%H:%M:%S')
        documento["Tipo"] = tipo_documento
        documento["AfiliacionIVA"] = factura.journal_id.afiliacion_iva
        documento["CodigoEstablecimiento"] = fel_setting.cod_establecimiento
        documento["NITEmisor"] = factura.company_id.vat.replace('-','')
        documento["NombreComercial"] = fel_setting.nombre_comercial


        #DireccionEmisor
        documento["ECorreoEmisor"] = fel_setting.emisor.email or ''
        documento["ENombreEmisor"] = fel_setting.emisor.name
        documento["EDireccionEmisor"] = fel_setting.emisor.street or 'Ciudad'
        documento["ECodigoPostal"] = fel_setting.emisor.zip or '01001'
        documento["EMunicipio"] = fel_setting.emisor.city or 'Guatemala'
        documento["EDepartamento"] = fel_setting.emisor.state_id.name or 'Guatemala'
        documento["EPais"] = fel_setting.emisor.country_id.code or 'GT'

        #Receptor
        documento["IDReceptor"] = self.getNitFelFormat(factura.partner_id.vat) if factura.partner_id.vat else 'CF'
        documento["NombreReceptor"] = factura.partner_id.name
        documento["CorreoReceptor"] = factura.partner_id.email or ''

        if factura.journal_id.tipo_documento == "FESP":
            documento["IDReceptor"] = factura.partner_id.cui
            documento["TipoEspecial"] = "CUI"

        documento["ReceptorDireccion"] = factura.partner_id.street or 'Ciudad'
        documento["ReceptorCodigoPostal"] = factura.partner_id.zip or '01009'
        documento["ReceptorMunicipio"] = factura.partner_id.city or 'Guatemala'
        documento["ReceptorDepartamento"] = factura.partner_id.state_id.name if factura.partner_id.state_id else 'Guatemala'
        documento["ReceptorPais"] = factura.partner_id.country_id.code or 'GT'

        #Frases
        frases = []
        existen_frases = False
        for frase_escenario in factura.journal_id.fel_frases_ids:
            existen_frases = True
            escenario = {}
            escenario["TipoFrase"] = frase_escenario.fel_tipofrase.code
            escenario["CodigoEscenario"] = frase_escenario.fel_escenario.code
            frases.append(escenario)
        if existen_frases:
            documento["Frases"] = frases

        #Items
        items = []
        gran_total = gran_subtotal = gran_total_impuestos = 0
        for detalle in factura.invoice_line_ids:
            linea = {}
            linea["BienOServicio"] = "S"  if detalle.product_id.type == "service" else "B"
            linea["Cantidad"] = detalle.quantity
            linea["UnidadMedida"] = detalle.product_uom_id.name
            linea["Descripcion"] = detalle.name
            precio_sin_descuento = detalle.price_unit
            linea["PrecioUnitario"] = '{:.2f}'.format(precio_sin_descuento)
            linea["Precio"] = '{:.2f}'.format(precio_sin_descuento * detalle.quantity)
            precio_unitario = detalle.price_unit * (100-detalle.discount) / 100
            descuento = precio_sin_descuento * detalle.quantity - precio_unitario * detalle.quantity
            linea["Descuento"] = '{:.6f}'.format(descuento)

            #Impuestos
            precio_unitario_base = detalle.price_subtotal / detalle.quantity
            total_linea = precio_unitario * detalle.quantity
            total_linea_base = precio_unitario_base * detalle.quantity
            total_impuestos = total_linea - total_linea_base

            if total_impuestos != 0:
                linea["NombreCorto"] = "IVA"
                linea["CodigoUnidadGravable"] = "2" if factura.journal_id.tipo_operacion == 'EXPO' else "1"
                linea["MontoGravable"] = '{:.2f}'.format(factura.currency_id.round(total_linea_base))
                linea["MontoImpuesto"] = '{:.2f}'.format(factura.currency_id.round(total_impuestos))
            linea["Total"] = '{:.2f}'.format(factura.currency_id.round(total_linea))

            gran_total += factura.currency_id.round(total_linea)
            gran_subtotal += factura.currency_id.round(total_linea_base)
            gran_total_impuestos += factura.currency_id.round(total_impuestos)



            items.append(linea)
        documento["Items"] = items
        documento["gran_total_impuestos"] = gran_total_impuestos
        documento["TotalMontoImpuesto"] = '{:.2f}'.format(factura.currency_id.round(gran_total_impuestos))
        documento["GranTotal"] = '{:.2f}'.format(factura.currency_id.round(gran_total))

        documento["Adenda"] = factura.name

        #Complementos
        documento["Complementos"] = False
        #Notas de credito o debito
        if tipo_documento in ['NDEB', 'NCRE']:
            documento["Complementos"] = True
            if factura.refund_invoice_id:
                #Este if es para identificar si no tiene firma, es del regimen anterior, se realiza por medio de buscar FACE en la descripcion de la serie.
                if factura.refund_invoice_id.fel_serie.find("FACE")>=0:
                    documento["RegimenAntiguo"] = "Antiguo"
                    documento["FechaEmisionDocumentoOrigen"] = fields.Date.from_string(factura.invoice_date).strftime('%Y-%m-%dT%H:%M:%S')
                    documento["MotivoAjuste"] = factura.name
                    documento["NumeroAutorizacionDocumentoOrigen"] = factura.refund_invoice_id.fel_firma
                    documento["NumeroDocumentoOrigen"] = factura.refund_invoice_id.fel_numero
                    documento["SerieDocumentoOrigen"] = factura.refund_invoice_id.fel_serie
                else:
                    documento["RegimenAntiguo"] = "Actual"
                    documento["FechaEmisionDocumentoOrigen"] = str(factura.refund_invoice_id.invoice_date)
                    documento["MotivoAjuste"] = factura.name
                    documento["NumeroAutorizacionDocumentoOrigen"] = factura.refund_invoice_id.fel_firma
                    documento["NumeroDocumentoOrigen"] = factura.refund_invoice_id.fel_numero
                    documento["SerieDocumentoOrigen"] = factura.refund_invoice_id.fel_serie

        #Factura CompCambiaria
        elif tipo_documento in ['FCAM']:
            documento["Complementos"] = True
            documento["FCAM_NumeroAbono"] = "1"
            documento["FCAM_FechaVencimiento"] = str(factura.invoice_date)
            documento["FCAM_MontoAbono"] = '{:.2f}'.format(factura.currency_id.round(gran_total))

        #Factura Especial
        elif tipo_documento in ['FESP']:
            documento["Complementos"] = True
            total_isr = abs(factura.amount_tax)
            total_iva_retencion = 0
            for impuesto in factura.tax_line_ids:
                if impuesto.amount > 0:
                    total_iva_retencion += impuesto.amount

            documento["FESP_RetencionISR"] = str(total_isr)
            documento["FESP_RetencionIVA"] = str(total_iva_retencion)
            documento["FESP_TotalMenosRetenciones"] = str(factura.amount_total)

        return documento

    def firmar_factura_INFILE(self, documento, batch, anulacion):
        factura = self

        fel_setting = factura.journal_id.fel_setting_id

        factura.fel_setting_id = fel_setting.id


        fel_dte = fel.Fel()
        if anulacion:
            fel_dte.anular(documento)
        else:
            fel_dte.getXmlFormat(documento)

        fel_dte.setDatosConexion(
            fel_setting.token,
            fel_setting.clave,
            fel_setting.usuario,
            documento["NITEmisor"],
            "jrivera@bavaria.com.gt",
            documento["factura_id"],
        )
        print("--------------------------------------------------------")
        print(documento["factura_id"])
        try:
            firmado = fel_dte.firmar_xml(anulacion)
            logging.info(firmado)
        except IOError as e:
            _logger.exception("\n\n Error de Conexion-------------------------------")

            error_msg = _("Something went wrong during your conexion\n``%s``") % str(e)
            _logger.exception("\n\n" + error_msg)
            raise self.env['res.config.settings'].get_config_warning(error_msg)

        if not firmado["resultado"]:
            _logger.exception("\n\n Error de Factura(%s)-------------------------------" % (factura.id))
            _logger.exception("\n\n" + str(fel_dte.xmls_file))
            _logger.exception("\n\n Error de Firma de Factura(%s)-------------------------------" % (factura.id))
            _logger.exception("\n\n" + fel_dte.xmls_file_firmado)
            if not batch:
                raise UserError(firmado["descripcion"])

        fel_certificacion_response = fel_dte.certificar_xml(anulacion)

        if not fel_certificacion_response["resultado"]:
            mensaje_error = ''
            for m in fel_certificacion_response["descripcion_errores"]:
                mensaje_error = str(m)
            _logger.exception("\n\nFactura(%s)-------------------------------" % (factura.id))
            _logger.exception("\n\n" + str(fel_dte.xmls))
            _logger.exception("\n\nError de Certificado de Factura(%s)-------------------------------" % (factura.id))
            _logger.exception("\n\n" + fel_dte.xmls_file_certificado)
            if not batch:
                raise UserError(mensaje_error)

        if not firmado["resultado"] or not fel_certificacion_response["resultado"]:
            msg="Error generando Factura Electronica FEL"
            attachments = [('Factura.xml', fel_dte.xmls_file),('Firmado.json', fel_dte.xmls_file_firmado),('Certificado.json', fel_dte.xmls_file_certificado)]
            factura.message_post(subject='FEL', body=mensaje_error, attachments=attachments)

        if factura.journal_id.fel_setting_id:
            if factura.journal_id.fel_setting_id.attach_xml:
                msg="Generando Factura Electronica FEL"
                attachments = [('Factura.xml', fel_dte.xmls_file),('Firmado.json', fel_dte.xmls_file_firmado),('Certificado.json', fel_dte.xmls_file_certificado)]
                self.message_post(subject='FEL', body=msg, attachments=attachments)
        if fel_certificacion_response["resultado"]:
            logging.info(fel_certificacion_response)
            factura.fel_firma = fel_certificacion_response["uuid"]
            #factura.name = str(fel_certificacion_response["serie"])+"-"+str(fel_certificacion_response["numero"])
            factura.fac_serie = fel_certificacion_response["serie"]
            factura.fac_numero = fel_certificacion_response["numero"]
            factura.fecha_certificacion = fel_certificacion_response["fecha"]
            msg = "https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid="+fel_certificacion_response["uuid"]
            factura.message_post(subject='FEL', body=msg)

    def firmar_factura(self, documento, batch, anulacion):
        factura = self

        fel_setting = factura.journal_id.fel_setting_id

        factura.fel_setting_id = fel_setting.id


        fel_dte = fel.Fel()
        if anulacion:
            fel_dte.anular(documento)
        else:
            fel_dte.getXmlFormat(documento)

        fel_dte.setDatosConexion(
            fel_setting.token,
            fel_setting.clave,
            fel_setting.usuario,
            fel_setting.demo,
            documento["NITEmisor"],
            "jrivera@bavaria.com.gt",
            documento["factura_id"],
            documento,
        )
        try:

#=======================================>
            #Realizo la primera conexion para mandar a firmar
            result_firmado = fel_dte.firmar_xml_4gs("SYSTEM_REQUEST", anulacion)
            #Servidor logra realizar conexion
            codigo_error = 0
            if fel_dte.xml_response.status_code == 200:
                resultado = {}
                codigo_error = result_firmado["{http://www.fact.com.mx/schema/ws}Code"]

                #Si el codigo es 9, quiere decir que la factura ya habia sido enviada.
                if result_firmado["{http://www.fact.com.mx/schema/ws}Code"] == "1":

                    fel_dte.documentuid = result_firmado['{http://www.fact.com.mx/schema/ws}DocumentGUID']
                    resultado = fel_dte.respuesta_firma(result_firmado["{http://www.fact.com.mx/schema/ws}ResponseData1"])


                #Si el codigo es 9, quiere decir que la factura ya habia sido enviada.
                elif result_firmado["{http://www.fact.com.mx/schema/ws}Code"] in ("9","999"):
                    #Busco el UUID para buscar el numero de la factura
                    result_firmado_code9 = fel_dte.firmar_xml_4gs("LOOKUP_ISSUED_INTERNAL_ID", False)

                    #Con el UUID, puedo traer la informacion de la factura que ya habia sido firmada.
                    fel_dte.documentuid = result_firmado_code9['{http://www.fact.com.mx/schema/ws}DocumentGUID']
                    result_firmado_code9_getdocument = fel_dte.firmar_xml_4gs("GET_DOCUMENT", False)

                    resultado = fel_dte.respuesta_firma(result_firmado_code9_getdocument["{http://www.fact.com.mx/schema/ws}ResponseData1"])

                else:
                    raise UserError(result_firmado["{http://www.fact.com.mx/schema/ws}Description"])

                print(resultado)
                if resultado:
                    fecha_certificacion = ''
                    try:
                        import xml.etree.ElementTree as ET
                        tree = ET.fromstring(resultado['XML_Factura'].decode('utf-8'))
                        if tree:
                            fecha_certificacion = tree[0][0][1][3].text
                    except Exception as e:
                        pass
                    factura.fel_firma = resultado["NumeroAutorizacion"]
                    #factura.name = str(fel_certificacion_response["serie"])+"-"+str(fel_certificacion_response["numero"])
                    factura.fac_serie = resultado["Serie"]
                    factura.fac_numero = resultado["Numero"]
                    factura.fecha_certificacion = fecha_certificacion

                    _logger.info("Factura Firmada id(%s), %s" % (documento["factura_id"],result_firmado["{http://www.fact.com.mx/schema/ws}Description"]))

#=========================>
#Me quede aqui, en teoria, es de recuperar la serie de la factura, y despues arreglar todo este desorden de codigo.

            else:
                _logger.exception("No se logra realizar conexion FEL")
        except IOError as e:
            _logger.exception("\n\n Error de Conexion-------------------------------")

            error_msg = _("Something went wrong during your conexion\n``%s``") % str(e)
            _logger.exception("\n\n" + error_msg)
            raise self.env['res.config.settings'].get_config_warning(error_msg)

    def action_post(self):
        move = super(AccountMove,self).action_post()
        if self.journal_id.fel_setting_id and self.state == 'posted':
            if not self.invoice_date:
                raise UserError(_("No puede utilizar este diario, solo se puede utilizar desde una venta."))
            documento = self.getListFactura()
            self.firmar_factura(documento, False, False)

        return move


    def button_draft_fel(self):
        move = super(AccountMove,self).button_draft()
        move = super(AccountMove,self).button_cancel()
        fel_dte = fel.Fel()
        for factura in self:
            if factura.fel_setting_id:
                documento = {}
                documento["FechaHoraAnulacion"] = fields.datetime.now(pytz.timezone(self.env.user.tz or 'UTC')).strftime('%Y-%m-%dT%H:%M:%S')
                documento["DatosAnulacion"] = "DatosAnulacion"
                documento["NITEmisor"] = factura.company_id.vat.replace('-','')
                documento["FechaEmisionDocumentoAnular"] = factura.invoice_date.strftime('%Y-%m-%dT%H:%M:%S')
                documento["IDReceptor"] = self.getNitFelFormat(factura.partner_id.vat) if factura.partner_id.vat else 'CF'
                if factura.journal_id.tipo_documento == "FESP":
                    documento["IDReceptor"] = factura.partner_id.cui
                documento["NumeroDocumentoAAnular"] = factura.fel_firma
                documento["MotivoAnulacion"] = "Cancelacion de Factura"
                documento["factura_id"] = str(factura.id)

                factura.firmar_factura(documento, False, True)



class AccountMoveConfirmFEL(models.TransientModel):
    """
    Timbrar facturas en FEL
    """

    _name = "account.move.confirm.fel"
    _description = "Confirm the selected invoices in FEL"

    def invoice_confirm_fel(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for factura in self.env['account.move'].browse(active_ids):
            if factura.state in ['open'] and factura.journal_id.fel_setting_id and not factura.fel_firma:
                documento = factura.getListFactura()
                factura.firmar_factura(documento, True, False)
                print("Firmo----------------------------------------------------------")
            else:
                print("NooooooooooooFirmo----------------------------------------------------------")


        return {'type': 'ir.actions.act_window_close'}
