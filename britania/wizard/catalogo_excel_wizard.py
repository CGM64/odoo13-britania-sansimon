# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


_logger = logging.getLogger(__name__)

import io
import tempfile
import binascii
import xlrd
from datetime import datetime

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

class ImportarCatalogosExcel(models.TransientModel):

	_name = "comelasa.importar.catalogos.excel.wizard"
	_description = "Importar Pedidos de Excel"

	archivo = fields.Binary(string="Archivo (XLS)")
	tipo_plantilla = fields.Selection([
		('p1', 'Revisar Productos'),
		('p2', 'Actualizar Costos'),
		('p3', 'Subir Pedido de Ventas'),
	], required=True, default='p3')



	def cargar_catalogo_excel(self):
		if self.tipo_plantilla == 'p1':
			self._revisar_producto()
		if self.tipo_plantilla == 'p2':
			self._actualizar_sale_margin()
		if self.tipo_plantilla == 'p3':
			self._subir_ventas()

	def _subir_ventas(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 0
		una_vez = True

		for row_no in range(sheet.nrows):
			i+=1
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}

				producto_line = {
					"pedido_id": int(float(line[3].strip())) if line[3] else 0,
                    "articulo": line[4].strip(),
                    "cantidad": int(float(line[6].strip())) if line[6] else 0,
					"precio": float(line[7].strip()) if line[7] else 0,
				}
				if una_vez:
					compra = self.env["purchase.order"].search([('id','=',producto_line['pedido_id'])])
					compra.order_line.unlink()
					una_vez = False


				product_product = None
				product_template = self.env["product.template"].search([('default_code','=',producto_line['articulo'])])
				if len(product_template) > 1:
					print("Producto Duplicado %s" % producto_line)
				else:
					if product_template:
						if product_template.type == 'product':
							product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])

							linea_venta = {
								'order_id': producto_line['pedido_id'],
								'product_id': product_product.id,
								'product_qty': producto_line['cantidad'],
								'product_uom': 1,
								'price_unit': producto_line['precio'],
								'name': product_product.name,
								'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
							}
							detalle_id = self.env['purchase.order.line'].create(linea_venta)
							detalle_id._compute_tax_id()
						else:
							print("Producto no es almacenable %s" % producto_line)
					else:
						print("No se encontro %s" % producto_line)

	def _actualizar_sale_margin(self):
		print("Si llego")
		pedido_detalle = self.env["sale.order.line"].search([])
		for linea in pedido_detalle:
			linea.product_id_change_margin()
			print(linea.name)

	def _revisar_producto(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 0

		for row_no in range(sheet.nrows):
			i+=1
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}

				producto_line = {
                    "articulo": line[0].strip(),
                    "tipo": line[1].strip(),
					"descripcion1": line[2].strip(),
					"categoria": line[3].strip(),
					"grupo": line[4].strip(),
					"familia": line[5].strip(),
					"linea": line[6].strip(),
					"precio": float(line[7].strip()) if line[7] else 0,
					"costopromedio": float(line[8].strip()) if line[8] else 0,
					"grupodeutilidad": line[9].strip(),
					"porcentajesobreprecio": float(line[10].strip()) if line[10] else 0,
					"volumen": float(line[11].strip()) if line[11] else 0,
					"fabricante": line[12].strip(),
				}
				product_product = None
				product_template = self.env["product.template"].search([('default_code','=',producto_line['articulo'])])
				if product_template:
					product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])
					product_template.categ_id = self._get_Categoria(
						producto_line["categoria"],
						producto_line["grupo"],
						producto_line["familia"],
						producto_line["linea"],
					)
					product_template.marca_id = self._get_Marca(producto_line['fabricante'])
					product_template.volume = producto_line['volumen']

					print("%s |----- %s" % (i, producto_line))

				else:
					print("%s |-NO ENCONTRO---- %s" % (i, producto_line))

	def _get_Marca(self, name):
		#print("que pasa nombre (%s) y porcentaje(%s)" % (name,porcentaje))
		if name:
			marca = self.env["product.marca"].search([("name","=", name)])
			if not marca:
				marca = self.env["product.marca"].create({
				"name": name,
				})
			return marca.id
		#Si trae null la categoria de intelisis entonce se le asigna la categoria padre.
		return None

	def _get_Categoria(self, name, grupo_name, familia_name, linea_name):
		categoria_padre = self.env["product.category"].search([("name","=", "Saleable")])
		categoria = categoria_padre
		if name:
			categoria = self.env["product.category"].search([("name","=", name)])
			if not categoria:
				categoria = self.env["product.category"].create({
                "name": name,
                "parent_id": categoria_padre.id,
                "property_cost_method": 'fifo',
                "property_valuation": 'real_time',
                })

		if grupo_name:
			categoria_padre = categoria
			categoria = self.env["product.category"].search([("name","=", grupo_name),('parent_id','=',categoria_padre.id)])
			if not categoria:
				categoria = self.env["product.category"].create({
                "name": grupo_name,
                "parent_id": categoria_padre.id,
                "property_cost_method": 'fifo',
                "property_valuation": 'real_time',
				})

		if familia_name:
			categoria_padre = categoria
			categoria = self.env["product.category"].search([("name","=", familia_name),('parent_id','=',categoria_padre.id)])
			if not categoria:
				categoria = self.env["product.category"].create({
                "name": familia_name,
                "parent_id": categoria_padre.id,
                "property_cost_method": 'fifo',
                "property_valuation": 'real_time',
                })

		if linea_name:
			categoria_padre = categoria
			categoria = self.env["product.category"].search([("name","=", linea_name),('parent_id','=',categoria_padre.id)])
			if not categoria:
				categoria = self.env["product.category"].create({
                "name": linea_name,
                "parent_id": categoria_padre.id,
                "property_cost_method": 'fifo',
                "property_valuation": 'real_time',
                })

        #Si trae null la categoria de intelisis entonce se le asigna la categoria padre.
		return categoria.id
