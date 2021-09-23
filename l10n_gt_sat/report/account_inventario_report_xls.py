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


    def _stock_valuation_layer(self, stock_move_id, fecha_inicio, fecha_fin):
        dominio = [
            ('stock_move_id', '=', stock_move_id),
            ('stock_valuation_layer_id', '=', False), 
            ('create_date', '>=', fecha_inicio),
            ('create_date', '<=', fecha_fin)]

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

    def _estructura_reporte(self, fecha_inicio, fecha_fin):
        regexLetras = "[^a-zA-Z0-9_ ,/]"

        fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        ff = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        dominio = [
            ('state', '=', 'done'),
            ('date_done', '>=', fecha_inicio),
            ('date_done', '<=', fecha_fin),
            # ('purchase_id', '!=', None),
            # ('location_id.usage', '!=', 'internal'),
            ('sale_id', '=', None),
        ]
        stock_picking = request.env['stock.picking'].search(dominio)
        stock_picking = stock_picking.sorted(lambda orden: orden.id)

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

                    picking_lines.append(picking_line)
            recepcion['lines'] = picking_lines

            listado_picking.append(recepcion)
        return listado_picking

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

        stock_picking = self._estructura_reporte(fecha_inicio, fecha_fin)

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
        sheet_inventario.write(0, 10, "COSTO EN DESTINO", formato_encabezado)

        sheet_inventario.set_column("A:R", 25)

        fila = 0
        for picking in stock_picking:
            for line in picking['lines']:
                fila += 1

                sheet_inventario.write(
                    fila, 0, picking['date_done'], formato_fecha)
                sheet_inventario.write(fila, 1, picking['name'])
                sheet_inventario.write(fila, 2, picking['origin'])
                sheet_inventario.write(fila, 3, picking['partner_name'])
                sheet_inventario.write(fila, 4, line['default_code'])
                sheet_inventario.write(fila, 5, line['product_name'])
                sheet_inventario.write(fila, 6, line['quantity_done'], formato_celda_numerica)

                sheet_inventario.write(fila, 7, line['value'], formato_celda_numerica)
                sheet_inventario.write(fila, 8, line['gasto'], formato_celda_numerica)
                sheet_inventario.write(fila, 9, line['total'], formato_celda_numerica)
                sheet_inventario.write(fila, 10, line['costo_en_destino'], formato_celda_numerica)

                
