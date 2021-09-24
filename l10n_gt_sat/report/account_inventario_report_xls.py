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
    
    def _sum_stock_valuation_layer(self, stock_move_ids, fecha_inicio, fecha_fin):

        if fecha_inicio !=None and fecha_fin !=None:
            dominio = [
                ('stock_move_id', 'in', stock_move_ids),
                ('create_date', '>=', fecha_inicio),
                ('create_date', '<=', fecha_fin)]
        else:
            dominio = [
                ('stock_move_id', 'in', stock_move_ids)]

        stock_valuation_layer = request.env['stock.valuation.layer'].search(dominio)
        total = sum([line.value for line in stock_valuation_layer])
        return total
        


    def _stock_valuation_layer(self, stock_move_id, fecha_inicio, fecha_fin):
        if fecha_inicio !=None and fecha_fin !=None:
            dominio = [
                ('stock_move_id', '=', stock_move_id),
                ('stock_valuation_layer_id', '=', False), 
                ('create_date', '>=', fecha_inicio),
                ('create_date', '<=', fecha_fin)]
        else:
            dominio = [
                ('stock_move_id', '=', stock_move_id),
                ('stock_valuation_layer_id', '=', False)]

        stock_valuation_layer = request.env['stock.valuation.layer'].search(dominio)

        if len(stock_valuation_layer) > 0:
            value = stock_valuation_layer.value
            dominio.pop(dominio.index( ('stock_valuation_layer_id', '=', False), ))
            dominio.append(('stock_valuation_layer_id', '!=', False))
            stock_valuation_layer = request.env['stock.valuation.layer'].search(dominio)
            gasto = sum([line.value for line in stock_valuation_layer.filtered(lambda gs: gs.stock_move_id.id == stock_move_id)])
            total = value + gasto
            costo_en_destino=[]
            for item in stock_valuation_layer:
                if item.description not in costo_en_destino:
                    costo_en_destino.append(item.description)
        else:
            value = 0
            gasto = 0
            total = 0
            costo_en_destino=None
        return value,gasto,total,str(costo_en_destino)

    def _estructura_reporte(self,generar_por,picking_ids,fecha_inicio, fecha_fin):
        regexLetras = "[^a-zA-Z0-9_ ,/]"

        # fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        # ff = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        if generar_por =='picking':
            dominio = [
                ('id', 'in', picking_ids),
            ]
        else:
            dominio = [
                ('state', '=', 'done'),
                ('date_done', '>=', fecha_inicio),
                ('date_done', '<=', fecha_fin),
                ('sale_id', '=', None),
            ]

        stock_picking = request.env['stock.picking'].search(dominio)
        stock_picking = stock_picking.sorted(lambda orden: orden.id)
        porcentaje=0
        
        picking_a_sumar=[]
        for pick in stock_picking.move_ids_without_package:
            if pick.id not in picking_a_sumar:
                picking_a_sumar.append(pick.id)
        total_general=self._sum_stock_valuation_layer(picking_a_sumar, fecha_inicio, fecha_fin)

        listado_picking = []
        for picking in stock_picking:
            lista_ids = []
            recepcion = {
                'date_done': picking.date_done,
                'name': picking.name,
                'partner_name': picking.partner_id.name,
                'state': picking.state,
                'origin': picking.origin,
            }
            picking_lines = []

            for line in picking.move_ids_without_package:
                value,gasto,total,costo_en_destino= self._stock_valuation_layer(line.id, fecha_inicio, fecha_fin)
                # print("line", line.id, ' product ', line.product_id.id,line.product_id.name, ' valor> ', value,' gasto> ',gasto)
                if line.id not in lista_ids:
                    lista_ids.append(line.id)
                    picking_line = {
                        'default_code': line.product_id.default_code,
                        'product_name': line.product_id.name,
                        'quantity_done': line.quantity_done,
                    }
                    costo_en_destino=re.sub(regexLetras, "", str(costo_en_destino))

                    picking_line['value'] = value
                    picking_line['gasto'] = gasto
                    picking_line['total'] = total
                    picking_line['costo_en_destino'] = costo_en_destino.replace('None','')
                    
                    
                    if float(total_general) !=0:
                        picking_line['porcentaje']= total/float(total_general)
                        picking_line['total_general'] = total_general
                        porcentaje+=total/float(total_general)
                    else:
                        picking_line['porcentaje']= 0
                        picking_line['total_general'] = 0
                        porcentaje+=total/float(total_general)


                    picking_lines.append(picking_line)
            recepcion['lines'] = picking_lines
            recepcion['porcentaje_total'] = porcentaje

            listado_picking.append(recepcion)
        return listado_picking

    def generate_xlsx_report(self, workbook, data, data_report):
        formato_celda_numerica = workbook.add_format(
            {'num_format': '#,##0.00', 'border': 0, })
        formato_encabezado = workbook.add_format(
            {'bold': 1,  'border': 1,    'align': 'center', 'valign':   'vcenter', 'fg_color': '#1C1C1C', 'font_color': 'white'})
        formato_fecha = workbook.add_format(
            {'num_format': 'dd/mm/yyyy', 'border': 0})
        formato_porcentaje = workbook.add_format({'num_format': '0.00%'})

        self.workbook = workbook
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']

        picking_ids = data['form']['picking_ids']
        generar_por = data['form']['generar_por']
        
        if generar_por=='fecha':
            stock_picking = self._estructura_reporte(generar_por,None,fecha_inicio, fecha_fin)
        else:
            stock_picking = self._estructura_reporte(generar_por,picking_ids,None,None)

        sheet_inventario = workbook.add_worksheet('Inventario')
        sheet_inventario.write(0, 0, "FECHA", formato_encabezado)
        sheet_inventario.write(0, 1, "RECEPCION", formato_encabezado)
        sheet_inventario.write(0, 2, "ORIGEN", formato_encabezado)
        sheet_inventario.write(0, 3, "PROVEEDOR", formato_encabezado)
        sheet_inventario.write(0, 4, "CODIGO", formato_encabezado)
        sheet_inventario.write(0, 5, "PRODUCTO", formato_encabezado)
        sheet_inventario.write(0, 6, "CANT RECIBIDA", formato_encabezado)

        sheet_inventario.write(0, 7, "VALUE", formato_encabezado)
        sheet_inventario.write(0, 8, "GASTO", formato_encabezado)
        sheet_inventario.write(0, 9, "TOTAL", formato_encabezado)
        sheet_inventario.write(0, 10, "PORCENTAJE", formato_encabezado)
        sheet_inventario.write(0, 11, "COSTO EN DESTINO", formato_encabezado)

        sheet_inventario.set_column("A:R", 25)


        # stock_picking_nuevo=list(filter(lambda f: f['value'] !=0))

        fila = 0
        for picking in stock_picking:
            for line in picking['lines']:
                if line['total'] !=0:
                    fila += 1
                    sheet_inventario.write(fila, 0, picking['date_done'], formato_fecha)
                    sheet_inventario.write(fila, 1, picking['name'])
                    sheet_inventario.write(fila, 2, picking['origin'])
                    sheet_inventario.write(fila, 3, picking['partner_name'])
                    sheet_inventario.write(fila, 4, line['default_code'])
                    sheet_inventario.write(fila, 5, line['product_name'])
                    sheet_inventario.write(fila, 6, line['quantity_done'], formato_celda_numerica)

                    sheet_inventario.write(fila, 7, line['value'], formato_celda_numerica)
                    sheet_inventario.write(fila, 8, line['gasto'], formato_celda_numerica)
                    sheet_inventario.write(fila, 9, line['total'], formato_celda_numerica)
                    sheet_inventario.write(fila, 10, line['porcentaje'], formato_porcentaje)
                    sheet_inventario.write(fila, 11, line['costo_en_destino'])
                    sheet_inventario.write(fila+1, 9, line['total_general'], formato_celda_numerica)
                    sheet_inventario.write(fila+1, 10, picking['porcentaje_total'], formato_porcentaje)




                    

                
