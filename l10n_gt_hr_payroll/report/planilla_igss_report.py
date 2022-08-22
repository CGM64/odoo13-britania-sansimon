# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.http import request
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from datetime import date, datetime
import calendar
import re
import io
import base64
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.l10n_gt_sat.wizard import account_report_libros
import calendar

TIPOS_DE_LIBROS = account_report_libros.TIPOS_DE_LIBROS

class HrPlanillaIgss(models.TransientModel):
    _name = 'report.l10n_gt_hr_payroll.planilla_igss_txt'
    _description = 'Planilla Electrónica IGSS Texto'
    
    def get_patrono(self, inicio, fin):
        normalizar=lambda parametro: parametro if parametro else ''
        #tipo_planilla = data['tipo_planilla']

        lista_patrono = []

        #PATRONO
        company_id = self.env.company
        patronos = request.env['res.company'].search([('id', '=',company_id.id)])  
        # t_planilla = request.env['hr.types_payroll'].search([('id', '=',int(tipo_planilla))])[0]
        # es_prueba=1 if t_planilla.es_prueba == True else 0
        
        for patrono in patronos:
            fecha=date.today()
            ficha_patrono={
                'version':'2.1.0',                
                'fecha_generacion':fecha.strftime('%d/%m/%Y'),
                'numero_patronal':normalizar(patrono.numero_patronal),
                'mes_planilla': fecha.strftime('%m'),
                'anio_planilla':fecha.strftime('%Y'),
                'nombre_comercial':normalizar(patrono.company_registry),
                'nit':normalizar(patrono.vat),
                'email':normalizar(patrono.email),
                'es_prueba':0,
            }
            lista_patrono.append(ficha_patrono)
        return lista_patrono
    
    def get_tipo_planillas(self, inicio, fin):
        lista_tipo_planillas = []
        
        
        
        employee_tipos_planilla = self.env['hr.employee'].read_group(
            domain=[('active', '=', True),('tipo_planilla_id','!=', False)],
            fields=['tipo_planilla_id',],
            groupby=['tipo_planilla_id',],
            lazy=False,
        )
        tipos_planilla_asignados = [] #Variable que me permite almacenar solo los tipos planilla que fueron asignados a los empleados a desplegar.
        for tipo in employee_tipos_planilla:
            tipos_planilla_asignados.append(tipo['tipo_planilla_id'][0])

        
        hr_tipos_planilla = self.env['hr.tipo.planilla'].search([('active','=',True),('id','in',tipos_planilla_asignados)])
        for tipo in hr_tipos_planilla.sorted('code'):
            ficha_tipo_planilla = {
                'code' : tipo.code,
                'nombre' : tipo.name,
                'afiliado': tipo.tipo_afiliados,
                'periodo': tipo.periodo_planilla,
                'departamento': tipo.codigo_departamento,
                'actividad': tipo.code_actividad_economica.code,
                'clase': tipo.clase_planilla,
                
            }
            lista_tipo_planillas.append(ficha_tipo_planilla)
        
        return lista_tipo_planillas
    
    
    def get_liquidaciones(self, inicio, fin):
        lista_liquidaciones = []
    
        employee_tipos_planilla = self.env['hr.employee'].read_group(
            domain=[('active', '=', True),('tipo_planilla_id','!=', False)],
            fields=['tipo_planilla_id',],
            groupby=['tipo_planilla_id',],
            lazy=False,
        )
        tipos_planilla_asignados = [] #Variable que me permite almacenar solo los tipos planilla que fueron asignados a los empleados a desplegar.
        for tipo in employee_tipos_planilla:
            tipos_planilla_asignados.append(tipo['tipo_planilla_id'][0])

        
        hr_tipos_planilla = self.env['hr.tipo.planilla'].search([('active','=',True),('id','in',tipos_planilla_asignados)])
        for tipo in hr_tipos_planilla:
            ficha_tipo_planilla = {
                'numero_liquidacion' : tipo.code,
                'numero_tipo_planilla' : tipo.code,
                'fecha_inicio': inicio.strftime('%d/%m/%Y'),
                'fecha_fin': fin.strftime('%d/%m/%Y'),
                'liquidacion_complementaria': 'O',
                'nota_cargo': '',
            }
            lista_liquidaciones.append(ficha_tipo_planilla)
        
        return lista_liquidaciones
        
    #Funcion que devuelve TRUE si la fecha se encuentra en el rango de fecha enviado.
    def get_bool_rango_fecha(self, inicio, fin, fecha):
        if fecha:
            if fecha >= inicio and fecha <= fin:
                return True
        return False
        
    
    def get_empleados(self, inicio, fin):
        normalizar=lambda parametro: parametro if parametro else ''

        hr_employee = self.env['hr.employee'].search([('active','=',True)])
        empleados = []
        i=0
        
        for employee in hr_employee.sorted(lambda r: r.tipo_planilla_id.code):
            if employee.afiliacion_igss:

                i += 1

                primer_nombre = ''
                segundo_nombre = ''
                tercer_nombre = ''
                primer_apellido = ''
                segundo_apellido = apellido_casada = ''
                
                primer_nombre, segundo_nombre, tercer_nombre, primer_apellido, segundo_apellido, apellido_casada = employee.get_nombres_separados()
                hr_contract = self.env['hr.contract'].search([('employee_id','=',employee.id),('state','not in',('cancel','draft'))])

                hr_payslip = self.env['hr.payslip'].search([('employee_id', '=', employee.id), ('date_to', '=', fin)])
                
                sueldo = 0.00
                if hr_payslip:
                    for rule in hr_payslip.line_ids:
                        if rule.code == 'LIQRE':
                            sueldo += rule.total
                        if rule.code == 'ANTIQUI':
                            sueldo += rule.total
                        
                empleado = {
                    'num_liquidacion': employee.tipo_planilla_id.code,
                    'numero_afiliacion_igss': employee.afiliacion_igss,
                    'primer_nombre': primer_nombre,
                    'segundo_nombre': segundo_nombre + ' ' + tercer_nombre,
                    'primer_apellido': primer_apellido,
                    'segundo_apellido': segundo_apellido,
                    'apellido_casada': apellido_casada,
                    'sueldo': sueldo,
                    'fecha_alta': hr_contract.date_start.strftime('%d/%m/%Y') if self.get_bool_rango_fecha(inicio, fin, hr_contract.date_start) else '',
                    'fecha_baja': hr_contract.date_end.strftime('%d/%m/%Y') if self.get_bool_rango_fecha(inicio, fin, hr_contract.date_end) else '',
                    'cod_centro': employee.work_location_id.location_number if employee.work_location_id else '',
                    'nit': employee.vat or '',
                    'cod_ocupacion': employee.ocupacion_id.code or '',
                    'condicion_laboral': hr_contract.condicion_laboral,
                    'deducciones': '',
                }
                
                
                empleados.append(empleado)
        return empleados
    
    def get_empleados_suspendidos(self, inicio, fin):
        lista_empleados_suspendios = []
        
        asistencia = self.env["hr.work.entry"].search([('employee_id','=',156)])
        # for asis in asistencia:
        #     print(asis)
        
        return lista_empleados_suspendios

    def get_centros(self, inicio, fin):
        normalizar=lambda parametro: parametro if parametro else ''

        hr_employee = self.env['hr.work.location'].search([])
        
        centros = []
        i=0
        for employee in hr_employee:
                i += 1
                        
                centro = {
                    'code': employee.location_number,
                    'name': employee.name,
                    'direccion': employee.address_id.street,
                    'zona': employee.zona or '',
                    'telefono': employee.address_id.phone,
                    'fax': '',#PENDIENTE
                    'nombre_del_contacto': employee.contacto or '',
                    'correo': employee.address_id.email or '',
                    'code_departamento': employee.address_id.state_id.code_igss or '',
                    'cod_municipio':  employee.address_id.municipio_id.code_igss or '',
                    'cod_actividad_economica': employee.code_actividad_economica.code,
                }
                
                centros.append(centro)
        return centros
    
    def get_planilla_igss(self, inicio, fin):
        patronos = self.get_patrono(inicio,fin)
        tipo_planillas = self.get_tipo_planillas(inicio,fin)
        liquidaciones = self.get_liquidaciones(inicio,fin)
        empleados = self.get_empleados(inicio,fin)
        suspendidos = self.get_empleados_suspendidos(inicio,fin)
        centros = self.get_centros(inicio,fin)
        planilla_igss = {
            'patronos': patronos,
            'tipo_planillas': tipo_planillas,
            'liquidaciones': liquidaciones,
            'empleados': empleados,
            'suspendidos': suspendidos,
            'centros': centros,
        }
        return planilla_igss

    @api.model
    def _get_report_values(self,docids,data):

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        inicio = datetime.strptime(data['form']['rango_fecha_inicio'], '%Y-%m-%d').date()
        fin = datetime.strptime(data['form']['rango_fecha_fin'], '%Y-%m-%d').date()
        planilla_igss = self.get_planilla_igss(inicio,fin)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'planilla_igss': planilla_igss,
            'currency': self.env.company.currency_id,
        }

        return docargs

