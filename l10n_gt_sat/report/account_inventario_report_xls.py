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

    lista_aux=[]

    def _costos_en_destino(self,picking_id,product_id,move_id):
        dominio = [('picking_ids.id', '=', picking_id),]
        stock_landed_cost = request.env['stock.landed.cost'].search(dominio)
        gasto=sum([line.additional_landed_cost for line in stock_landed_cost.valuation_adjustment_lines.filtered(lambda gs: gs.product_id.id == product_id and gs.move_id.id==move_id)])
        former_cost=[line.former_cost for line in stock_landed_cost.valuation_adjustment_lines.filtered(lambda gs: gs.product_id.id == product_id and gs.move_id.id==move_id)]

        if len(former_cost)>0:
            subtotal=former_cost[0] 
        else:
            subtotal=0


        name=[]
        date=[]
        account_move_id=[]
        for slc in stock_landed_cost:
            if slc.name not in name:
                name.append(slc.name)
            if slc.account_move_id not in account_move_id:
                account_move_id.append(slc.account_move_id.name)
            if slc.date not in date:
                date.append(slc.date.strftime('%d/%m/%Y'))
                
        return subtotal,gasto,str(name),date,str(account_move_id)

    def _move_id(self,picking_id,product_id):
        dominio = [('picking_ids.id', '=', picking_id),]
        stock_landed_cost = request.env['stock.landed.cost'].search(dominio)

        move_ids=[]
        for slc in stock_landed_cost:
            for line in slc.valuation_adjustment_lines.filtered(lambda gs: gs.product_id.id == product_id):
                move_ids.append(line.move_id.id)    

        return move_ids

    def _ordenes_de_compra(self, fecha_inicio, fecha_fin):
        regexLetras = "[^a-zA-Z0-9_ ,/]"

        fi=datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        ff=datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        dominio = [
            ('state', 'in', ('purchase', 'done',)),
            ('picking_ids.date_done', '>=', fecha_inicio),
            ('picking_ids.date_done', '<=', fecha_fin),
            # ('date_order', '>=', fecha_inicio),
            # ('date_order', '<=', fecha_fin),
            # ('name', 'in', ('P00015','P00016','P00017')),
            # ('name', 'in', ('P00015','P00016')),
            # ('name', '=', 'P00162'),
        ]
        purchase_orders = request.env['purchase.order'].search(dominio)
        purchase_orders = purchase_orders.sorted(lambda orden: orden.id)

        listado_compras = []
        for order in purchase_orders:
            lista_pickings=[]
            lista_invoices=[]
            
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
            lista_ids=[]
            for line in order.order_line:
                order_line = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,

                    #landed_cost_ids ->Costos en Destino
                    'gasto':None,
                    'subtotal':None,
                    'landed_cost_name':None,
                    'landed_cost_date':None,
                    'landed_account_move_id':None,
                    'total':None,
                    #picking_ids ->Recepciones
                    'picking_name':None,
                    'scheduled_date':None,
                    'date_done':None,
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

                for invoice in order.invoice_ids.filtered(lambda inv: inv.state=='posted'):
                    if invoice.name not in lista_invoices:
                        lista_invoices.append(invoice.name)

                    lista_facturas_modificada= re.sub(regexLetras, "", str(lista_invoices))
                    order_line['invoice_id']=invoice.id
                    order_line['invoice_name']=lista_facturas_modificada
                    order_line['journal_id']=invoice.journal_id.name
                    order_line['currency_name']=invoice.currency_id.name

                for picking in order.picking_ids.filtered(lambda pkg: pkg.state=='done' and pkg.date_done.date() >= fi and pkg.date_done.date() <= ff):
                    print("picking",picking.name)
                    move_ids=self._move_id(picking.id,line.product_id.id)                 
                    
                    for id in move_ids:
                        if id not in lista_ids:
                            if id:
                                subtotal,gasto,name,date,account_move_id=self._costos_en_destino(picking.id,line.product_id.id,id)
                                lista_ids.append(id)
                                print(' ID >',id)
                                print(' lista_ids >',lista_ids)
                            else:
                                subtotal,gasto,name,date,account_move_id=self._costos_en_destino(picking.id,line.product_id.id,None)

                            name=re.sub(regexLetras, "", str(name))
                            date=re.sub(regexLetras, "", str(date))
                            account_move_id=re.sub(regexLetras, "", str(account_move_id))
                            
                            if picking.name not in lista_pickings:
                                lista_pickings.append(picking.name)

                            lista_modificada= re.sub(regexLetras, "", str(lista_pickings))
                            order_line['picking_name']=lista_modificada
                            order_line['scheduled_date']=picking.scheduled_date
                            order_line['date_done']=picking.date_done

                            if gasto !=0:
                                order_line['gasto']=gasto
                                order_line['subtotal']=subtotal
                                order_line['total']=gasto+subtotal
                            else:
                                order_line['gasto']=None
                                order_line['subtotal']=None
                                order_line['total']=None

                            if name !=False:
                                order_line['landed_cost_name']=name
                                order_line['landed_cost_date']=date
                                order_line['landed_account_move_id']=account_move_id

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
        sheet_inventario.write(0, 7, "RECEPCION", formato_encabezado)
        sheet_inventario.write(0, 8, "FECHA RECEPCION", formato_encabezado)

        sheet_inventario.write(0, 9, "COSTO EN DESTINO", formato_encabezado)
        sheet_inventario.write(0, 10, "FECHA COSTO EN DESTINO", formato_encabezado)
        sheet_inventario.write(0, 11, "SUBTOTAL", formato_encabezado)
        sheet_inventario.write(0, 12, "GASTO", formato_encabezado)
        sheet_inventario.write(0, 13, "TOTAL", formato_encabezado)

        sheet_inventario.write(0, 14, "FACTURA", formato_encabezado)
        sheet_inventario.write(0, 15, "DIARIO", formato_encabezado)

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

                sheet_inventario.write(fila, 7, line['picking_name'])
                sheet_inventario.write(fila, 8,line['date_done'],formato_fecha)
                sheet_inventario.write(fila, 9,line['landed_cost_name'])
                sheet_inventario.write(fila, 10,line['landed_cost_date'],formato_fecha)
                sheet_inventario.write(fila, 11,line['subtotal'],formato_celda_numerica)                
                sheet_inventario.write(fila, 12,line['gasto'],formato_celda_numerica)                
                sheet_inventario.write(fila, 13,line['total'],formato_celda_numerica)

                sheet_inventario.write(fila, 14,line['invoice_name'])
                sheet_inventario.write(fila, 15,line['journal_id'],formato_celda_numerica)
                sheet_inventario.write(fila, 16,line['landed_account_move_id'])
                

                
                
                


                    

                
                



                



        
