# -*- coding: utf-8 -*-
from odoo import models,api
from datetime import datetime



class StockMovePeriodoXls(models.AbstractModel):
    _name = 'report.sansimon.stock_move_periodo_report_xls'
    _description = 'Reporte de Inventario por Periodo XLS'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None

    def generate_xlsx_report(self, workbook, data, data_report):
        self.workbook = workbook
        sheet_libro = workbook.add_worksheet('Inventario')
        productos = self.env['product.product'].search([('active','=',True),('qty_available','>',0)])
        i = 0;
        sheet_libro.write(i,0,"Linea")
        sheet_libro.write(i,1,"Codigo")
        sheet_libro.write(i,2,"Descripcion")
        sheet_libro.write(i,3,"Cantidad")
        sheet_libro.write(i,4,"qty_available")
        sheet_libro.write(i,5,"incoming_qty")
        sheet_libro.write(i,6,"outgoing_qty")
        sheet_libro.set_column(0,0,5)
        sheet_libro.set_column(1,1,16)
        sheet_libro.set_column(2,2,60)
        sheet_libro.set_column(3,6,12)
        productos = productos.filtered(lambda p: p.type != 'service')
        print(data)
        res = productos._compute_quantities_dict(None, None, None, data['form']['fecha_inicio'], data['form']['fecha_fin'])
        for producto in productos:
            i+=1
            sheet_libro.write(i,0,i)
            sheet_libro.write(i,1,producto.default_code)
            sheet_libro.write(i,2,producto.name)
            sheet_libro.write(i,3,producto.qty_available)

            sheet_libro.write(i,4,res[producto.id]['qty_available'])
            sheet_libro.write(i,5,res[producto.id]['incoming_qty'])
            sheet_libro.write(i,6,res[producto.id]['outgoing_qty'])





        # Requests = self.env['hr.leave']
        # Allocations = self.env['hr.leave.allocation']
        # today_date = datetime.datetime.utcnow().date()
        # today_start = fields.Datetime.to_string(today_date)  # get the midnight of the current utc day
        # today_end = fields.Datetime.to_string(today_date + relativedelta(hours=23, minutes=59, seconds=59))
    #
    # action['domain'] = [
    #         ('holiday_status_id', '=', self.ids[0]),
    #         ('date_from', '>=', fields.Datetime.to_string(datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)))
    #     ]
