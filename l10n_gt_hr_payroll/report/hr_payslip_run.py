from odoo import api, fields, models, _
import logging
from datetime import datetime
import base64
import re
import json
from odoo.tools import date_utils
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class Payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    def datos_empleado(self):
        diccionario = {}
        lista = []

        for line in self.slip_ids:
            diccionario = {
                "nombre": line.employee_id.name,
                "idregistro": line.employee_id.registration_number,
                "puesto": line.employee_id.job_title,
                "fecha_alta": line.contract_id.date_start,
                "salario_ordinario": str(format(round(line.contract_id.wage, 2), ',')),
                "dias_trabajados": line.worked_days_line_ids.number_of_days,
                "dias_septimo": 0,
                "dias_vacaciones": 0,
                "diurno": 0,
                "nocturno": 0,
                "ordinario": 0,
                "extraordinario": 0,
                "septimo": 0,
                "asueto": 0,
                "vacaciones": 0,
                "total_devengado": 0,
                "Bantrab":0,
                "default":0,
            }
            for item in line.line_ids:
                diccionario[item.name] = str(
                    format(round(item.amount, 2), ','))

            lista.append(diccionario)

        return lista

    def totales(self):
        diccionario2 = {'default':0,}
        lista2 = []
        suma_liquido = 0
        suma_bono_decreto = 0
        suma_total_descuento = 0
        suma_otros = 0
        suma_prestamo = 0
        suma_isr = 0
        suma_igss = 0
        suma_total_ingresos = 0
        suma_ordinario = 0
        suma_base = 0
        for line in self.slip_ids:
            for item in line.line_ids:
                if item.name == "Liquido a Recibir":
                    suma_liquido = suma_liquido + item.amount
                    diccionario2["total_liquido"] = str(
                        format(round(suma_liquido, 2), ','))
                if item.name == "Bono Decreto":
                    suma_bono_decreto = suma_bono_decreto + item.amount
                    diccionario2["total_bono_decreto"] = str(format(round(
                        suma_bono_decreto, 2), ','))
                if item.name == "Total de Descuentos":
                    suma_total_descuento = suma_total_descuento + item.amount
                    diccionario2["suma_total_descuento"] = str(format(round(
                        suma_total_descuento, 2), ','))
                if item.name == "Otros":
                    suma_otros = suma_otros+item.amount
                    diccionario2["suma_otros"] = str(
                        format(round(suma_otros, 2), ','))
                if item.name == "Bantrab":
                    suma_prestamo = suma_prestamo + item.amount
                    diccionario2["suma_prestamo"] = str(
                        format(round(suma_prestamo, 2), ','))
                if item.name == "ISR":
                    suma_isr = suma_isr + item.amount
                    diccionario2["suma_isr"] = str(
                        format(round(suma_isr, 2), ','))
                if item.name == "Cuota Laboral IGSS":
                    suma_igss = suma_igss + item.amount
                    diccionario2["suma_igss"] = str(
                        format(round(suma_igss, 2), ','))
                if item.name == "Total de Ingresos":
                    suma_total_ingresos = suma_total_ingresos + item.amount
                    diccionario2["suma_total_ingresos"] = str(
                        format(round(suma_total_ingresos, 2), ','))
                if item.name == "Sueldo x Dias":
                    suma_ordinario = suma_ordinario + item.amount
                    diccionario2["suma_ordinario"] = str(
                        format(round(suma_ordinario, 2), ','))
                if item.name == "Basic Salary":
                    suma_base = suma_base + item.amount
                    diccionario2["suma_base"] = str(
                        format(round(suma_base, 2), ','))

        lista2.append(diccionario2)
        return lista2

    def print_report(self):
        return self.env.ref('l10n_gt_hr_payroll.l10n_gt_hr_payroll_nomina_report').report_action(self)

    def export_txt(self):
        normalizar = lambda parametro : parametro if parametro else ''
      
        regexLetras = "[^a-zA-Z0-9_ ]"
        reLetras = {'á': 'a', 'Á': 'A',
                    'é': 'e', 'É': 'E',
                    'í': 'i', 'Í': 'I',
                    'ó': 'o', 'Ó': 'O',
                    'ú': 'u', 'Ú': 'U',
                    'ñ': 'n', 'Ñ': 'N',}

        MESES = {'1': 'Enero',      '2': 'Febrero', '3': 'Marzo',     '4': 'Abril',
                 '5': 'Mayo',       '6': 'Junio',   '7': 'Julio',     '8': 'Agosto',
                 '9': 'Septiembre','10': 'Octubre','11': 'Noviembre','12': 'Diciembre', }

        diccionario = {}
        lista = []
        lista_lineas = []
        ach=[]

        #Obtengo la fecha de inicio y de final de la planilla para validad si ambas fechas son del mismo mes.
        fecha_inicio = (datetime.strptime(str(self.date_start), '%Y-%m-%d')).timetuple()
        fecha_fin = (datetime.strptime(str(self.date_end), '%Y-%m-%d')).timetuple()

        #Valido si el mes inicio es igual al mes final y obtengo el número del mes, luego obtengo el valor según
        #la llave del diccionario
        if fecha_inicio.tm_mon == fecha_fin.tm_mon:
            mes = MESES[str(fecha_inicio.tm_mon)]

        id_planilla=self.id
        datos = self.slip_ids.filtered( lambda ch: ch.contract_id.forma_pago in  ('transferencia','ach'))
        cor_trans=0
        cor_ach=0
        for line in datos:
            nombre = line.employee_id.name
            for clave, valor in reLetras.items():
                nombre = nombre.replace(clave, valor)
            nombre_modificado = re.sub(regexLetras, "", nombre)

            diccionario = {
                "idplanilla": str(id_planilla)+' '+ self.name,
                "idempleado":normalizar(line.employee_id.registration_number),
                "nombre": normalizar(nombre_modificado),
                "cuentaBancaria": normalizar(line.employee_id.bank_account_id.acc_number),
                "ach_quetzales": str(line.employee_id.bank_account_id.bank_id.ach_quetzales),
                "ach_dolares": str(line.employee_id.bank_account_id.bank_id.ach_dolares),
            }
            diccionario['correo_trabajo']= "," + str(line.employee_id.work_email) if line.employee_id.work_email !=False else ","
            diccionario["tipo"] = '1' if line.employee_id.bank_account_id.account_type_id == 'monetaria' else '2'
            lista.append(diccionario)
            monto = line.line_ids.filtered(lambda x: x.code == 'LIQRE')
            diccionario["Liquido"] = round(monto.amount,2)
        
            if line.employee_id.contract_id.forma_pago == "transferencia":
                cor_trans+=1
                if diccionario['Liquido']>0:
                    diccionario['lineas']=(str(diccionario['tipo']) +","+str(diccionario['cuentaBancaria'])+","+ str(cor_trans)+","+diccionario['nombre']+","+str(diccionario['Liquido'])+","+diccionario['idplanilla'])
                    lista_lineas.append(diccionario)
            else:
                cor_ach+=1
                codigo_ach=''
                if line.employee_id.bank_account_id.currency_id.symbol==False:
                    codigo_ach=diccionario['ach_quetzales']
                elif line.employee_id.bank_account_id.currency_id.symbol=="Q":
                    codigo_ach=diccionario['ach_quetzales']
                elif line.employee_id.bank_account_id.currency_id.symbol=="$":
                    codigo_ach=diccionario['ach_dolares']
                if diccionario['Liquido']>0:
                    diccionario['ach']=str(cor_ach)+","+diccionario['nombre']+","+str(codigo_ach)+","+str(diccionario['cuentaBancaria'])+","+str(diccionario['tipo'])+","+str(diccionario['Liquido'])
                    ach.append(diccionario)
        return lista_lineas,ach

    def transferencia(self):
        lista_lineas,ach=self.export_txt()
        return lista_lineas
    
    def ach(self):
        lista_lineas,ach=self.export_txt()
        print("#####===== ACH")
        print(lista_lineas)
        return ach
    
    def export_xls(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['libro', 'tipo', 'periodo', 'ejercicio', 'company_id', 'vendedor'])[0]
        return self.env.ref('l10n_gt_hr_payroll.report_planilla_excel').report_action(self,data=data)