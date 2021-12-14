# -*- coding: utf-8 -*-

import xlrd
import binascii
import tempfile
import io
from odoo import api, fields, models, _
import logging
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime

# IMPORTANDO CLASE PARA CREAR XML
import xml.etree.cElementTree as ET


_logger = logging.getLogger(__name__)


try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportarTriumphServicios(models.TransientModel):

    _name = "britania.services.triumph.wizard"
    _description = "Importar Servicios Triumph de Excel"

    archivo = fields.Binary(string="Archivo (XLS)")

    def cargar_catalogo_excel(self):
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.archivo))
        fp.seek(0)
        values = []
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        product_template = []
        i = 0
        for row_no in range(sheet.nrows):
            i += 1
            if row_no <= 0:
                fields = map(lambda row: row.value.encode(
                    'utf-8'), sheet.row(row_no))
            else:
                line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode(
                                'utf-8') or str(row.value), sheet.row(row_no)))

                datos = {
                    'year': line[0],
                    'modelo': line[1],
                    'codigo_servicio': str(int(float(line[2]))),
                    'descripcion': line[3],
                    'tiempo': line[4],
                }
                print(i)
                servicio = self.crear_servicio(datos)

    def buscar_anio(self, anio_name):
        anio = self.env['fleet.model.year'].search([('name','=',anio_name)])
        if not anio:
            anio = self.env['fleet.model.year'].create({
                'name': anio_name,
            })
        return anio

    def buscar_modelo(self, modelo_name):
        modelo = self.env['fleet.vehicle.model'].search([('brand_id','=',67),('name','ilike',modelo_name)])
        if not modelo:
            modelo = self.env['fleet.vehicle.model'].create({
                'name': modelo_name,
                'brand_id': 67,
            })
        return modelo

    def crear_servicio(self, dato):
        year = self.buscar_anio(dato['year'])
        print(dato['modelo'])
        modelo_vehiculo = self.buscar_modelo(dato['modelo'])
        producto = self.env['product.product'].search([('default_code','=',dato['codigo_servicio'])])
        if producto:
            servicio = self.env['fleet.model.repair'].search([
                ('year_id','=',year.id),
                ('model_id','=',modelo_vehiculo.id),
                ('product_id','=',producto.id),
                ])
            if not servicio:
                servicio = self.env['fleet.model.repair'].create({
                    'year_id': year.id,
                    'model_id': modelo_vehiculo.id,
                    'product_id': producto.id,
                    'name': dato['descripcion'],
                    'labour_time': dato['tiempo'],
                })
        else:
            print("No existe codigo de servicio [%s]" % dato)
