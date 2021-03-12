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
        sheet_libro.write(0,0,'Hola Mundo')


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
