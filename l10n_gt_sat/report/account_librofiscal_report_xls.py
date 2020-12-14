# -*- coding: utf-8 -*-
from odoo import models,api
from datetime import datetime

class LibroFiscalReportXls(models.AbstractModel):
    _name = 'report.l10n_gt_sat.account_librofiscal_report_xls'
    _description = 'Reporte Fiscal XLS'
    _inherit = 'report.report_xlsx.abstract'

    workbook = None

    def _get_libro_ventas(self, libro, sheet_libro, fila, columna, format1, date_format, vendedor):
        sheet_libro.set_column(columna,columna,4)
        sheet_libro.set_column(columna + 1,columna + 1,8)
        sheet_libro.set_column(columna + 2,columna + 2,12)
        sheet_libro.set_column(columna + 3,columna + 3,12)
        sheet_libro.set_column(columna + 4,columna + 4,19)
        sheet_libro.set_column(columna + 5,columna + 5,15)
        sheet_libro.set_column(columna + 6,columna + 6,55)
        sheet_libro.set_column(columna + 7,columna + 7,12)
        sheet_libro.set_column(columna + 8,columna + 8,12)
        sheet_libro.set_column(columna + 9,columna + 9,12)
        sheet_libro.set_column(columna + 10,columna + 10,12)
        sheet_libro.set_column(columna + 11,columna + 12,12)
        sheet_libro.set_column(columna + 12,columna + 12,12)
        sheet_libro.set_column(columna + 13,columna + 13,12)
        sheet_libro.set_column(columna + 14,columna + 14,12)
        if vendedor:
            sheet_libro.set_column(columna + 15,columna + 15,30)


        sheet_libro.write(fila, columna, "No.", format1)
        sheet_libro.write(fila, columna + 1, "Cod.", format1)
        sheet_libro.write(fila, columna + 2, "Fecha", format1)
        sheet_libro.write(fila, columna + 3, "Serie", format1)
        sheet_libro.write(fila, columna + 4, "No. Factura", format1)
        sheet_libro.write(fila, columna + 5, "Nit", format1)
        sheet_libro.write(fila, columna + 6, "Nombre", format1)
        sheet_libro.write(fila, columna + 7, "Exenta", format1)
        sheet_libro.write(fila, columna + 8, "Exp. Fuera CA.", format1)
        sheet_libro.write(fila, columna + 9, "Exp. Centro A.", format1)
        sheet_libro.write(fila, columna + 10, "Servicios", format1)
        sheet_libro.write(fila, columna + 11, "Ventas", format1)
        sheet_libro.write(fila, columna + 12, "Subtotal", format1)
        sheet_libro.write(fila, columna + 13, "Iva", format1)
        sheet_libro.write(fila, columna + 14, "Total", format1)
        if vendedor:
            sheet_libro.write(fila, columna + 15, "Vendedor", format1)

        fila += 1

        for f in libro['facturas']:
            sheet_libro.write(fila, columna, f.no_linea)
            sheet_libro.write(fila, columna + 1, f.journal_id.code)
            sheet_libro.write(fila, columna + 2, f.invoice_date, date_format)
            sheet_libro.write(fila, columna + 3, f.sat_fac_serie)
            sheet_libro.write(fila, columna + 4, f.sat_fac_numero)
            sheet_libro.write(fila, columna + 5, f.partner_id.vat if f.state not in ('cancel') else '')
            sheet_libro.write(fila, columna + 6, f.partner_id.name if f.state not in ('cancel') else 'Anulado')
            sheet_libro.write(fila, columna + 7, 0, self.fnumerico)
            sheet_libro.write(fila, columna + 8, 0, self.fnumerico)
            sheet_libro.write(fila, columna + 9, f.sat_exportacion_in_ca, self.fnumerico)
            sheet_libro.write(fila, columna + 10, f.sat_servicio, self.fnumerico)
            sheet_libro.write(fila, columna + 11, f.sat_bien, self.fnumerico)
            sheet_libro.write(fila, columna + 12, f.sat_subtotal, self.fnumerico)
            sheet_libro.write(fila, columna + 13, f.sat_iva, self.fnumerico)
            sheet_libro.write(fila, columna + 14, f.sat_amount_total, self.fnumerico)
            if vendedor:
                sheet_libro.write(fila, columna + 15, f.invoice_user_id.name)
            fila += 1

        r = libro['resumen']

        sheet_libro.write(fila, columna + 9, r['sat_exportacion_in_ca'], self.money)
        sheet_libro.write(fila, columna + 10, r['servicio'], self.money)
        sheet_libro.write(fila, columna + 11, r['bien'], self.money)
        sheet_libro.write(fila, columna + 12, r['sat_subtotal_total'], self.money)
        sheet_libro.write(fila, columna + 13, r['sat_iva_total'], self.money)
        sheet_libro.write(fila, columna + 14, r['amount_total_total'], self.money)
        fila += 1

        return sheet_libro

    def _get_libro_compras(self, libro, sheet_libro, fila, columna, format1, date_format):
        sheet_libro.set_column(columna,columna,4)
        sheet_libro.set_column(columna + 1,columna + 1,8)
        sheet_libro.set_column(columna + 2,columna + 2,12)
        sheet_libro.set_column(columna + 3,columna + 3,12)
        sheet_libro.set_column(columna + 4,columna + 4,12)
        sheet_libro.set_column(columna + 5,columna + 5,12)
        sheet_libro.set_column(columna + 6,columna + 6,55)
        sheet_libro.set_column(columna + 7,columna + 7,10)
        sheet_libro.set_column(columna + 8,columna + 8,10)
        sheet_libro.set_column(columna + 9,columna + 9,10)
        sheet_libro.set_column(columna + 10,columna + 10,10)
        sheet_libro.set_column(columna + 11,columna + 11,12)
        sheet_libro.set_column(columna + 12,columna + 12,12)
        sheet_libro.set_column(columna + 13,columna + 13,12)
        sheet_libro.set_column(columna + 14,columna + 14,12)
        sheet_libro.set_column(columna + 15,columna + 15,12)
        sheet_libro.set_column(columna + 16,columna + 16,12)
        sheet_libro.set_column(columna + 17,columna + 17,12)



        sheet_libro.write(fila, columna, "No.", format1)
        sheet_libro.write(fila, columna + 1, "Cod.", format1)
        sheet_libro.write(fila, columna + 2, "Fecha", format1)
        sheet_libro.write(fila, columna + 3, "Serie", format1)
        sheet_libro.write(fila, columna + 4, "No. Factura", format1)
        sheet_libro.write(fila, columna + 5, "Nit", format1)
        sheet_libro.write(fila, columna + 6, "Nombre", format1)
        sheet_libro.write(fila, columna + 7, "Exenta", format1)
        sheet_libro.write(fila, columna + 8, "Importacion fuera CA", format1)
        sheet_libro.write(fila, columna + 9, "Importacion CA", format1)
        sheet_libro.write(fila, columna + 10, "Servicios", format1)
        sheet_libro.write(fila, columna + 11, "Compra de activos fijos", format1)
        sheet_libro.write(fila, columna + 12, "Pequeño Contrib.", format1)
        sheet_libro.write(fila, columna + 13, "Bienes", format1)
        sheet_libro.write(fila, columna + 14, "Combust.", format1)
        sheet_libro.write(fila, columna + 15, "Base para Compras", format1)
        sheet_libro.write(fila, columna + 16, "IVA", format1)
        sheet_libro.write(fila, columna + 17, "Total", format1)

        fila += 1

        for f in libro['facturas']:
            sheet_libro.write(fila, columna, f.no_linea)
            sheet_libro.write(fila, columna + 1, f.journal_id.code)
            sheet_libro.write(fila, columna + 2, f.invoice_date, date_format)
            sheet_libro.write(fila, columna + 3, f.sat_fac_serie)
            sheet_libro.write(fila, columna + 4, f.sat_fac_numero)
            sheet_libro.write(fila, columna + 5, f.partner_id.vat)
            sheet_libro.write(fila, columna + 6, f.partner_id.name)
            sheet_libro.write(fila, columna + 7, f.sat_exento, self.fnumerico)
            sheet_libro.write(fila, columna + 8, f.sat_importa_out_ca, self.fnumerico)
            sheet_libro.write(fila, columna + 9, f.sat_importa_in_ca, self.fnumerico)
            sheet_libro.write(fila, columna + 10, f.sat_servicio, self.fnumerico)
            sheet_libro.write(fila, columna + 11, 0, self.fnumerico)
            sheet_libro.write(fila, columna + 12, f.sat_peq_contri, self.fnumerico)
            sheet_libro.write(fila, columna + 13, f.sat_bien, self.fnumerico)
            sheet_libro.write(fila, columna + 14, f.sat_combustible, self.fnumerico)
            sheet_libro.write(fila, columna + 15, f.sat_base, self.fnumerico)
            sheet_libro.write(fila, columna + 16, f.sat_iva, self.fnumerico)
            sheet_libro.write(fila, columna + 17, f.sat_amount_total, self.fnumerico)
            fila += 1

        r = libro['resumen']
        sheet_libro.write(fila, columna + 7, r['sat_exento'], self.money)
        sheet_libro.write(fila, columna + 8, r['sat_importa_out_ca'], self.money)
        sheet_libro.write(fila, columna + 9, r['sat_importa_in_ca'], self.money)
        sheet_libro.write(fila, columna + 10, r['servicio'], self.money)
        sheet_libro.write(fila, columna + 12, r['sat_peq_contri'], self.money)
        sheet_libro.write(fila, columna + 13, r['bien'], self.money)
        sheet_libro.write(fila, columna + 14, r['sat_combustible'], self.money)
        sheet_libro.write(fila, columna + 15, r['sat_base'], self.money)
        sheet_libro.write(fila, columna + 16, r['sat_iva_total'], self.money)
        sheet_libro.write(fila, columna + 17, r['amount_total_total'], self.money)
        fila += 1

        sheet_libro = self.workbook.add_worksheet("Resumen " + libro['descripcion'])

        fila = 0
        sheet_libro.set_column(columna,columna,15)
        sheet_libro.set_column(columna + 1,columna + 1,12)
        sheet_libro.set_column(columna + 2,columna + 2,12)
        sheet_libro.set_column(columna + 3,columna + 3,12)

        sheet_libro.write(fila, columna, "Concepto", self.bold)
        sheet_libro.write(fila, columna + 1, "Base Imponible", self.bold)
        sheet_libro.write(fila, columna + 2, "IVA", self.bold)
        sheet_libro.write(fila, columna + 3, "Total", self.bold)

        fila += 1
        sheet_libro.write(fila, columna, "Servicio")
        sheet_libro.write(fila, columna + 1, r['servicio'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, r['servicio_iva'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['servicio_total'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Bienes")
        sheet_libro.write(fila, columna + 1, r['bien'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, r['bien_iva'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['bien_total'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Pequeño Contribuyente")
        sheet_libro.write(fila, columna + 1, r['sat_peq_contri'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, 0, self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['sat_peq_contri'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Combustible")
        sheet_libro.write(fila, columna + 1, r['sat_combustible'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, r['sat_combustible_iva'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['sat_combustible_total'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Importacion CA")
        sheet_libro.write(fila, columna + 1, r['sat_importa_in_ca'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, r['sat_importa_in_ca_iva'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['sat_importa_in_ca_total'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Importacion Fuera CA")
        sheet_libro.write(fila, columna + 1, r['sat_importa_out_ca'], self.fnumerico)
        sheet_libro.write(fila, columna + 2, r['sat_importa_out_ca_iva'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, r['sat_importa_out_ca_total'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "Total")
        sheet_libro.write_formula(fila, columna + 1, '=SUM(B2:B7)', self.fnumerico)
        sheet_libro.write(fila, columna + 2, '=SUM(C2:C7)', self.fnumerico)
        sheet_libro.write(fila, columna + 3, '=SUM(D2:D7)', self.fnumerico)

        sheet_libro = self.workbook.add_worksheet("Top 10 " + libro['descripcion'])

        fila = 0
        sheet_libro.set_column(columna,columna,12)
        sheet_libro.set_column(columna + 1,columna + 1,55)
        sheet_libro.set_column(columna + 2,columna + 2,12)
        sheet_libro.set_column(columna + 3,columna + 3,12)


        sheet_libro.write(fila, columna, "Nit", self.bold)
        sheet_libro.write(fila, columna + 1, "Cliente", self.bold)
        sheet_libro.write(fila, columna + 2, "Cantidad", self.bold)
        sheet_libro.write(fila, columna + 3, "Monto Base", self.bold)
        fila = 1
        for t in libro['top10_documentos']:
            sheet_libro.write(fila, columna, t['partner'].vat)
            sheet_libro.write(fila, columna + 1, t['partner'].name)
            sheet_libro.write(fila, columna + 2, t['cant_docs'], self.fnumerico)
            sheet_libro.write(fila, columna + 3, t['sat_base'], self.fnumerico)
            fila += 1

        sheet_libro.write(fila, columna, '')
        sheet_libro.write(fila, columna + 1, 'Diferencia')
        sheet_libro.write(fila, columna + 2, libro['top10_documentos_diferencia']['cant_docs'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, libro['top10_documentos_diferencia']['sat_base'], self.fnumerico)

        fila += 1
        sheet_libro.write(fila, columna, "")
        sheet_libro.write(fila, columna + 1, "Total", self.fnumerico)
        sheet_libro.write(fila, columna + 2, libro['top10_documentos_total']['cant_docs'], self.fnumerico)
        sheet_libro.write(fila, columna + 3, libro['top10_documentos_total']['sat_base'], self.fnumerico)


        return sheet_libro

    def generate_xlsx_report(self, workbook, data, data_report):
        self.workbook = workbook
        format1 = workbook.add_format({'font_size': 12, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format1.set_align('center')
        self.bold = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        self.fnumerico = workbook.add_format({'num_format': '#,##0.00'})
        self.money = workbook.add_format({'font_size': 12, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True, 'num_format': '#,##0.00'})


        libros_fiscales = self.env["report.l10n_gt_sat.librofiscal"].get_libro(data)
        for libro in libros_fiscales:
            sheet_libro = workbook.add_worksheet(libro['descripcion'])


            sheet_libro.write(0, 0, data['form']['company_id'][1], self.bold)
            sheet_libro.write(1, 0, "Libro de " + libro['descripcion'], self.bold)
            sheet_libro.write(2, 0, "Del: " + libro['del'] + "Al: " + libro['del'], self.bold)

            vendedor = data['form']['vendedor']

            fila = 5
            columna = 0

            if libro['libro'] == 'sale':
                sheet_libro = self._get_libro_ventas(libro, sheet_libro, fila, columna, format1, date_format, vendedor)
            else:
                sheet_libro = self._get_libro_compras(libro, sheet_libro, fila, columna, format1, date_format)
