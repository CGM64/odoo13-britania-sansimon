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

        i = 0;
        sheet_libro.write(i,0,"Linea")
        sheet_libro.write(i,1,"Codigo")
        sheet_libro.write(i,2,"Descripcion")
        sheet_libro.write(i,3,"Ext. Actual")
        sheet_libro.write(i,4,"Cnt. Ini.")
        sheet_libro.write(i,5,"Entradas")
        sheet_libro.write(i,6,"Salidas")
        sheet_libro.write(i,7,"Cnt. Final")
        sheet_libro.set_column(0,0,5)
        sheet_libro.set_column(1,1,16)
        sheet_libro.set_column(2,2,60)
        sheet_libro.set_column(3,7,12)




        productos = self.env['product.product'].search([
                ('active','=',True),
                ('qty_available','>',0),
                #('id','=',1826),
                ])
        productos = productos.filtered(lambda p: p.type != 'service')
        #print(data)
        fecha_inicio = data['form']['fecha_inicio']
        fecha_fin = data['form']['fecha_fin']
        res = productos._compute_quantities_dict(None, None, None, fecha_inicio, fecha_inicio)


        for producto in productos:
            Move = self.env['stock.move']
            domain_quant_loc, domain_move_in_loc, domain_move_out_loc = producto.with_context(company_owned=True)._get_domain_locations()
            domain_move_in = [('product_id', '=', producto.id),('state', '=', 'done'), ('date', '>=', fecha_inicio), ('date', '<=', fecha_fin)] + domain_move_in_loc
            domain_move_out = [('product_id', '=', producto.id),('state', '=', 'done'), ('date', '>=', fecha_inicio), ('date', '<=', fecha_fin)] + domain_move_out_loc

            moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
            moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out, ['product_id', 'product_qty'], ['product_id'], orderby='id'))


            i+=1
            sheet_libro.write(i,0,i)
            sheet_libro.write(i,1,producto.default_code)
            sheet_libro.write(i,2,producto.name)
            sheet_libro.write(i,3,producto.qty_available)

            sheet_libro.write(i,4,res[producto.id]['qty_available'])
            sheet_libro.write(i,5,moves_in_res.get(producto.id, 0.0))
            sheet_libro.write(i,6,moves_out_res.get(producto.id, 0.0))

            cantidad_final = res[producto.id]['qty_available'] + moves_in_res.get(producto.id, 0.0) - moves_out_res.get(producto.id, 0.0)
            sheet_libro.write(i,7,cantidad_final)

            sheet_libro.write(i,8,producto.categ_id.name)

            lista = self.categoria(producto.categ_id.id)
            j=7
            for categoria in lista:
                j += 1
                sheet_libro.write(i,j,categoria)


    def categoria(self, categoria_id):
        lista = list()
        categorias = self.env['product.category'].search([('id','=',categoria_id)])
        for categoria in categorias:

            lista.append(categoria.name)
            if categoria.parent_id:
                lista = self.categoria(categoria.parent_id.id) + lista
        return lista



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
