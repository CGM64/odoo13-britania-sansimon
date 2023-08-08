# -*- coding: utf-8 -*-
from odoo import models,fields,api,_
from zeep import Client
from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class update_currency_rate(models.Model):
	_name = 'update.currency.rate'
	_description = 'Actualizar taza de cambio'

	def update_currency_rate(self):
		try:
			currency = self.env['res.currency'].search([('name','=','USD'),('active','=',True)])
			companias = self.env['res.company'].search([('actualizar_moneda','=',True)])
			Cliente = Client("http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?WSDL")
			respuesta = Cliente.service.TipoCambioDia()
			for compania in companias:
				if currency:
					rate_company = self.env['res.currency.rate']
					#Se obtiene la fecha del servicio xml, pero el retorno es un string
					fecha1 = respuesta['CambioDolar']['VarDolar'][0]['fecha']
					#Converitmos el string a un dato datetime
					fecha2 = datetime.strptime(fecha1,"%d/%m/%Y")
					#Registramos el ingreso en la base de datos
					rate_company.create({'name': fecha2,
										'company_id':compania.id,
										'currency_id':currency.id,
										'rate':float(1/float(respuesta['CambioDolar']['VarDolar'][0]['referencia']))})
		except Exception as e:
			print (e)

class update_currency_rate(models.Model):
	_name = 'res.currency'
	_inherit = 'res.currency'

	def fecha_min_move(self):
		sql_query = "select min(date) as fecha from account_move where state = %s"
		params = (('posted'),)
		self.env.cr.execute(sql_query, params)
		results = self.env.cr.dictfetchall()
		for dato in results:
			if dato['fecha']:
				return dato['fecha']
			else:
				return (datetime.today() + timedelta(days=-0)).strftime("%d-%m-%Y")


	#Funcion que sirve para ir a traer todas las tasas de cambio desde la creacion del primer movimiento de inventario
	#hasta el presente mes, creando la tasa en todas las empresas activas. Esto con el proposito de poder generar los estados
	#financieros y puedan ir a traer la tasa del dia exactamente.
	def update_tasas_qfaltan(self):
		# try:
		currency = self.env['res.currency'].search([('name','=','USD'),('active','=',True)])
		companias = self.env['res.company'].search([('actualizar_moneda','=',True)])
		Cliente = Client("http://www.banguat.gob.gt/variables/ws/TipoCambio.asmx?WSDL")

		min_fecha = self.fecha_min_move()
		if not min_fecha:
			return

		respuesta = Cliente.service.TipoCambioFechaInicial(min_fecha)
		fechas = respuesta['Vars']['Var']
		for dato in fechas:
			fecha = datetime.strptime(dato["fecha"],"%d/%m/%Y")
			hoy =  datetime.today()
			if fecha > hoy:
				return

			for compania in companias:
				if currency:
					rate_company = self.env['res.currency.rate']


					#Registramos el ingreso en la base de datos
					rate = rate_company.search([('name','=',fecha),('company_id','=',compania.id),('currency_id','=',currency.id)])
					if not rate:
						rate_company.create({'name': fecha,
										'company_id':compania.id,
										'currency_id':currency.id,
										'rate':float(1/float(dato["venta"]))})

		# except Exception as e:
		# 	print("Error SQL (update_tasas_qfaltan) --> %s)" % e)
