# -*- coding: utf-8 -*-
from odoo import fields,models, api, _
from odoo.exceptions import UserError

class account_tax(models.Model):
	_inherit = "account.tax"
	#Flag: Indica si se aplica retencion, si esta habilitado, se realiza la funcion
	#get_taxes_values, definida en el modelo account_invoice
	impuesto_sat = fields.Selection([
		('retencion_iva','Retencion IVA'),
		('iva','Impuesto al valor agregado'),
		('isr','Impuesto sobre la renta'),
		('idp','Impuesto sobre distribucion de petroleo y derivados'),
		('itme','Impuesto Tasa Municipal Energía'),
		('ipeq','Impuesto Pequeño Contribuyente'),
		])

	sat_tipo_producto = fields.Selection([
		('bien','Bien'),
		('servicio','Servicio'),
		('exento','Excento'),
		('gas','Combustible'),
		('exp_in_ca_bien', 'Exportacion Bien in CA'),
		('imp_in_ca_bien', 'Importacion Bien in CA'),
		('imp_out_ca_bien', 'Importacion Bien out CA'),
		])