class HrPlanillaIgssReportXLSX(models.AbstractModel):
    _name = 'report.l10n_gt_hr_payroll.planilla_igss_xlsx'
    _description = "Planilla Electrónica IGSS XLS"
    _inherit = 'report.report_xlsx.abstract'

    # SEPARADORES EXCEL
    def separadores(self, hoja, num_col,fila):
        for i in range(0, num_col):
            if i%2:
                hoja.set_column(i, i, 1)
                hoja.write(fila, i, '|')
            else:
                hoja.set_column(i, i, 30)


    # INICIA LA GENERACION DEL REPORTE EXCEL
    def generate_xlsx_report(self, workbook, data, model):
        inicio = datetime.strptime(data['form']['rango_fecha_inicio'], '%Y-%m-%d').date()
        fin = datetime.strptime(data['form']['rango_fecha_fin'], '%Y-%m-%d').date()
        num_format = workbook.add_format({'num_format': '#,##0.00'})

        
        planilla_igss = self.env["report.l10n_gt_hr_payroll.planilla_igss_txt"].get_planilla_igss(inicio, fin)
        
        # INICIA LA GENERACION DEL REPORTE EXCEL
        # PATRONO
        patrono = workbook.add_worksheet('PATRONO')
        self.separadores(patrono,18,0)
        patrono.write(0, 0, '1. Versión del mensaje. 2.1.0')
        patrono.write(0, 2, '2. Fecha de generación del archivo de planilla, con formato dd/mm/yyyy')
        patrono.write(0, 4, '3. Numero patronal')
        patrono.write(0, 6, '4. Mes de la planilla de IGSS ')
        patrono.write(0, 8, '5. Año de la planilla de IGSS')
        patrono.write(0, 10, '6. Nombre Comercial')
        patrono.write(0, 12, '7. Nit del patrono (SIN GUION)')
        patrono.write(0, 14, '8. Correo Electrónico del Patrono')
        patrono.write(0, 16, '9. “0” (cero) si la planilla es de producción  y “1” (uno) si la planilla es de pruebas')
        i = 0
        for p in planilla_igss['patronos']:
            i += 1
            self.separadores(patrono,18,i)
            patrono.write(i, 0, p['version'])
            patrono.write(i, 2, p['fecha_generacion'])
            patrono.write(i, 4, p['numero_patronal'])
            patrono.write(i, 6, p['mes_planilla'])
            patrono.write(i, 8, p['anio_planilla'])
            patrono.write(i, 10, p['nombre_comercial'])
            patrono.write(i, 12, p['nit'])
            patrono.write(i, 14, p['email'])
            patrono.write(i, 16, p['es_prueba'])
            
        # CENTROS DE TRABAJO
        centro = workbook.add_worksheet('CENTROS')
        self.separadores(centro,22,0)
        centro.write(0, 0, '1. Código del centro de trabajo.')
        centro.write(0, 2, '2. Nombre o descripción del centro de trabajo.')
        centro.write(0, 4, '3. Dirección del centro de trabajo.')
        centro.write(0, 6, '4. Zona donde se ubica el centro de trabajo, si aplicara.')
        centro.write(0, 8, '5. Teléfonos, separados por guiones o diagonales')
        centro.write(0, 10, '6. Fax.')
        centro.write(0, 12, '7. Nombre del contacto en ese centro de trabajo.')
        centro.write(0, 14, '8. Correo electrónico.')
        centro.write(0, 16, '9. Departamento de la República donde se ubica.')
        centro.write(0, 18, '10. Municipio de la República.')
        centro.write(0, 20, '11. Código de actividad económica.')
        i = 0
        for p in planilla_igss['centros']:
            i += 1
            self.separadores(centro,22,i)
            centro.set_column(0, 0, 10)
            centro.set_column(2, 2, 40)
            centro.set_column(4, 4, 40)
            centro.set_column(6, 6, 8)
            centro.set_column(8, 8, 8)
            centro.set_column(10, 10, 8)
            centro.set_column(12, 12, 10)
            centro.set_column(14, 14, 10)
            centro.set_column(16, 16, 11)
            centro.set_column(18, 18, 11)
            centro.set_column(20, 20, 8)
            
            centro.write(i, 0, p['code'])
            centro.write(i, 2, p['name'])
            centro.write(i, 4, p['direccion'])
            centro.write(i, 6, p['zona'])
            centro.write(i, 8, p['telefono'])
            centro.write(i, 10, p['fax'])
            centro.write(i, 12, p['nombre_del_contacto'])
            centro.write(i, 14, p['correo'])
            centro.write(i, 16, p['code_departamento'])
            centro.write(i, 18, p['cod_municipio'])
            centro.write(i, 20, p['cod_actividad_economica'])
                    
        #TIPOS DE PLANILLA
        tipos_planilla = workbook.add_worksheet('TIPOS DE PLANILLA')
        self.separadores(tipos_planilla,14,0)
        tipos_planilla.write(0, 0, '1. Identificación de Tipo de planilla')
        tipos_planilla.write(0, 2, '2. Nombre o descripción del tipo de planilla')
        tipos_planilla.write(0, 4, '3. Tipo de afiliados, (S)Trabajador Sin IVS         (C) Trabajador Con IVS')
        tipos_planilla.write(0, 6, '4. Periodo de planilla, (M)Mensual (C)Catorcenal (S)Semanal.')
        tipos_planilla.write(0, 8, '5. Departamento de la República donde laboran los empleados')
        tipos_planilla.write(0, 10, '6. Actividad económica')
        tipos_planilla.write(0, 12, '7. Clase de Planilla,        (N) Normal,   (V) Sin movimiento')
        i = 0
        for p in planilla_igss['tipo_planillas']:
            i += 1
            self.separadores(tipos_planilla,14,i)
            
            tipos_planilla.write(i, 0, p['code'])
            tipos_planilla.write(i, 2, p['nombre'])
            tipos_planilla.write(i, 4, p['afiliado'])
            tipos_planilla.write(i, 6, p['periodo'])
            tipos_planilla.write(i, 8, int(p['departamento']))
            tipos_planilla.write(i, 10, int(p['actividad']))
            tipos_planilla.write(i, 12, p['clase'])
                    
        #LIQUIDACIONES
        liquidaciones = workbook.add_worksheet('LIQUIDACIONES')
        self.separadores(liquidaciones,12,0)
        liquidaciones.write(0, 0, '1. Número de liquidación')
        liquidaciones.write(0, 2, '2. Tipo de planilla que define a esta liquidación.')
        liquidaciones.write(0, 4, '3. Fecha inicial de la liquidación.       dd/mm/yyyy')
        liquidaciones.write(0, 6, '4. Fecha final de la liquidación.       dd/mm/yyyy')
        liquidaciones.write(0, 8, '5. Si es una liquidación complementaria (C) o una que no ha sido presentada y pagada o sea original (O).')
        liquidaciones.write(0, 10, '6. Número Nota de Cargo.')

        i = 0
        for p in planilla_igss['liquidaciones']:
            i += 1
            self.separadores(liquidaciones,12,i)
            liquidaciones.write(i, 0, p['numero_liquidacion'])
            liquidaciones.write(i, 2, p['numero_tipo_planilla'])
            liquidaciones.write(i, 4, p['fecha_inicio'])
            liquidaciones.write(i, 6, p['fecha_fin'])
            liquidaciones.write(i, 8, p['liquidacion_complementaria'])
            liquidaciones.write(i, 10, p['nota_cargo'])

        # EMPLEADOS
        empleado = workbook.add_worksheet('EMPLEADOS')
        self.separadores(empleado,30,0)
        empleado.write(0, 0, '1. Número o identificación de la liquidación.')
        empleado.write(0, 2, '2. Numero de Afiliado')
        empleado.write(0, 4, '3. Primer Nombre de afiliado')
        empleado.write(0, 6, '4. Segundo Nombre de afiliado')
        empleado.write(0, 8, '5. Primer Apellido de Afiliado')
        empleado.write(0, 10, '6. Segundo Apellido de Afiliado')
        empleado.write(0, 12, '7. Apellido de Casada')
        empleado.write(0, 14, '8. Sueldo devengado en el periodo')
        empleado.write(0, 16, '9. Fecha de alta')
        empleado.write(0, 18, '10. Fecha de baja')
        empleado.write(0, 20, '11. Código de Centro de trabajo asignado')
        empleado.write(0, 22, '12. Nit')
        empleado.write(0, 24, '13. Código Ocupación')
        empleado.write(0, 26, '14. Condición Laboral (P = Permanente   T = Temporal)')
        empleado.write(0, 28, '15. Deducciones')
        i = 0
        for p in planilla_igss['empleados']:
            i += 1
            self.separadores(empleado,30,i)
            empleado.write(i, 0, p['num_liquidacion'])
            empleado.write(i, 2, p['numero_afiliacion_igss'])
            empleado.write(i, 4, p['primer_nombre'])
            empleado.write(i, 6, p['segundo_nombre'])
            empleado.write(i, 8, p['primer_apellido'])
            empleado.write(i, 10, p['segundo_apellido'])
            empleado.write(i, 12, p['apellido_casada'])
            empleado.write(i, 14, p['sueldo'],num_format)
            empleado.write(i, 16, p['fecha_alta'])
            empleado.write(i, 18, p['fecha_baja'])
            empleado.write(i, 20, p['cod_centro'])
            empleado.write(i, 22, p['nit'])
            empleado.write(i, 24, p['cod_ocupacion'])
            empleado.write(i, 26, p['condicion_laboral'])
            empleado.write(i, 28, p['deducciones'])
        
        # SUSPENDIDOS
        suspendidos = workbook.add_worksheet('SUSPENDIDOS')
        self.separadores(suspendidos,16,0)
        suspendidos.write(0, 0, '1. Número o identificación de la liquidación.')
        suspendidos.write(0, 2, '2. Numero de Afiliado.')
        suspendidos.write(0, 4, '3. Primer Nombre de afiliado')
        suspendidos.write(0, 6, '4. Segundo Nombre de afiliado')
        suspendidos.write(0, 8, '5. Primer Apellido de Afiliado')
        suspendidos.write(0, 10, '6. Segundo Apellido de Afiliado')
        suspendidos.write(0, 11, '7. Apellido de Casada')
        suspendidos.write(0, 12, '8. Fecha de inicio suspensión (DD/MM/YYYY)')
        suspendidos.write(0, 14, '9. Fecha final suspensión (DD/MM/YYYY)')

        # LICENCIAS
        licencias = workbook.add_worksheet('LICENCIAS')
        self.separadores(licencias,16,0)
        licencias.write(0, 0, '1. Número o identificación de la liquidación.')
        licencias.write(0, 2, '2. Numero de Afiliado.')
        licencias.write(0, 4, '3. Primer Nombre de afiliado')
        licencias.write(0, 6, '4. Segundo Nombre de afiliado')
        licencias.write(0, 8, '5. Primer Apellido de Afiliado')
        licencias.write(0, 10, '6. Segundo Apellido de Afiliado')
        licencias.write(0, 11, '7. Apellido de Casada')
        licencias.write(0, 12, '8. Fecha de inicio licencia (DD/MM/YYYY)')
        licencias.write(0, 14, '9. Fecha final licencia (DD/MM/YYYY)')
