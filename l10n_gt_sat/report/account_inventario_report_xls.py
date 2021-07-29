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
            ('invoice_date', '<', fecha_inicio),
            ('invoice_date', '<', fecha_inicio),
            ('journal_id.type', '=', 'purchase'),
            ('journal_id.code', 'in', ('FACTU','CEXT')),
        ]
        facturas= request.env['account.move'].search(dominio)
        return facturas

    
    def _purchase_order(self,fecha_inicio,fecha_fin):
        dominio = [
            ('state', '=', 'purchase'),
            ('date_approve', '>=', fecha_inicio),
            ('date_approve', '<=', fecha_fin),
            ('date_approve', '<=', fecha_fin),
                    ]
        purchase_order= request.env['purchase.order'].search(dominio)

        lista_ordenes=[]
        for orden in purchase_order:
            lista_facturas=[]
            suma_facturas=0
            for factura in orden.invoice_ids:
                if factura.state =='posted':
                    suma_facturas+=factura.amount_untaxed
                    ordenes_compra={
                        factura.id:orden.name,
                        'amount':factura.amount_untaxed,
                    }
                    lista_facturas.append(ordenes_compra)

            orden_compra={
                'orden_id':orden.id,
                'orden':orden.name,
                'sumatoria':suma_facturas,
                'facturas':lista_facturas,
            }
            if len(orden_compra['facturas'])!=0:
                lista_ordenes.append(orden_compra)
        # print(lista_ordenes)
        return lista_ordenes

    def generate_xlsx_report(self, workbook, data, data_report):
        self.workbook = workbook
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']

        facturas=self._facturas(fecha_inicio,fecha_fin)
        orden_compra=self._purchase_order(fecha_inicio,fecha_fin)

        lista_orden=[]
        for orden in orden_compra:
            for f in orden['facturas']:
                lista_orden.append(f)

        #contado=list(filter(lambda monto: monto['invoice_user_id'] ==vendedor_id, pagos_contado))

        sheet_inventario = workbook.add_worksheet('Inventario')
        sheet_inventario.write(0, 0, "FACTURA")
        sheet_inventario.write(0, 1, "MONTO SIN IVA")
        sheet_inventario.write(0, 2, "PROVEEDOR")
        sheet_inventario.write(0, 3, "FECHA FACTURA")
        sheet_inventario.write(0, 4, "ORDER DE COMPRA")

        fila=0
        for factura in facturas:
            fila+=1

            # ordern = purchase_order.filtered(lambda v: v.team_id.id ==  team.id)
            # vendedor = vendedor.sorted(lambda v: v.invoice_user_id.name)
            sheet_inventario.write(fila, 0, factura.name)
            sheet_inventario.write(fila, 1, factura.amount_untaxed)
            sheet_inventario.write(fila, 2, factura.partner_id.name)
            sheet_inventario.write(fila, 3, factura.invoice_date)
            # sheet_inventario.write(fila, 4, factura.purchase_vendor_bill_id)

