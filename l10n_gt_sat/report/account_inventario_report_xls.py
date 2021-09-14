# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import datetime
from odoo.http import request
import re


class LibroInventarioReportXls(models.AbstractModel):
    _name = 'report.l10n_gt_sat.account_inventario_report_xls'
    _description = 'Reporte Inventario XLS'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None

    def _costos_en_destino(self,picking_id,product_id,quantity):
        dominio = [
            ('picking_ids.id', '=', picking_id),
        ]
        stock_landed_cost = request.env['stock.landed.cost'].search(dominio)
        gasto=sum([line.additional_landed_cost for line in stock_landed_cost.valuation_adjustment_lines.filtered(lambda gs: gs.product_id.id == product_id and gs.quantity == quantity)])

        name=[]
        date=[]
        for line in stock_landed_cost:
            if line.name not in name:
                name.append(line.name)
            if line.date not in date:
                date.append(line.date.strftime('%d/%m/%Y'))
                

        return gasto,str(name),date

    def _ordenes_de_compra(self, fecha_inicio, fecha_fin):
        regexLetras = "[^a-zA-Z0-9_ ,/]"

        dominio = [
            ('state', 'in', ('purchase', 'done',)),
            ('picking_ids.scheduled_date', '>=', fecha_inicio),
            ('picking_ids.scheduled_date', '<=', fecha_fin),
            # ('name', 'in', ('P00015','P00016','P00017')),
            # ('name', 'in', ('P00015','P00016')),
            # ('name', '=', 'P00162'),
        ]
        purchase_orders = request.env['purchase.order'].search(dominio)

        purchase_orders = purchase_orders.sorted(lambda orden: orden.id)

        listado_compras = []
        for order in purchase_orders:
            lista_pickings=[]
            orden_compra = {
                'id': order.id,
                'name': order.name,
                'partner_id': order.partner_id.name,
                'date_order': order.date_approve, 
            }

            if order.partner_ref != False:
                orden_compra['partner_ref']=order.partner_ref
            else:
                orden_compra['partner_ref']=None

            order_lines=[]
            for line in order.order_line:
                order_line = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,

                    #landed_cost_ids ->Costos en Destino
                    'gasto':None,
                    'landed_cost_name':None,
                    'landed_cost_date':None,
                    'total':None,
                    #picking_ids ->Recepciones
                    'picking_name':None,
                    'scheduled_date':None,
                    #invoice_ids ->Facturas
                    'invoice_id':None,
                    'invoice_name':None,
                    'journal_id':None,
                    'currency_name':None,
                }      

                if line.product_id.default_code !=False:
                    order_line['default_code']=line.product_id.default_code
                else:
                    order_line['default_code']=None

                invoices=[]
                for invoice in order.invoice_ids:
                    if invoice.state =='posted':
                        order_invoices={
                            'invoice_id':invoice.id,
                            'name':invoice.name,
                            'journal_id':invoice.journal_id.name,
                            'currency_name':invoice.currency_id.name
                        }
                        order_line['invoice_id']=invoice.id
                        order_line['invoice_name']=invoice.name
                        order_line['journal_id']=invoice.journal_id.name
                        order_line['currency_name']=invoice.currency_id.name
                        invoices.append(order_invoices)
                orden_compra['invoices']=invoices

                pickings=[]
                for picking in order.picking_ids:
                    if picking.state =='done':
                        gasto,name,date=self._costos_en_destino(picking.id,line.product_id.id,line.product_qty)

                        name=re.sub(regexLetras, "", str(name))
                        date=re.sub(regexLetras, "", str(date))
                        
                        if picking.name not in lista_pickings:
                            lista_pickings.append(picking.name)
                        order_pickings={
                            'picking_id':picking.id,
                            'name':picking.name,
                            'scheduled_date':picking.scheduled_date,
                            'date_done':picking.date_done,
                        }

                        lista_modificada= re.sub(regexLetras, "", str(lista_pickings))
                        order_line['picking_name']=lista_modificada
                        order_line['scheduled_date']=picking.scheduled_date

                        if gasto !=0:
                            order_line['gasto']=gasto
                        else:
                            order_line['gasto']=None

                        if name !=False:
                            order_line['landed_cost_name']=name
                            order_line['total']=gasto+line.price_subtotal
                            order_line['landed_cost_date']=date

                        pickings.append(order_pickings)
                orden_compra['pickings']=pickings

                order_lines.append(order_line)                    
            orden_compra['lines']=order_lines

            listado_compras.append(orden_compra)

        return listado_compras

    def generate_xlsx_report(self, workbook, data, data_report):
        formato_celda_numerica = workbook.add_format(
            {'num_format': '#,##0.00', 'border': 0, })
        formato_encabezado = workbook.add_format(
            {'bold': 1,  'border': 1,    'align': 'center', 'valign':   'vcenter', 'fg_color': '#1C1C1C', 'font_color': 'white'})
        formato_fecha = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 0})

        self.workbook = workbook
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']

        purchase_orders=self._ordenes_de_compra(fecha_inicio, fecha_fin)

        sheet_inventario = workbook.add_worksheet('Inventario')
        sheet_inventario.write(0, 0, "ORDEN DE COMPRA", formato_encabezado)
        sheet_inventario.write(0, 1, "PROVEEDOR", formato_encabezado)
        sheet_inventario.write(0, 2, "FECHA", formato_encabezado)
        sheet_inventario.write(0, 3, "REFERENCIA", formato_encabezado)

        sheet_inventario.write(0, 4, "CODIGO", formato_encabezado)
        sheet_inventario.write(0, 5, "PRODUCTO", formato_encabezado)
        sheet_inventario.write(0, 6, "CANTIDAD", formato_encabezado)
        sheet_inventario.write(0, 7, "PRECIO", formato_encabezado)
        sheet_inventario.write(0, 8, "SUB-TOTAL", formato_encabezado)

        sheet_inventario.write(0, 9, "RECEPCION", formato_encabezado)
        sheet_inventario.write(0, 10, "FECHA RECEPCION", formato_encabezado)

        sheet_inventario.write(0, 11, "COSTO EN DESTINO", formato_encabezado)
        sheet_inventario.write(0, 12, "FECHA COSTO EN DESTINO", formato_encabezado)
        sheet_inventario.write(0, 13, "GASTO", formato_encabezado)
        sheet_inventario.write(0, 14, "TOTAL", formato_encabezado)

        sheet_inventario.write(0, 15, "FACTURA", formato_encabezado)
        sheet_inventario.write(0, 16, "DIARIO", formato_encabezado)

        sheet_inventario.set_column("A:R", 25)

        fila=0
        for order in purchase_orders:
            for line in order['lines']:
                fila+=1
                sheet_inventario.write(fila, 0,order['name'],)
                sheet_inventario.write(fila, 1,order['partner_id'])
                sheet_inventario.write(fila, 2,order['date_order'],formato_fecha)
                sheet_inventario.write(fila, 3,order['partner_ref'])

                sheet_inventario.write(fila, 4,line['default_code'])
                sheet_inventario.write(fila, 5,line['name'])
                sheet_inventario.write(fila, 6,line['product_qty'],formato_celda_numerica)
                sheet_inventario.write(fila, 7,line['price_unit'],formato_celda_numerica)
                sheet_inventario.write(fila, 8,line['price_subtotal'],formato_celda_numerica)

                sheet_inventario.write(fila, 9, line['picking_name'])
                sheet_inventario.write(fila, 10,line['scheduled_date'],formato_fecha)
                sheet_inventario.write(fila, 11,line['landed_cost_name'])
                sheet_inventario.write(fila, 12,line['landed_cost_date'],formato_fecha)
                sheet_inventario.write(fila, 13,line['gasto'],formato_celda_numerica)                
                sheet_inventario.write(fila, 14,line['total'],formato_celda_numerica)

                sheet_inventario.write(fila, 15,line['invoice_name'])
                sheet_inventario.write(fila, 16,line['journal_id'],formato_celda_numerica)
                
                
                


                    

                
                



                



        
