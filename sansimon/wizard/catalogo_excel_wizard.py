# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime


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
		('p1', 'Carga de Productos'),
		('p2', 'Cargo de Orden de Compra'),
		('p3', 'Cargo de Existencias'),
		('p4', 'Transferencia'),
		('p5', 'Actualizar costos'),
		('p6', 'Revisar Articulos'),
	], required=True, default='p6')

	ubicacion = fields.Many2one('stock.location', string='Ubicacion')
	inventario = fields.Many2one('stock.inventory', string='Inventario')
	transferencia = fields.Many2one('stock.picking', string='Transferencia')
	counterpart_account_id = fields.Many2one(
        'account.account', string="Counter-Part Account",
        domain=[('deprecated', '=', False)])

	def cargar_catalogo_excel(self):
		if self.tipo_plantilla == 'p1':
			self._cargar_catalogo_productos()
		elif self.tipo_plantilla == 'p2':
			self._carga_orden_compra()
		elif self.tipo_plantilla == 'p3':
			self._carga_existencia()
		elif self.tipo_plantilla == 'p4':
			self._carga_transferencia()
		elif self.tipo_plantilla == 'p5':
			self._actualizar_costos()
		elif self.tipo_plantilla == 'p6':
			self._revisar_producto()

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
                    "barra": line[0].strip(),
                    "empresa": line[1].strip(),
					"codigo": line[2].strip(),
					"descripcion": line[3].strip(),
					"existencia": line[4].strip(),
					"costo": float(line[5].strip()) if line[5] else 0,
					"costototal": float(line[5].strip()) if line[5] else 0,
				}

				product_product = None
				product_template = self.env["product.template"].search([('default_code','=',producto_line['codigo'])], limit=1)
				if product_template:
					product_product = None
					product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])
				else:
					product_product = None
					product_template = self.env["product.template"].search([('name','=',producto_line['descripcion'])], limit=1)
					if product_template:
						product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])

				encontro = False
				cargado = 'nada'
				carga_valor = 0
				if product_product:
					encontro = True

					carga = self.env["stock.move.line"].search([
							('location_id','=',14),
							('location_dest_id','=',8),
							('state','=','done'),
							('product_id','=',product_product.id)
					])
					for c in carga:
						cargado = 'cargado'
						carga_valor += c.qty_done

					descarga = self.env["stock.move.line"].search([
							('location_id','=',8),
							('location_dest_id','=',14),
							('state','=','done'),
							('product_id','=',product_product.id)
					])
					for d in descarga:
						cargado = 'cargado/descargado'
						carga_valor -= d.qty_done



				print("%s |----------%s------------------ %s" % (i,encontro,producto_line))

				with open("/mnt/extra-addons/Comelasa/holaSI.txt", 'a') as f:
					if encontro:
						print("%s|%s|%s|%s|%s|odoo|%s|%s|%s|carga|%s|%s" % (
						i,
						producto_line['codigo'],
						producto_line['descripcion'],
						producto_line['existencia'],
						producto_line['costo'],
						product_product.product_tmpl_id.name,
						product_product.standard_price,
						product_product.qty_available,
						cargado,  #Valor true si esta en la carga inicial, y falso si no
						carga_valor,
						), file=f)

				with open("/mnt/extra-addons/Comelasa/holaNO.txt", 'a') as g:
					if not encontro:
						print("%s|%s|%s|%s|%s" % (i,producto_line['codigo'],producto_line['descripcion'],producto_line['existencia'],producto_line['costo']), file=g)



	def _actualizar_costos(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 2

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}

				producto_line = {
                    "codigo1": line[0].strip(),
                    "codigo2": line[1].strip(),
					"codigo3": line[2].strip(),
					"descripcion": line[3].strip(),
					"existencia": line[4].strip(),
					"costo": float(line[5].strip()) if line[5] else 0,
					}
				if producto_line:

					product_template = self.env["product.template"].search([('default_code','=',producto_line['codigo2'])], limit=1)
					if product_template:
						product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])
					else:
						product_template = self.env["product.template"].search([('name','=',producto_line['descripcion'])], limit=1)
						if product_template:
							product_product = self.env["product.product"].search([('product_tmpl_id','=',product_template.id)])

						else:
							product_product = None
							print("%s |----------NO------------------ %s" % (i,producto_line))

					if product_product:
						costo_anterior = product_product.standard_price
						if costo_anterior != producto_line['costo']:
							product_product._change_standard_price(producto_line['costo'], counterpart_account_id=self.counterpart_account_id.id)
							costo_nuevo = product_product.standard_price
							print("%s |- [%s] (%s) Costo anterior (%s), Consto nuevo(%s), ExistenciaActual(%s), ExistenciaNueva(%s)" % (product_product.product_tmpl_id.id,product_product.default_code,producto_line['descripcion'], str(costo_anterior), str(producto_line['costo']), str(product_product.qty_available), producto_line['existencia']))
				i+=1

	def _carga_transferencia(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 1

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}

				producto_line = {
                    "referencia_interna": line[0].strip(),
                    "nombre": line[2].strip(),
					"cantidad": float(line[5].strip()) if line[5] else 0.0,
					}
				if producto_line['cantidad'] > 0:
					product = self.env["product.product"].search([('name','=',producto_line['nombre'])], limit=1)
					if product:
						product_line = self.env["stock.inventory.line"].search([('inventory_id','=',self.inventario.id),('product_id','=',product.id)])
						if product_line:
							product_line.product_qty = producto_line['cantidad']
						else:
							new_linea_inventario = {}
							new_linea_inventario['picking_id'] = self.transferencia.id
							new_linea_inventario['name'] = product.display_name
							new_linea_inventario['description_picking'] = product.name
							new_linea_inventario['product_id'] = product.id
							new_linea_inventario['location_id'] = self.transferencia.location_id.id
							new_linea_inventario['location_dest_id'] = self.transferencia.location_dest_id.id
							new_linea_inventario['picking_type_id'] = self.transferencia.picking_type_id.id
							#new_linea_inventario['product_qty'] = producto_line['cantidad']
							new_linea_inventario['product_uom'] = 1
							new_linea_inventario['product_uom_qty'] = producto_line['cantidad']
							new_linea_inventario['company_id'] = self.env.user.company_id.id
							self.env["stock.move"].create(new_linea_inventario)
					else:
						print("%s |---------------------------- %s" % (i,producto_line))
					i+=1

	def _carga_existencia(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 1

		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}

				producto_line = {
                    "referencia_interna": line[0].strip(),
                    "nombre": line[2].strip(),
					"cantidad": float(line[5].strip()) if line[5] else 0.0,
					}
				if producto_line['cantidad'] > 0:
					product = self.env["product.template"].search([('name','=',producto_line['nombre'])], limit=1)
					product = self.env["product.product"].search([('product_tmpl_id','=',product.id)], limit=1)
					if product:
						product_line = self.env["stock.inventory.line"].search([('inventory_id','=',self.inventario.id),('product_id','=',product.id)])
						if product_line:
							product_line.product_qty = producto_line['cantidad']
						else:
							new_linea_inventario = {}
							new_linea_inventario['inventory_id'] = self.inventario.id
							new_linea_inventario['product_id'] = product.id
							new_linea_inventario['location_id'] = self.ubicacion.id
							new_linea_inventario['product_qty'] = producto_line['cantidad']
							new_linea_inventario['company_id'] = self.env.user.company_id.id
							self.env["stock.inventory.line"].create(new_linea_inventario)
					else:
						print("%s |---------------------------- %s" % (i,producto_line))
					#print("%s |---------------------------- %s" % (i,producto_line))
					i+=1

	def _carga_orden_compra(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 1
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}
				producto_line = {
                    "orden_id": line[0],
                    "producto_id": line[1].strip(),
					"descripcion": line[2].strip(),
                    "cantidad": line[3],
                    "precio": line[4],
					}
				product_id = self._find_products(producto_line['producto_id'])
				if product_id:
					producto['product_id'] = product_id.id
					producto['name'] = producto_line['descripcion']
					producto['product_qty'] = producto_line['cantidad']
					producto['product_uom'] = product_id.uom_po_id.id
					producto['price_unit'] = producto_line['precio']
					producto['date_planned'] = datetime.today()
					producto['order_id'] = int(float(producto_line['orden_id']))
					order = self.env['purchase.order.line'].create(producto)
					_logger.info("Creando producto %s codigo %s" % (i, producto_line['producto_id']))
				else:
					_logger.info("No se creo producto %s codigo %s" % (i, producto_line['producto_id']))
				i += 1

	def _find_products(self, product):
		find_codigo = self.env['product.template'].search([("default_code","=",product)], limit=1)
		return find_codigo

	def _cargar_catalogo_productos(self):
		fp = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 1
		for row_no in range(sheet.nrows):
			if row_no <= 0:
				fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
				producto = {}
				producto_line = {
                    "codigo": line[0].strip(),
                    "marca": line[1],
                    "name": line[3].strip(),
                    "padre": line[5],
                    "categoria": line[6],
                    "costo": line[7],
                    "precio": line[8],
                    "proveedor": line[11],
					#"dai": line[12],
					}
				producto['name'] = producto_line['name']
				producto['default_code'] = producto_line['codigo']
				producto['product_brand_id'] = self._get_Marca(producto_line['marca']).id
				producto['type'] = 'product'
				producto['categ_id'] = self._get_Categoria(producto_line['padre'], producto_line['categoria']).id
				producto['list_price'] = producto_line['precio']
				producto['standard_price'] = producto_line['costo']
				#producto['dai_id'] = self._get_Dai(producto_line['dai'])
				product_template = self.create_products(producto, producto_line, i)
				_logger.info("Creando producto %s codigo %s" % (i, product_template["name"]))
				i += 1

	def _get_Dai(self, dai):
		dai_id = self.env['product.dai'].search([('name','=',dai)])
		if dai_id:
			return dai_id.id
		return None

	def _get_Marca(self, marca):
		brand = self.env['product.brand'].search([('name','ilike',marca)],limit=1)
		if not brand:
			brand = self.env['product.brand'].create({
                "name": marca
            })
		return brand

	def _get_Categoria(self, padre, categoria):
		padre_categoria = self.env['product.category'].search([('name','=',padre)], limit=1)
		if not padre_categoria:
			padre_categoria = self.env['product.category'].search([('name','=','All')])
			padre_categoria = self.env['product.category'].create({
                "name": padre,
                "parent_id": padre_categoria.id,
            })

		categoria_producto = self.env['product.category'].search([('name','=',categoria)], limit=1)
		if not categoria_producto:
			categoria_producto = self.env['product.category'].create({
                "name": categoria,
                "parent_id": padre_categoria.id,
            })

		return categoria_producto



	def create_products(self, product, producto_line, contador):
		find_codigo = self.env['product.template'].search([("default_code","=",product["default_code"])], limit=1)
		if not find_codigo:
			find_codigo = self.env['product.template'].create(product)
			supplierinfo1 = self.env['product.supplierinfo'].create({
                'product_tmpl_id': find_codigo.id,
                'name': self._get_Contacto(producto_line['proveedor']).id,
                'min_qty': 1,
                'price': product['standard_price'],
                'sequence': 1,
            })
			name = ('product_comelasa_template_%s' % str(find_codigo.id).strip())
			self.env['ir.model.data'].create({
	            'name': name,
	            'model': 'product.template',
	            'module': '__export__',
	            'res_id': find_codigo.id,
				})

		else:
			find_codigo["name"] = product["name"]
		return find_codigo

	def _get_Contacto(self, nombre):
		contacto = self.env['res.partner'].search([('name','ilike',nombre)], limit=1)
		if not contacto:
			contacto = self.env['res.partner'].create({
                "name": nombre,
            })
		return contacto
