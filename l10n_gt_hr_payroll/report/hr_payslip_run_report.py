import abc
import re
from typing import List
from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime, date

class HrPayslipRunInherit(models.Model):
    _inherit = "hr.payslip.run"
    _description = "Reporte PDF de la planilla de fin de mes"


    def print_report(self):
        return self.env.ref('l10n_gt_hr_payroll.l10n_gt_hr_payroll_nomina_report').report_action(self)

    def type(self,dato):
        tipo=str(type(dato)).replace('<class','').replace("'",'').replace('>','').replace(' ','')
        return tipo

    def _get_dis_laborados(self, payslip):
        fecha_inicio = payslip.date_from.replace(month=payslip.date_from.month, day=1, year=payslip.date_from.year)
        fecha_fin = payslip.date_to

        empleado_nomina_anticpo = payslip.env['hr.payslip'].search([
                ('struct_id','in',( payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id, 
                                    payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id)),
                ('state','in',('done','verify')),
                ('contract_id','=', payslip.contract_id.id),
                ('date_from','>=',fecha_inicio),
                ('date_to','<=',fecha_fin)
                ])
        return sum(calculo.number_of_days for calculo in empleado_nomina_anticpo.worked_days_line_ids.filtered(lambda payslip: payslip.code == 'WORK100'))

    def _get_nominas_bonos(self, payslip):
        fecha_inicio = payslip.date_from.replace(month=payslip.date_from.month, day=1, year=payslip.date_from.year)
        fecha_fin = payslip.date_to

        empleado_nomina_bono = payslip.env['hr.payslip'].search([
                ('struct_id','in',(payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id,)),
                ('state','in',('done','verify')),
                ('contract_id','=', payslip.contract_id.id),
                ('date_from','>=',fecha_inicio),
                ('date_to','<=',fecha_fin)
                ])
        return sum(calculo.total for calculo in empleado_nomina_bono.line_ids.filtered(lambda payslip: payslip.code in ('LIQRE',)))


    def generate_xlsx_report(self):
        estructura = self.slip_ids.struct_id.id
        if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id:
            # ITERO LAS LINEAS DEL MODELO Y ASIGNO LAS VARIABLES DE ENCABEZADO AL DICCIONARIO
            consulta_departamento = request.env['hr.department'].search([])
            lista_departamento = []
            l=[]
            l_claves=[]
            
            for departamento in consulta_departamento:
                lista_empleados = []
                nominas = self.slip_ids.filtered( lambda nom: nom.contract_id.department_id.id == departamento.id)
                nominas = nominas.sorted(lambda emp: emp.contract_id.employee_id.name)

                listado_clave = []
                listado_subtotal=[]
                listado_total=[]

                for empleado in nominas:
                    for linea in empleado.line_ids:
                        clave = linea.code
                        if clave not in (listado_clave):
                            listado_clave.append(clave)

                for empleado in nominas:
                    d_empleados = {
                        "ID": empleado.employee_id.id,
                        "EMPLEADO": empleado.employee_id.name,
                        "FECHA_INGRESO": empleado.contract_id.date_start,

                        "FORMA_PAGO": empleado.employee_id.contract_id.forma_pago.upper(),
                        "OBSERVACIONES": '',
                        "DEFAULT": 0,
                    }

                    #d_empleados.update(d_empleados_1q)
                    d_empleados['D_LABORADOS'] = self._get_dis_laborados(empleado)
                    d_empleados['TOTAL_BONOS'] = self._get_nominas_bonos(empleado)

                    for linea in listado_clave:
                        clave = linea
                        d_empleados[clave] = sum([line.amount for line in empleado.line_ids.filtered(lambda emp: emp.code == linea)])
                    lista_empleados.append(d_empleados)

                sub_total_emp = {}
                for sum_clave in listado_clave:
                    sub_total_emp[sum_clave] = 0
                    sub_total_emp['TOTAL_BONOS']=0
                    for emp_nom in lista_empleados:
                        if 'TOTAL_BONOS' in emp_nom:
                            sub_total_emp['TOTAL_BONOS'] +=emp_nom['TOTAL_BONOS']
                        else:
                            sub_total_emp[sum_clave] += 0

                        if sum_clave in emp_nom:
                            sub_total_emp[sum_clave] += emp_nom[sum_clave]
                        else:
                            sub_total_emp[sum_clave] += 0
                listado_subtotal.append(sub_total_emp)

                # GUARDO LOS DATOS DEL DICCIONARIO EN UNA LISTA.
                dato_emp = {
                    "departamento": departamento.name,
                    "empleados": lista_empleados,
                    "sub_total_emp": listado_subtotal,
                    "total":listado_total,
                }

                if dato_emp["empleados"] != []:
                    lista_departamento.append(dato_emp)

                for rec in listado_subtotal:
                    if not rec:
                        continue
                    else:
                        l.append(rec)

                for rec in listado_clave:
                    if not rec:
                        continue
                    else:
                        l_claves.append(rec)

            #SUMATORIA FINAL
            total = {}
            l_total=[]
            for sum_clave in l_claves:
                total[sum_clave] = 0
                total['TOTAL_BONOS'] = 0
                for subt in l:
                    if sum_clave in subt:
                        total[sum_clave] += subt[sum_clave]
                    else:
                        total[sum_clave] += 0
                    if 'TOTAL_BONOS' in subt:
                        total['TOTAL_BONOS'] +=subt['TOTAL_BONOS']
                    else:
                        total['TOTAL_BONOS'] += 0                    
            l_total.append(total)

            empresa = str(self.company_id.name).upper()
            nombre_planilla = str(self.name).upper()
            moneda = str(self.company_id.currency_id.name).upper()
            cifras='( CIFRAS EXPRESADAS EN '+ moneda + ' )'

            header={'empresa':empresa,'nombre_planilla':nombre_planilla,'cifras':cifras}
            lista_header=[header]
            
            #RESUMEN
            resumen = {}
            lresumen = []

            dato= self.slip_ids.filtered( lambda ch: ch.contract_id.forma_pago not in ('transferencia','ach'))
            dato  = dato.sorted(lambda emp: emp.contract_id.employee_id.name and emp.contract_id.forma_pago)
            for line in dato:
                resumen = {
                    "nombre": line.employee_id.name,
                    "forma_pago": line.contract_id.forma_pago.upper(),
                    }
                for item in line.line_ids:
                    clave = item.code
                    if clave=='LIQRE':
                        resumen[clave] = item.amount
                lresumen.append(resumen)

            suma_cheque = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'cheque')) 
            suma_transferencia = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'transferencia')) 

            suma_ach = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'ach')) 
            suma_fondofijo = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'fondofijo')) 
            suma_cajachica = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'cajachica')) 

            datos={
                'head':lista_header,
                'page':lista_departamento,
                'footer':l_total,
                'resumen':lresumen,
                'cheque':suma_cheque,
                'transferencia':suma_transferencia,
                'ach':suma_ach,
                'fondofijo':suma_fondofijo,
                'cajachica':suma_cajachica
            }
            lista_datos=[datos]
            return lista_datos


