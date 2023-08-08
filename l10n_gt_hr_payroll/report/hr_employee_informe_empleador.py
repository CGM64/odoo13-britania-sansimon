# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from datetime import datetime
import io
import time
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class LibroFiscalReportXls(models.AbstractModel):
    _name = 'report.l10n_gt_hr_payroll.hr_informe_empleador'
    _description = 'Informe del Empleador y Nomina 29-89 Y Zonas Francas'
    _inherit = 'report.report_xlsx.abstract'
     
    def get_empleados(self, periodo):
        tiempo = datetime.strptime(periodo + '-01-01', '%Y-%m-%d').date()
        hoy = fields.Date.today()
        hr_employee = self.env['hr.employee'].search([('active','=',True), ('contract_id','!=',False)])
        hr_employee = hr_employee.sorted(lambda m: (m.contract_id.date_start))
        hr_employee = hr_employee.filtered(lambda emp: (emp.contract_id.date_end if emp.contract_id.date_end else hoy) >= tiempo)
        #hr_employee = hr_employee.filtered(lambda emp: emp.contract_id.date_end < tiempo)
        empleados = []
        i=0
        for employee in hr_employee:
            i += 1

            primer_nombre = ''
            segundo_nombre = ''
            tercer_nombre = ''
            primer_apellido = ''
            segundo_apellido = apellido_casada = ''
            
            primer_nombre, segundo_nombre, tercer_nombre, primer_apellido, segundo_apellido, apellido_casada = employee.get_nombres_separados()
                     
            empleado = {
                'num_empleado': i,
                'empleado': employee,
                'primer_nombre': primer_nombre,
                'segundo_nombre': segundo_nombre,
                'tercer_nombre': tercer_nombre,
                'primer_apellido': primer_apellido,
                'segundo_apellido': segundo_apellido,
                'apellido_casada': apellido_casada,
                'nacionalidad': employee.country_id.codigo_nacionalidad or '',
                'tipo_discapacidad': employee.discapacidad_id.code,
                'estado_civil': employee.get_estado_civil(),
                'documento_identificacion': employee.documento_identificacion_id.code or '',
                'numero_documento': employee.cui or '',
                'pais_origen': employee.country_id.codigo_nacionalidad or '',
                'numero_expediente_extranjero': employee.numero_expediente_extranjero or '',
                'lugar_nacimiento_municipio': employee.municipio_id.code or '',
                'numero_tributario': employee.vat or '',
                'numero_afiliacion_igss': employee.afiliacion_igss,
                'sexo': employee.get_genero(),
                'fecha_nacimiento': employee.birthday or '',
                'nivel_educativo': employee.nivel_educativo_id.code,
                'titulo_diploma': (employee.nivel_academico_id.name or '').upper(),
                'pueblo_pertenencia': employee.pueblo_pertenencia_id.code,
                'comunidad_liguistica': employee.comunidad_linguistica_id.code,
                'cantidad_hijos': employee.children,
                'temporalidad_contrato': employee.contract_id.temporalidad_contrato or '',
                'tipo_contrato': employee.contract_id.tipo_contrato or '',
                'fecha_inicio_labores': employee.contract_id.date_start or '',
                'fecha_reinicio_labores': employee.contract_id.fecha_reinicio_labores or '',
                'fecha_finalizo_labores': employee.contract_id.date_end or '',
                'ocupacion': employee.ocupacion_id.code,
                'jornada_trabajo': employee.contract_id.jornada_trabajo or '',
                'dias_laborados_anio': 0,
                'salario_mensual': employee.contract_id.wage,
                'salario_anual': 0,
                'bono_decreto_7889': employee.contract_id.bono_decreto,
                'horas_extras_anuales': 0,
                'valor_hora_extra': 0,
                'monto_aguinaldo': employee.contract_id.wage,
                'monto_bono14': employee.contract_id.wage,
                'retribucion_comisiones': 0,
                'viaticos': 0,
                'bonificaciones_adicionales': 0,
                'retribucion_vacaciones': 0,
                'retribución_indemnizacion': 0,
                'sucursal': 0,
            }
            #print(time.strftime(periodo + '-01-01'))
            nominas = self.env['hr.payslip'].search([
                    ('contract_id','=',employee.contract_id.id),
                    ('state','in',('done','paid')),
                    ('date_from','>=',time.strftime(periodo + '-01-01')),
                    ('date_to','<=',time.strftime(periodo + '-12-31')),
                ])
            dias_laborados_anio = salario_anual = 0
            for nomina in nominas:
                if nomina.struct_id.id in (self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id,self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id):
                    dias_laborados_anio += sum(line.number_of_days for line in nomina.worked_days_line_ids.filtered(lambda tipo_entrada: tipo_entrada.work_entry_type_id.es_informe_empleador))
                    if nomina.struct_id.id == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id:
                        salario_anual += sum(line.amount for line in nomina.line_ids.filtered(lambda tipo_entrada: tipo_entrada.salary_rule_id.code == 'HRSUD'))
            #empleado['dias_laborados_anio'] = dias_laborados_anio
            empleado['salario_anual'] = salario_anual
            
            empleados.append(empleado)
        return empleados

    def generate_xlsx_report(self, workbook, data, data_report):
        bold = workbook.add_format({'bold': True})
        text_format = workbook.add_format({'text_wrap': True, 'bold': True})
        sheet_libro = workbook.add_worksheet('Informe')

        text_right = workbook.add_format()
        text_right.set_align('right')
        
        text_left = workbook.add_format()
        text_left.set_align('left')
        
        text_date = workbook.add_format()
        text_date.set_num_format('dd/mm/yyyy')

        periodo = data['form']['periodos']
        empleados = self.get_empleados(periodo)
        
        i=0
        sheet_libro.set_column(0,6,18)
        sheet_libro.set_column(7,7,9)
        sheet_libro.set_column(8,8,18)
        sheet_libro.set_column(9,9,10)
        sheet_libro.set_column(10,16,15)
        sheet_libro.set_column(18,44,15)
        sheet_libro.set_column(20,20,70)

        
        sheet_libro.write(i, 0, 'Número de empleado', bold)
        sheet_libro.write(i, 1, 'Primer nombre', bold)
        sheet_libro.write(i, 2, 'Segundo nombre', bold)
        sheet_libro.write(i, 3, 'Tercer nombre', bold)
        sheet_libro.write(i, 4, 'Primer apellido', bold)
        sheet_libro.write(i, 5, 'Segundo apellido', bold)
        sheet_libro.write(i, 6, 'Apellido de casada', bold)
        sheet_libro.write(i, 7, 'Nacionalidad', bold)
        sheet_libro.write(i, 8, 'Tipo de discapacidad', bold)
        sheet_libro.write(i, 9, 'Estado civil', bold)
        sheet_libro.write(i, 10, 'Documento identificación (DPI, Pasaporte u otro)', text_format)
        sheet_libro.write(i, 11, 'Número de documento', text_format)
        sheet_libro.write(i, 12, 'País de origen', text_format)
        sheet_libro.write(i, 13, 'Número de expediente del permiso de extranjero', text_format)
        sheet_libro.write(i, 14, 'Lugar de nacimiento (municipio)', text_format)
        sheet_libro.write(i, 15, 'Número de Identificación Tributaria (NIT)', text_format)
        sheet_libro.write(i, 16, 'Número de afiliación IGSS', text_format)
        sheet_libro.write(i, 17, 'Sexo', text_format)
        sheet_libro.write(i, 18, 'Fecha de nacimiento', text_format)
        sheet_libro.write(i, 19, 'Nivel académico más alto alcanzado', text_format)
        sheet_libro.write(i, 20, 'Titulo o diploma (profesión)', text_format)
        sheet_libro.write(i, 21, 'Pueblo de pertenencia', text_format)
        sheet_libro.write(i, 22, 'Comunidad Lingüística', text_format)
        sheet_libro.write(i, 23, 'Cantidad de hijos', text_format)
        sheet_libro.write(i, 24, 'Temporalidad del contrato', text_format)
        sheet_libro.write(i, 25, 'Tipo de contrato', text_format)
        sheet_libro.write(i, 26, 'Fecha de inicio de labores', text_format)
        sheet_libro.write(i, 27, 'Fecha de reinicio de labores', text_format)
        sheet_libro.write(i, 28, 'Fecha de finalización de labores', text_format)
        sheet_libro.write(i, 29, 'Ocupación (puesto)', text_format)
        sheet_libro.write(i, 30, 'Jornada de trabajo', text_format)
        sheet_libro.write(i, 31, 'Días laborados en el año', text_format)
        sheet_libro.write(i, 32, 'Salario mensual nominal', text_format)
        sheet_libro.write(i, 33, 'Salario anual nominal', text_format)
        sheet_libro.write(i, 34, 'Bonificación Decreto 78-89 (Q.250.00)', text_format)
        sheet_libro.write(i, 35, 'Total horas extras anuales', text_format)
        sheet_libro.write(i, 36, 'Valor de la hora extra', text_format)
        sheet_libro.write(i, 37, 'Monto Aguinaldo Decreto 76-78', text_format)
        sheet_libro.write(i, 38, 'Monto Bono 14  Decreto 42-92', text_format)
        sheet_libro.write(i, 39, 'Retribución por comisiones', text_format)
        sheet_libro.write(i, 40, 'Viáticos', text_format)
        sheet_libro.write(i, 41, 'Bonificaciones adicionales', text_format)
        sheet_libro.write(i, 42, 'Retribución por vacaciones', text_format)
        sheet_libro.write(i, 43, 'Retribución por indemnización (Artículo 82 Código de Trabajo)', text_format)
        sheet_libro.write(i, 44, 'Sucursal', text_format)
        
        for empleado in empleados:
            i+=1
            sheet_libro.write(i, 0, empleado['num_empleado'])
            sheet_libro.write(i, 1, empleado['primer_nombre'])
            sheet_libro.write(i, 2, empleado['segundo_nombre'])
            sheet_libro.write(i, 3, empleado['tercer_nombre'])
            sheet_libro.write(i, 4, empleado['primer_apellido'])
            sheet_libro.write(i, 5, empleado['segundo_apellido'])
            sheet_libro.write(i, 6, empleado['apellido_casada'])
            sheet_libro.write(i, 7, empleado['nacionalidad'])
            sheet_libro.write(i, 8, empleado['tipo_discapacidad'])
            sheet_libro.write(i, 9, empleado['estado_civil'])
            sheet_libro.write(i, 10, empleado['documento_identificacion'])
            sheet_libro.write(i, 11, empleado['numero_documento'])
            sheet_libro.write(i, 12, empleado['pais_origen'])
            sheet_libro.write(i, 13, empleado['numero_expediente_extranjero'])
            sheet_libro.write(i, 14, empleado['lugar_nacimiento_municipio'])
            sheet_libro.write(i, 15, empleado['numero_tributario'],text_right)
            sheet_libro.write(i, 16, empleado['numero_afiliacion_igss'],text_right)
            sheet_libro.write(i, 17, empleado['sexo'])
            sheet_libro.write(i, 18, empleado['fecha_nacimiento'],text_date)
            sheet_libro.write(i, 19, empleado['nivel_educativo'],text_right)
            sheet_libro.write(i, 20, empleado['titulo_diploma'],text_left)
            sheet_libro.write(i, 21, empleado['pueblo_pertenencia'],text_right)
            sheet_libro.write(i, 22, empleado['comunidad_liguistica'],text_right)
            sheet_libro.write(i, 23, empleado['cantidad_hijos'])
            sheet_libro.write(i, 24, empleado['temporalidad_contrato'],text_right)
            sheet_libro.write(i, 25, empleado['tipo_contrato'],text_right)
            sheet_libro.write(i, 26, empleado['fecha_inicio_labores'],text_date)
            sheet_libro.write(i, 27, empleado['fecha_reinicio_labores'],text_date)
            sheet_libro.write(i, 28, empleado['fecha_finalizo_labores'],text_date)
            sheet_libro.write(i, 29, empleado['ocupacion'],text_right)
            sheet_libro.write(i, 30, empleado['jornada_trabajo'],text_right)
            sheet_libro.write(i, 31, empleado['dias_laborados_anio'],text_right)
            sheet_libro.write(i, 32, empleado['salario_mensual'])
            sheet_libro.write(i, 33, empleado['salario_anual'])
            sheet_libro.write(i, 34, empleado['bono_decreto_7889'])
            sheet_libro.write(i, 35, empleado['horas_extras_anuales'])
            sheet_libro.write(i, 36, empleado['valor_hora_extra'])
            sheet_libro.write(i, 37, empleado['monto_aguinaldo'])
            sheet_libro.write(i, 38, empleado['monto_bono14'])
            sheet_libro.write(i, 39, empleado['retribucion_comisiones'])
            sheet_libro.write(i, 40, empleado['viaticos'])
            sheet_libro.write(i, 41, empleado['bonificaciones_adicionales'])
            sheet_libro.write(i, 42, empleado['retribucion_vacaciones'])
            sheet_libro.write(i, 43, empleado['retribución_indemnizacion'])
            sheet_libro.write(i, 44, empleado['sucursal'])


