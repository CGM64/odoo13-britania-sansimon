# -*- coding: utf-8 -*-
from odoo import models,api
from datetime import datetime
from odoo.http import request

class LibroInventarioReportXls(models.AbstractModel):
    _name = 'report.l10n_gt_sat.account_inventario_report_xls'
    _description = 'Reporte Inventario XLS'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None


    def _facturas(self,fecha_inicio,fecha_fin):
        dominio = [
            ('state', 'in', ('posted','reconciled')),
            ('invoice_date', '>=', fecha_inicio),
            ('invoice_date', '<=', fecha_fin),
            ('journal_id.type', '=', 'purchase'),
            ('journal_id.code', 'in', ('FACTU','CEXT')),
        ]
        facturas= request.env['account.move'].search(dominio)
        return facturas

    def _stock_valuation_layer(self,fecha_inicio,fecha_fin):
        year = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%Y')
        fecha_inicial = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime(str(year)+'-01-01')
        fecha_final = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime(str(year)+'-12-31')    
        dominio = [
            ('quantity', '>',0),
            ('create_date', '>=', fecha_inicial),
            ('create_date', '<=', fecha_final),
        ]
        valoracion= request.env['stock.valuation.layer'].search(dominio)
        lista_valores=[]
        for valor in valoracion:
            dict_valores={
                'stock_move_id':valor.stock_move_id,
                'quantity':valor.quantity,
                'value':valor.value,
            }
            lista_valores.append(dict_valores)
        return lista_valores

    def _purchase_order(self,fecha_inicio,fecha_fin):
        year = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%Y')
        fecha_inicial = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime(str(year)+'-01-01')
        fecha_final = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime(str(year)+'-12-31')        
        dominio = [
            ('state', 'in', ('done','purchase')),
            ('date_approve', '>=', fecha_inicial),
            ('date_approve', '<=', fecha_final),
                    ]
        purchase_order= request.env['purchase.order'].search(dominio)

        lista_ordenes=[]
        stock_valuation_layer= self._stock_valuation_layer(fecha_inicio,fecha_fin)
        for orden in purchase_order:
            lista_facturas=[]
            lista_recepciones=[]
            suma_facturas=0

            for factura in orden.invoice_ids:
                if factura.state =='posted':
                    suma_facturas+=factura.amount_untaxed
                    ordenes_compra={
                        'factura_id':factura.id,
                        'factura':factura.name,
                        'orden_id':orden.id,
                        'orden':orden.name,
                        'fecha':orden.date_approve,
                        'monto_orden':orden.amount_untaxed,
                        'monto_factura':factura.amount_untaxed,
                        'moneda':factura.currency_id.id,
                        'tasa_cambio':factura.sat_tasa_cambio,
                    }
                    lista_facturas.append(ordenes_compra)

            for recepcion in orden.picking_ids:
                if recepcion.state =='done' :
                    # print(recepcion.name)
                    lista_valorizacion=[]
                    for linea in recepcion.move_line_ids:
                        valorizacion=list(filter(lambda svl: svl['stock_move_id']==linea.move_id, stock_valuation_layer))
                        for valor in valorizacion:
                            lista_valorizacion.append(valor['value'])
                            # print("    recepcion-->",linea.move_id.id,valor['value'])

                    orden_recepciones={
                        'recepcion_id':recepcion.id,
                        'recepcion':recepcion.name,
                        'orden_id':orden.id,
                        'orden':orden.name,
                        'monto_recepcion':sum(lista_valorizacion),
                    }
                    lista_recepciones.append(orden_recepciones)

            orden_compra={
                'orden_id':orden.id,
                'orden':orden.name,
                'sumatoria':suma_facturas,
                'facturas':lista_facturas,
                'recepciones':lista_recepciones,
            }
            if len(orden_compra['facturas'])!=0:
                lista_ordenes.append(orden_compra)
        
        return lista_ordenes

    def generate_xlsx_report(self, workbook, data, data_report):
        formato_celda_numerica = workbook.add_format({'num_format': '#,##0.00', 'border': 0, })
        formato_encabezado = workbook.add_format({'bold': 1,  'border': 1,    'align': 'center', 'valign':   'vcenter','fg_color': '#1C1C1C', 'font_color': 'white'})
        formato_fecha = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 0})


        self.workbook = workbook
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']   

        facturas=self._facturas(fecha_inicio,fecha_fin)
        ordenes_de_compra=self._purchase_order(fecha_inicio,fecha_fin)

        lista_orden=[]
        lista_recepcion=[]
        for orden in ordenes_de_compra:
            for factura_orden in orden['facturas']:
                lista_orden.append(factura_orden)
            for recepcion_orden in orden['recepciones']:
                lista_recepcion.append(recepcion_orden)

        sheet_inventario = workbook.add_worksheet('Inventario')
        sheet_inventario.write(0, 0, "FACTURA",formato_encabezado)
        sheet_inventario.write(0, 1, "TASA CAMBIO",formato_encabezado)
        sheet_inventario.write(0, 2, "MONTO SIN IVA",formato_encabezado)
        sheet_inventario.write(0, 3, "PROVEEDOR",formato_encabezado)
        sheet_inventario.write(0, 4, "FECHA FACTURA",formato_encabezado)
        sheet_inventario.write(0, 5, "ORDEN DE COMPRA",formato_encabezado)
        sheet_inventario.write(0, 6, "MONTO ORDEN",formato_encabezado)
        sheet_inventario.write(0, 7, "MONTO FACTURA RELACIONADA",formato_encabezado)
        sheet_inventario.write(0, 8, "RECEPCIONES",formato_encabezado)
        sheet_inventario.write(0, 9, "MONTO RECEPCION",formato_encabezado)

        fila=0
        for factura in facturas:
            fila+=1
            sheet_inventario.write(fila, 0, factura.name)
            sheet_inventario.write(fila, 1, factura.sat_tasa_cambio,formato_celda_numerica)
            sheet_inventario.write(fila, 2, factura.amount_untaxed,formato_celda_numerica)
            sheet_inventario.write(fila, 3, factura.partner_id.name)
            sheet_inventario.write(fila, 4, factura.invoice_date,formato_fecha)

            ordenes=list(filter(lambda fac: fac['factura_id']==factura.id, lista_orden))
            for orden in ordenes:
                order_name= orden['orden']
                monto_orden= orden['monto_orden']
                monto_factura= orden['monto_factura']
    
                sheet_inventario.write(fila, 5,order_name)
                sheet_inventario.write(fila, 6,monto_orden,formato_celda_numerica)
                sheet_inventario.write(fila, 7,monto_factura,formato_celda_numerica)

                recepciones=list(filter(lambda o: o['orden_id']==orden['orden_id'], lista_recepcion))
                lista_de_recepciones=[]
                for recepcion in recepciones:
                    lista_de_recepciones.append(recepcion['recepcion'])     
                    sheet_inventario.write(fila, 9,recepcion['monto_recepcion'],formato_celda_numerica)

                caracteres="'[]"
                for caracter in caracteres:
                    lista_de_recepciones=str(lista_de_recepciones).replace(caracter,"")

                sheet_inventario.write(fila, 8,str(lista_de_recepciones))
                