#--------------------INICIA REPORTE DINÁMICO--------------------
        else:
            # ITERO LAS LINEAS DEL MODELO Y ASIGNO LAS VARIABLES DE ENCABEZADO AL DICCIONARIO
            lista_excluidos=[]

            if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id:
                lista_excluidos = ['Basic Salary', 'Net Salary', 'Gross','dias laborados','fecha inicio','fecha fin']
            if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id:
                lista_excluidos = ['Net Salary', 'Gross','fecha inicio','fecha fin']
            if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bono14_emp').id:
                lista_excluidos = ['Net Salary', 'Gross','dias laborados']
            else:
                lista_excluidos = ['Net Salary', 'Gross','dias laborados','fecha inicio','fecha fin']


            consulta_departamento = request.env['hr.department'].search([])
            lista_departamento = []
            l=[]
            l_claves=[]
            for departamento in consulta_departamento:
                lista_empleados = []
                nominas = self.slip_ids.filtered( lambda nom: nom.contract_id.department_id.id == departamento.id)
                nominas = nominas.sorted(lambda emp: emp.contract_id.employee_id.name)
                listado_clave = []
                listado_subtotal=[]
                listado_total=[]
                for empleado in nominas:
                    for linea in empleado.line_ids:
                        clave = linea.name
                        if clave not in (listado_clave) and clave not in lista_excluidos:
                            listado_clave.append(clave)

                for empleado in nominas:
                    d_empleados = {
                        "nombre": empleado.employee_id.name,
                    }

                    for reg in empleado: 
                        year = int(self.date_end.strftime('%Y'))-1
                        fecha_inicio=self.date_start.strftime( '01-07-'+str(year))
                        fecha_fin= self.date_end.strftime('30-06-%Y')
                        fecha=datetime.strptime(fecha_inicio, '%d-%m-%Y').date()

                        if reg.contract_id.date_start > fecha:
                            fecha_inicio = reg.contract_id.date_start.strftime('%d-%m-%Y')

                    if 'fecha inicio' not in lista_excluidos:
                        d_empleados['fecha inicio']=fecha_inicio
                    
                    if 'fecha fin' not in lista_excluidos:
                        d_empleados['fecha fin']=fecha_fin

                    if 'dias laborados' not in lista_excluidos:
                        for d_trabajados in empleado.worked_days_line_ids:
                            if d_trabajados.code=='WORK100':
                                d_empleados['dias laborados']=d_trabajados.number_of_days
                            else:
                                d_empleados['dias laborados']=0.00

                    for linea in listado_clave:
                        clave = linea
                        if clave not in lista_excluidos:
                            d_empleados[clave] = round(sum([line.amount for line in empleado.line_ids.filtered(lambda emp: emp.name == linea)]),2)

                    if 'forma pago' not in lista_excluidos:
                        for d_forma_pago in empleado:
                            d_empleados['forma pago']= d_forma_pago.employee_id.contract_id.forma_pago.upper()
                    lista_empleados.append(d_empleados)   
                    #revision           
                    empleado_titulos=lista_empleados

                sub_total_emp = {}
                for sum_clave in listado_clave:
                    sub_total_emp[sum_clave] = 0.00
                    for emp_nom in lista_empleados:
                        if sum_clave in emp_nom:
                            sub_total_emp[sum_clave] += emp_nom[sum_clave]
                        else:
                            sub_total_emp[sum_clave] += 0.00
                listado_subtotal.append(sub_total_emp)

                # GUARDO LOS DATOS DEL DICCIONARIO EN UNA LISTA.
                if len(lista_empleados)!=0:
                    dato_emp = {
                        "departamento": departamento.name,
                        "empleados": lista_empleados,
                        "sub_total_emp": listado_subtotal,
                    }
                    lista_departamento.append(dato_emp)

                for rec in listado_subtotal:
                    if not rec:
                        continue
                    else:
                        l.append(rec)

                for rec in listado_clave:
                    if not rec:
                        continue
                    else:
                        l_claves.append(rec)

            #SUMATORIA FINAL
            total = {}
            l_total=[]
            for sum_clave in l_claves:
                total[sum_clave] = 0.00
                for subt in l:
                    total[sum_clave] += subt[sum_clave]
            l_total.append(total)

            #RESUMEN
            resumen = {}
            lresumen = []

            dato= self.slip_ids.filtered( lambda ch: ch.contract_id.forma_pago not in ('transferencia','ach'))
            dato  = dato.sorted(lambda emp: emp.contract_id.employee_id.name and emp.contract_id.forma_pago)
            for line in dato:
                resumen = {
                    "nombre": line.employee_id.name,
                    "forma_pago": line.contract_id.forma_pago.upper(),
                    }
                for item in line.line_ids:
                    clave = item.code
                    if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id:
                        if clave=='LIQRE':
                            resumen[clave] = item.amount
                    if estructura == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id:
                        if clave=='LIQRE':
                            resumen[clave] = item.amount
                    else:
                        if clave=='LIQRE':
                            resumen[clave] = item.amount
                lresumen.append(resumen)
            
            suma_cheque = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'cheque')) 
            suma_transferencia = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'transferencia')) 

            suma_ach = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'ach')) 
            suma_fondofijo = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'fondofijo')) 
            suma_cajachica = sum(calculo.total for calculo in self.slip_ids.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE' and payslip.contract_id.forma_pago == 'cajachica')) 


            titulo=[]
            for dato in empleado_titulos:
                for k in dato.keys():
                    if k not in titulo:
                        titulo.append(k)

            nombre_planilla = str(self.name).upper()
            moneda = str(self.company_id.currency_id.name).upper()
            cifras='( CIFRAS EXPRESADAS EN '+ moneda + ' )'

            head=[
                {'empresa':self.company_id.company_registry,
                'nombre_planilla':nombre_planilla,
                'cifras':cifras}
            ]

            datos={
                'head':head,
                'titulo':titulo,
                'len':len(titulo),
                'page':lista_departamento,
                'total':l_total,
                'resumen':lresumen,
                'cheque':suma_cheque,
                'transferencia':suma_transferencia,
                'ach':suma_ach,
                'fondofijo':suma_fondofijo,
                'cajachica':suma_cajachica
            }
            lista_datos=[datos]

            return lista_datos









