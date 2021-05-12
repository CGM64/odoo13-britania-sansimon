from odoo import models


class TestXlsx(models.AbstractModel):
    _name = 'report.update_listprice.report_list_price'
    _description = "Excel Reporte de lista de precios"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, model):
        i = 6
        formatTitle = workbook.add_format({'bold': True, 'font_size': 20})
        formatLabel = workbook.add_format(
            {'bold': True, 'font_color': 'black'})
        formatColumn = workbook.add_format(
            {'bold': True, 'font_color': 'black', 'align': 'center', 'border': 1, 'border_color': 'black'})
        formatPercentage = workbook.add_format(
            {'num_format': 2, 'font_color': 'black', 'border': 1, 'border_color': 'black'})
        formatData = workbook.add_format(
            {'font_color': 'black', 'border': 1, 'border_color': 'black'})
        sheet = workbook.add_worksheet('Lista de precios')
        sheet.set_column(1, 1, 50)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)

        # HEADER
        sheet.write(1, 1, model.name, formatTitle)

        sheet.write(3, 1, 'Aplicar en', formatLabel)
        if model.applied_on == '3_manual':
            sheet.write(3, 2, 'Manual')
        elif model.applied_on == '1_factura_compra':
            sheet.write(3, 2, 'Compra')
        elif model.applied_on == '2_proveedor':
            sheet.write(3, 2, 'Proveedor')
        elif model.applied_on == '0_categoria':
            sheet.write(3, 2, 'Categoria')

        sheet.write(4, 1, 'Calculo del precio', formatLabel)
        if model.compute_price == 'fixed':
            sheet.write(4, 2, 'Precio Fijo')
        elif model.compute_price == 'fixed_volume':
            sheet.write(4, 2, 'Precio Fijo por volumen')
        elif model.compute_price == 'percentage':
            sheet.write(4, 2, 'Porcentaje')
        elif model.compute_price == 'utilidad':
            sheet.write(4, 2, 'Grupo de Utilidad')

        sheet.write(3, 4, 'Categoria Producto', formatLabel)
        sheet.write(3, 5, model.categ_id.name)

        sheet.write(4, 4, 'Procentaje al Precio', formatLabel)
        sheet.write(4, 5, model.percent_price)

        # TABLA
        sheet.write(6, 1, 'Producto', formatColumn)
        sheet.write(6, 2, 'Original', formatColumn)
        sheet.write(6, 3, 'Nuevo', formatColumn)
        sheet.write(6, 4, '% Margen', formatColumn)
        sheet.write(6, 5, 'Diferencia', formatColumn)
        sheet.write(6, 6, '% Diferencia', formatColumn)
        for product in model.line_ids:
            i += 1
            sheet.write(i, 1, product.product_id.name, formatData)
            sheet.write(i, 2, product.price_original, formatData)
            sheet.write(i, 3, product.price_nuevo, formatData)
            sheet.write(i, 4, product.percent_margen, formatPercentage)
            sheet.write(i, 5, product.price_diferencia, formatData)
            sheet.write(i, 6, product.percent_diferencia, formatPercentage)
