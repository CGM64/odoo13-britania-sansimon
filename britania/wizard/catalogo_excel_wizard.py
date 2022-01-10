# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime

#IMPORTANDO CLASE PARA CREAR XML
import xml.etree.cElementTree as ET


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
		('p7', 'Revisar Ventas Sin costos'),
		('p8', 'Asignar Origen'),
		('p9', 'Colocar codigo de barras'),
		('p10', 'Verificar proveedor'),
		('p11', 'Verificar proveedor Eliminar productos'),
		('p12', 'Verificar proveedor Actualizar productos'),
		('p13', 'Actualizar vendedor'),
		('p14', 'Generar xml de actividades economicas'),
		('p15', 'Generar xml de ocupación'),
		('p16', 'Asignar codigo nomina a provincia y municipio'),
		('p17', 'Actualizar el costo, en los productos servicio'),
	], required=True, default='p1')

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
		elif self.tipo_plantilla == 'p7':
			self._revisar_venta_sin_costo()
		elif self.tipo_plantilla == 'p8':
			self._asignar_origen()
		elif self.tipo_plantilla == 'p9':
			self._asignar_codigo_barras()
		elif self.tipo_plantilla == 'p10':
			self._verificar_asignar_proveedor()
		elif self.tipo_plantilla == 'p11':
			self._verificar_eliminar_proveedor_actualizar_producto()
		elif self.tipo_plantilla == 'p12':
			self._verificar_asignar_proveedor_actualizar_producto()
		elif self.tipo_plantilla == 'p13':
			self._actualiza_vededor_factura()
		elif self.tipo_plantilla == 'p14':
			self._generar_xml()
		elif self.tipo_plantilla == 'p15':
			self._generar_xml_ocupacion()
		elif self.tipo_plantilla == 'p16':
			self._asignar_codigo_nomina()
		elif self.tipo_plantilla == 'p17':
			self._asignar_costo_producto_servicio()

	#Funcion para actualizar el costo en el caso de los productos tipo servicio.
	#Esto con el proposito de realizar autoconsumos, todo se factura al costo, pero los codigos servicios no tienen costo.
	def _asignar_costo_producto_servicio(self):
		producto_servicio = self.env['product.template'].search([('type','=','service')])
		for pser in producto_servicio:
			if pser.default_code:
				pser.standard_price = pser.lst_price / 1.12
				print("%s %s %s" % (pser.default_code, pser.standard_price, pser.name))

	def _actualiza_vededor_factura(self):
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
				factura_line = {
					"name": line[0],
                    "comercial_id": int(round(float(line[1]),0)),
				}

				factura = self.env['account.move'].search([('name','=',factura_line['name'])])
				print("%s, %s, %s    " % (factura_line, factura.name, len(factura)))
				factura.invoice_user_id = factura_line['comercial_id']



	def _verificar_eliminar_proveedor_actualizar_producto(self):
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
                    "product_template_id": int(round(float(line[1]),0)),

				}
				product_template = self.env["product.template"].search([('id','=',producto_line['product_template_id'])])
				for product in product_template:
					print("%s. %s --> %s" % (i,producto_line, product.name))
					product.seller_ids.unlink()


	def _verificar_asignar_proveedor_actualizar_producto(self):
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
                    "product_template_id": int(round(float(line[1]),0)),
					"partner_id": int(round(float(line[7]),0)),
				}
				product_template = self.env["product.template"].search([('id','=',producto_line['product_template_id'])])
				for product in product_template:
					print("%s. %s --> %s" % (i,producto_line, product.name))
					#product.seller_ids.unlink()
					supplierinfo1 = self.env['product.supplierinfo'].create({
		                'product_tmpl_id': product.id,
		                'name': producto_line['partner_id'],
		                'min_qty': 1,
		                'price': product.standard_price,
		                'sequence': 1,
		            })

	def _verificar_asignar_proveedor(self):

		product_template = self.env["product.template"].search([
		#('id','=',3615)
		])
		i=0

		# Comienzo a buscar el producto en el detalle da la orden de Compra
		orden_compra_detalle = self.env["purchase.order.line"].search([])
		lista_producto_proveedor = {}
		for compra_detalle in orden_compra_detalle:
			lista_producto_proveedor[compra_detalle.product_id.product_tmpl_id.id] = compra_detalle.order_id.partner_id
		#print(proveedor)

		f = open("/mnt/extra-addons/Comelasa/proveedor.txt","r+")
		f.truncate(0)
		print("line|product_template_id|count|product_name|proveedor_name|es_cliente|es_proveedor|proveedor2_id|proveedor2|es_cliente2", file=f)




		for producto in product_template:
			i += 1
			filas = len(producto.seller_ids)

			ultimo_compra_proveedor = None
			for proveedor in producto.seller_ids.sorted(key=lambda m: (m.id)):
				ultimo_compra_proveedor = proveedor


			actual_proveedor = None

			if producto.id in lista_producto_proveedor.keys():
				actual_proveedor = lista_producto_proveedor[producto.id]
				print



			imprimir = ("%s|%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
				i,
				producto.id,
				filas,
				producto.name,
				(ultimo_compra_proveedor.name.name.replace('\n', '') if ultimo_compra_proveedor else False),
				(ultimo_compra_proveedor.name.customer_rank if ultimo_compra_proveedor else 0),
				(ultimo_compra_proveedor.name.supplier_rank if ultimo_compra_proveedor else 0),
				(actual_proveedor.id if actual_proveedor else ''),
				(actual_proveedor.name.replace('\n', '') if actual_proveedor else False),
				(actual_proveedor.customer_rank if actual_proveedor else 0),
				))
			print(imprimir, file=f)

		f.close



	def _asignar_codigo_barras(self):
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
                    "codigo": line[0].strip(),
                    "descripcion": line[3].strip(),
					"barra": line[4].strip(),
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
				duplicado = False
				cargado = 'nada'
				carga_valor = 0
				if product_product:
					encontro=True
					verificar_codigo_bara = self.env["product.product"].search([('barcode','=',producto_line["barra"])], limit=1)
					if verificar_codigo_bara:
						duplicado = True
						print("%s |Duplicado----------%s------------------ %s" % (i,encontro,producto_line))
					else:
						product_product.barcode = producto_line["barra"]
				else:
					print("%s |NO----------%s------------------ %s" % (i,encontro,producto_line))

				# with open("/mnt/extra-addons/Comelasa/holaSI.txt", 'a') as f:
				# 	if encontro:
				# 		print("%s|%s|%s|%s" % (
				# 		i,
				# 		producto_line['codigo'],
				# 		producto_line['descripcion'],
				# 		producto_line['barra'],
				# 		), file=f)
				#
				# with open("/mnt/extra-addons/Comelasa/holaNO.txt", 'a') as g:
				# 	if not encontro:
				# 		print("%s|%s|%s|%s" % (i,producto_line['codigo'],producto_line['descripcion'],producto_line['barra']), file=g)
				#
				# with open("/mnt/extra-addons/Comelasa/duplicado.txt", 'a') as h:
				# 	if duplicado:
				# 		print("%s|%s|%s|%s" % (i,producto_line['codigo'],producto_line['descripcion'],producto_line['barra']), file=h)





	def _revisar_venta_sin_costo(self):
		pedidos = self.env["sale.order"].search([('state','=','done'),('warehouse_id','=',1)],order='date_order, id')
		i=0
		for pedido in pedidos:
			i+=1


			despachos = self.env["stock.picking"].search([('sale_id','=',pedido.id)])
			for despacho in despachos:


				for monto_costo in despacho.move_lines.stock_valuation_layer_ids:
					with open("/mnt/extra-addons/Comelasa/comparando_costo.txt", 'a') as f:
						print("%s|%s|%s|%s|%s|%s|%s|%s|%s" % (
							i,
							pedido.id,
							pedido.date_order,
							monto_costo.product_id.name,
							str(monto_costo.unit_cost),
							str(monto_costo.value),
							str(monto_costo.quantity),
							str(monto_costo.product_id.standard_price),
							despacho.state,
						), file=f)





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


	def _asignar_origen(self):
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
                    "codigo": line[0].strip(),
					"descripcion": line[2].strip(),
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


				print("%s |----------%s------------------ %s" % (i,encontro,producto_line))

				with open("/mnt/extra-addons/Comelasa/holaSI.txt", 'a') as f:
					if encontro:
						product_template.origen = 'nacional'
						print("%s|%s|%s|%s|%s|%s" % (
						i,
						producto_line['codigo'],
						producto_line['descripcion'],
						product_product.id,
						product_product.default_code,
						product_product.name,
						), file=f)

				with open("/mnt/extra-addons/Comelasa/holaNO.txt", 'a') as g:
					if not encontro:
						print("%s|%s|%s|%s|%s" % (
							i,
							producto_line['codigo'],
							producto_line['descripcion'],
							False,
							False,
							), file=g)

	def _generar_xml(self):
		fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 0

		# CREANDO XML
		# Construimos el xml
		odoo = ET.Element("odoo")
		data = ET.SubElement(odoo, "data", noupdate="0")
		grupo1 = ""
		grupo2 = ""
		grupo3 = ""
		id_xml = "hr_economic_activity_"
		id = -1

		ruta = "/mnt/extra-addons/"

		for row_no in range(sheet.nrows):
			i += 1
			id += 1
			if row_no <= 0:
				fields = map(lambda row: row.value.encode(
						'utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode(
						'utf-8') or str(row.value), sheet.row(row_no)))
				if line[2] == "" and line[3] == "" and line[4] == "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
					ET.SubElement(record, "field",
									name="display_name").text = line[5]

					ET.SubElement(record, "field",
									name="categoria").text = line[0]

					if line[1] == "":
						pass
					else:
						code = line[1]
						ET.SubElement(record, "field",
										name="code").text =  code
					grupo1 = id_xml+str(id)
									
				elif line[1] == "" and line[3] == "" and line[4] == "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
						
					grupo2 = id_xml+str(id)

					ET.SubElement(record, "field",
									name="display_name").text = line[5]

					ET.SubElement(record, "field",
									name="categoria").text = line[0]
						
					code = line[2]
					ET.SubElement(record, "field",
									name="code").text =  code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo1}
					ET.SubElement(record, "field",
										attributes)
					id = id+1

				elif line[1] == "" and line[2] == "" and line[4] == "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
						
					grupo3 = id_xml+str(id)

					ET.SubElement(record, "field",
									name="display_name").text = line[5]

					ET.SubElement(record, "field",
									name="categoria").text = line[0]

					code = line[3]
					ET.SubElement(record, "field",
									name="code").text =  code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo2}
					ET.SubElement(record, "field",
									attributes)
					id = id+1

				elif line[1] == "" and line[2] == "" and line[3] == "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)

					ET.SubElement(record, "field",
									name="display_name").text = line[5]

					ET.SubElement(record, "field",
									name="categoria").text = line[0]
						
					code = line[4]
					ET.SubElement(record, "field",
									name="code").text = code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo3}
					ET.SubElement(record, "field",
									attributes)
					id = id+1
				elif line[1] == "" and line[2] == "" and line[3] == "" and line[4] == "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)

					ET.SubElement(record, "field",
									name="display_name").text = line[5]

					ET.SubElement(record, "field",
									name="categoria").text = line[0]

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo3}
					ET.SubElement(record, "field",
									attributes)
					id = id+1

		archivo = ET.ElementTree(odoo)
		archivo.write(ruta + "ejemplo.xml",
		xml_declaration=True,encoding='utf-8',
		method="xml")
		
	def _asignar_codigo_nomina(self):
		fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 0

		# CREANDO XML
		# Construimos el xml
		odoo = ET.Element("odoo")
		data = ET.SubElement(odoo, "data", noupdate="0")
		ruta = "/mnt/extra-addons/"

		id_xml = "hr_economic_activity_"
		id = -1

		for row_no in range(sheet.nrows):
			i += 1
			id += 1
			if row_no <= 0:
				fields = map(lambda row: row.value.encode(
						'utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode(
						'utf-8') or str(row.value), sheet.row(row_no)))

				if line[0] != "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
					ET.SubElement(record, "field",
									name="name").text = line[2]

					ET.SubElement(record, "field",
									name="code_nm").text = line[0]

					departamento = self.env['res.country.state'].search([('name','ilike',line[2])])
					departamento.code_nm = line[0]
									
				elif line[1] != "":
					attributes = {"model" : "hr.economic_activity", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)

					ET.SubElement(record, "field",
									name="name").text = line[2]

					ET.SubElement(record, "field",
									name="code_nm").text = line[1]
					municipio = self.env['res.country.municipio'].search([('name','ilike',line[2])])
					municipio.code_nm = line[1]

		archivo = ET.ElementTree(odoo)
		archivo.write(ruta + "ejemplo.xml",
		xml_declaration=True,encoding='utf-8',method="xml") 
	
	def _generar_xml_ocupacion(self):
		fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
		fp.write(binascii.a2b_base64(self.archivo))
		fp.seek(0)
		values = []
		workbook = xlrd.open_workbook(fp.name)
		sheet = workbook.sheet_by_index(0)
		product_template = []
		i = 0

		# CREANDO XML
		# Construimos el xml
		odoo = ET.Element("odoo")
		data = ET.SubElement(odoo, "data", noupdate="0")
		grupo1 = ""
		grupo2 = ""
		grupo3 = ""
		id_xml = "hr_occupation_"
		id = -1

		ruta = "/mnt/extra-addons/"

		for row_no in range(sheet.nrows):
			i += 1
			id += 1
			if row_no <= 0:
				fields = map(lambda row: row.value.encode(
					'utf-8'), sheet.row(row_no))
			else:
				line = list(map(lambda row: isinstance(row.value, bytes) and row.value.encode(
					'utf-8') or str(row.value), sheet.row(row_no)))
				if line[1] == "" and line[2] == "" and line[3] == "":
					attributes = {"model" : "hr.occupation", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
					ET.SubElement(record, "field",
								name="display_name").text = line[4]

					code = line[0]
					ET.SubElement(record, "field",
									name="code").text =  code
					grupo1 = id_xml+str(id)
								
				elif line[0] == "" and line[2] == "" and line[3] == "":
					attributes = {"model" : "hr.occupation", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
						
					grupo2 = id_xml+str(id)

					ET.SubElement(record, "field",
								name="display_name").text = line[4]
						
					code = line[1]
					ET.SubElement(record, "field",
									name="code").text =  code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo1}
					ET.SubElement(record, "field",
										attributes)
					id = id+1

				elif line[0] == "" and line[1] == "" and line[3] == "":
					attributes = {"model" : "hr.occupation", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)
						
					grupo3 = id_xml+str(id)

					ET.SubElement(record, "field",
								name="display_name").text = line[4]

					code = line[2]
					ET.SubElement(record, "field",
								name="code").text =  code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo2}
					ET.SubElement(record, "field",
									attributes)
					id = id+1

				elif line[0] == "" and line[1] == "" and line[2] == "":
					attributes = {"model" : "hr.occupation", "id" : id_xml+str(id)}
					record = ET.SubElement(data, "record", attributes)

					ET.SubElement(record, "field",
									name="display_name").text = line[4]
						
					code = line[3]
					ET.SubElement(record, "field",
									name="code").text = code

					id = id-1
					attributes = {"name" : "parent_id", "ref" : grupo3}
					ET.SubElement(record, "field",
									attributes)
					id = id+1

		archivo = ET.ElementTree(odoo)
		archivo.write(ruta + "ejemplo.xml",
		xml_declaration=True,encoding='utf-8',
		method="xml")