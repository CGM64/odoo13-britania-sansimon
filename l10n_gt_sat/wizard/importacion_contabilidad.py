# -*- coding: utf-8 -*-

import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

from odoo import api, fields, models, _



class AnalisisImportacionesContabilidad(models.TransientModel):
    _name = "l10n_gt_sat.importacion.contabilidad"
    _description = "Analisis de Importacion y Contabilidad"
    
    previous_month = datetime.today() + relativedelta(months=-1)
    days_previous_month = calendar.monthrange(previous_month.year, previous_month.month)

    fecha_inicio = fields.Date(string='Fecha Inicio', required=True, default=previous_month.strftime('%Y-%m-01'))
    fecha_fin = fields.Date(string='Fecha Fin', required=True, default=previous_month.strftime('%Y-%m-' + str(days_previous_month[1])))

    def export_xls(self):
        print("------------------llego al botons")
        self.ensure_one()
        data = {}
        data['form'] = self.read(['fecha_inicio', 'fecha_fin'])[0]
        return self.env['ir.actions.report'].search([('report_name', '=', 'l10n_gt_sat.analisis_importacion_contabilidad_report_xls'),
                ('report_type', '=', 'xlsx')], limit=1).report_action(self,data=data)
        

class AnalisisImportacionesContabilidadXls(models.AbstractModel):
    _name = 'report.l10n_gt_sat.analisis_importacion_contabilidad_report_xls'
    _description = 'Analisis de Importaciones y Contabilidad XLS'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None

    def generate_xlsx_report(self, workbook, data, data_report):
        print("-----------llego al reporte")
        self.workbook = workbook
        sheet_libro = workbook.add_worksheet('Ventas')
        money = workbook.add_format({'align':'right','valign':'vcenter','num_format': 'Q#,##0.00'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy','align':'left'})
        izquierda = workbook.add_format({'align':'left','valign':'vcenter','text_wrap':1})
        negritaizquierda = workbook.add_format({'bold': True,'align':'left','valign':'vcenter','text_wrap':1})
        porcentaje = workbook.add_format({'num_format': '0.00%','align':'left'})

        i = 0;
        
        sheet_libro.set_column(0,0,5)
        sheet_libro.set_column(1,3,15)
        sheet_libro.set_column(3,3,5)
        sheet_libro.set_column(4,4,20)
        sheet_libro.set_column(5,5,5)
        sheet_libro.set_column(6,6,20)
        sheet_libro.set_column(7,7,20)
        
        sheet_libro.write(i,0,"No", negritaizquierda)
        sheet_libro.write(i,1,"Pedidos", negritaizquierda)
        sheet_libro.write(i,2,"Fecha", negritaizquierda)
        sheet_libro.write(i,3,"# Fact.", negritaizquierda)
        sheet_libro.write(i,4,"T. Fact.", negritaizquierda)
        sheet_libro.write(i,5,"#. Desp.", negritaizquierda)
        sheet_libro.write(i,6,"T. Desp.", negritaizquierda)
        sheet_libro.write(i,7,"Cost. Fac.", negritaizquierda)
        
        inicio = data['form']['fecha_inicio']
        fin = data['form']['fecha_fin']
        