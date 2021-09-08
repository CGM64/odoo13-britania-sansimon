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

	_name = "britania.products.triumph.wizard"
	_description = "Importar Pedidos de Excel"

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
				
				tri_product = self.env['tri.product'].search([('default_code','=',line[0])], limit=1)
				tri_group = self.env['tri.product.group'].search([('name','=',line[2])], limit=1)
				
				if not tri_group:
					group = self.env['tri.product.group'].create({
                		"name": line[2],
            		})

				if tri_product:
					tri_product.standard_price = line[3]
				else:
					product = self.env['tri.product'].create({
                		"name": line[1],
                		"default_code": line[0],
                		"standard_price": float(line[3]),
                		"group": int(tri_group.id),
            		})
		self.update_product()
	
	def update_product(self):
		product_t = self.env['tri.product'].search([])
		if product_t:
			for product in product_t:
				product_p = self.env['product.product'].search([('default_code','=',product.default_code)], limit=1)
				if product_p:
					product_p.list_price = product.price_mar
	
	#METODO PARA CREAR PRODUCTO EN PRODUCT PRODUCT
	def update_pricelist_line(self,id_product,id_tarifa):
		pricelist_item = self.env['product.pricelist.item'].search([('product_tmpl_item','=',id),('pricelist_id','=',id_tarifa)], limit=1)