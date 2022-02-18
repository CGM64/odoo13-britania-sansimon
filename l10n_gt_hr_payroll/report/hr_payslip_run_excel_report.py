import abc
import re
from typing import List
from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime, date
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class HrPayslipRunInherit(models.Model):
    _inherit = "hr.payslip.run"
    _description = "Exportar Planilla"

    def export_planilla_xls(self):
        return self.env.ref('l10n_gt_hr_payroll.export_planilla_xls').report_action(self)

    def constructor_planillas_pdf(self):
        data=self.env['report.l10n_gt_hr_payroll.report_planilla_excel'].constructor_planilla_dinamica(self)
        return data


class HrPayslipRunXlsxExport(models.AbstractModel):
    _name = 'report.l10n_gt_hr_payroll.report_planilla_excel'
    _description = "Exportacion de planilla"
    _inherit = 'report.report_xlsx.abstract'

    def _get_dis_laborados(self, payslip):
        fecha_inicio = payslip.date_from.replace(
            month=payslip.date_from.month, day=1, year=payslip.date_from.year)
        fecha_fin = payslip.date_to
        empleado_nomina_anticpo = payslip.env['hr.payslip'].search([
            ('struct_id', 'in', (payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id,
                                 payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id)),
            ('state', 'in', ('done', 'verify')),
            ('contract_id', '=', payslip.contract_id.id),
            ('date_from', '>=', fecha_inicio),
            ('date_to', '<=', fecha_fin)
        ])
        return sum(calculo.number_of_days for calculo in empleado_nomina_anticpo.worked_days_line_ids.filtered(lambda payslip: payslip.code == 'WORK100'))

    def _get_nominas_bonos(self, payslip):
        fecha_inicio = payslip.date_from.replace(
            month=payslip.date_from.month, day=1, year=payslip.date_from.year)
        fecha_fin = payslip.date_to
        empleado_nomina_bono = payslip.env['hr.payslip'].search([
            # ('struct_id','in',(payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id,)),
            ('struct_id', 'in', (payslip.env.ref(
                'l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id,)),
            ('state', 'in', ('done', 'verify')),
            ('contract_id', '=', payslip.contract_id.id),
            ('date_from', '>=', fecha_inicio),
            ('date_to', '<=', fecha_fin)
        ])
        return sum(calculo.total for calculo in empleado_nomina_bono.line_ids.filtered(lambda payslip: payslip.code in ('LIQRE',)))

    #LA PLANILLA CON ESTRUCTURA DE FIN DE MES SE ARMA A PARTIR DE LOS ENCABEZADOS ACÁ DEFINIDOS
    def get_codigos_encabezados_estatica(self):
        encabezados = [{'NO':'NO'},{'EMPLEADO':'EMPLEADO'},{'FECHAINGRESO':'FECHA DE INGRESO'},{'DIASLAB':'DIAS LAB.'},{'BASIC':'SUELDO BASE'},{'SEPTM':'SEPTIMO'},{'HRSUD':'SUELDO DEL MES'},
                        {'BONOESPE':'BONO ESPECIAL'},{'HRBDC':'BONIFICACION DECRETO'},{'BONOPRO':'BONO PRODUCCIÓN'},{'BONOLOGI':'BONO LOGISTICA'},{'COMISION':'COMISION'},
                        {'HRTIG':'TOTAL INGRESOS'},{'HRCLI':'IGSS'},{'ISR':'ISR'},{'BTRAB':'BANTRAB'},{'JURID':'JURIDICO'},{'DESANTI':'ANTICIPOS'},{'DESFAC':'FACTURA'},
                        {'DESOTROS':'OTROS'},{'COMISION':'COMISION'},{'ANTIQUI':'1ERA QUINCENA'},{'TDESC':'TOTAL DESCUENTOS'},{'LIQRE':'LIQUIDO A RECIBIR'},{'TOTALBONOS':'TOTAL DE BONOS'},
                        {'OBSERVACIONES':'OBSERVACIONES'},{'FORMAPAGO':'FORMA DE PAGO'}]
        return encabezados
    
    #LAS PLANILLAS QUE NO SEAN ESTRUCTURA DE FIN DE MES SE ARMAN A PARTIR DEL DETALLE DE LAS NOMINAS
    def get_codigos_encabezados_dinamica(self,model):
        codigos = [{'NO':'NO'},{'EMPLEADO':'EMPLEADO'},]
        estructura_id=model.slip_ids.struct_id.id
        #DEBO COMPARAR EL ID DE LA ESTRUCTURA EN DADO CASO NECESITE AGREGAR COLUMNAS PARA ESA ESTRUCTURA.
        if estructura_id == model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bono14_emp').id:
            codigos.append({'INICIOCALCULO':'FECHA INICO DEL CALCULO'})
            codigos.append({'FINALIZACALCULO':'FECHA FINAL DEL CALCULO'})
        lista_exclusion=self.lista_exclusion(model)
        for line in model.slip_ids.line_ids:
            if {line.code:line.name} not in codigos and {line.code:line.name} not in lista_exclusion:
                codigos.append({line.code:line.name})
                if line.code == 'HRTIG':
                    codigos.append({'HRCLI':'Cuota Laboral IGSS'})
        codigos.append({'FORMAPAGO':'FORMA DE PAGO'})
        return codigos

    #EN ESTA LISTA SE AGREGAN LAS COLUMNAS QUE NO QUEREMOS QUE SE MUESTREN EN LA PLANILLA
    def lista_exclusion(self,model):
        estructura_id=model.slip_ids.struct_id.id
        lista_exclusion=[{'NET':'Net Salary'},{'GROSS':'Gross'}]
        return lista_exclusion
    
    def get_abc(self):
        abc = {1: 'A',2: 'B',3: 'C',4: 'D', 5: 'E',6: 'F',7: 'G',8: 'H', 9: 'I',10: 'J',11: 'K',12: 'L',13: 'M',14: 'N',
        15: 'O',16: 'P',17: 'Q',18: 'R',19: 'S',20: 'T', 21: 'U',22: 'V',23: 'W',24: 'X',25: 'Y',26: 'Z',27:'AA',28:'AB',29:'AC',}
        return abc
        

    def meses(self):
        meses={1:'ENERO',
                2:'FEBRERO',
                3:'MARZO ',
                4:'ABRIL',
                5:'MAYO',
                6:'JUNIO',
                7:'JULIO',
                8:'AGOSTO',
                9:'SEPTIEMBRE',
                10:'OCTUBRE',
                11:'NOVIEMBRE',
                12:'DICIEMBRE'
                }
        return meses

    def get_empresa_titulo(self,model):
        fecha=model.date_end
        estructura_id=model.slip_ids.struct_id.id
        empresa,titulo=model.company_id.company_registry,model.name #='BONO 14 DEL 01 DE JULIO DEL '+str(year)+' AL 30 DE JUNIO DEL '+str(year_now)

        if estructura_id == model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bono14_emp').id:
            titulo='BONO 14 DEL 01 DE JULIO DEL %s AL 30 DE JUNIO DEL %s'%(fecha.year-1,fecha.year)
        elif estructura_id==model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id:
            empresa=model.company_id.name
        else:
           titulo=model.name
        return empresa,titulo

    def constructor_planilla_dinamica(self,model):
        departamentos = self.env['hr.department'].search([])
        estructura_id=model.slip_ids.struct_id.id
        estructura_finmes= model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id
        codigos_encabezados=self.get_codigos_encabezados_dinamica(model) if estructura_id != estructura_finmes else self.get_codigos_encabezados_estatica()
        empresa,titulo=self.get_empresa_titulo(model)
        d_nominas = {
            'empresa': empresa.upper(),
            'titulo': titulo.upper(),
            'moneda': model.company_id.currency_id.name,
            'encabezados': [] if estructura_id != estructura_finmes else self.get_codigos_encabezados_estatica(),
            'departamentos': [],
            'totales': [],
            'resumen':{'formapago':[],'totales':{},},
        }
        #DEPARTAMENTOS
        correlativo = 0
        total_bonos_general=0
        formas_pago=['cheque']
        no_sumar=['NO','EMPLEADO','FECHAINGRESO','DIASLAB','FORMAPAGO','INICIOCALCULO','FINALIZACALCULO','OBSERVACIONES']
        excluir=[{'BASIC':'Basic Salary'}]
        for departamento in departamentos:
            d_departamento = {'departamento': str(departamento.name).upper() ,'detalle': [], 'totales': []}
            nominas = model.slip_ids.filtered(lambda f: f.contract_id.department_id.id == departamento.id)
            #EMPLEADOS
            total_bonos_depto=0
            for nomina in nominas.sorted(lambda s: s.employee_id.name):
                correlativo += 1
                total_bonos_depto+=self._get_nominas_bonos(nomina)
                d_empleado = {'empleado': [],}

                for codigo in codigos_encabezados:
                    for k,v in codigo.items():
                        if {k:v} not in d_nominas['encabezados'] and estructura_id != estructura_finmes and {k:v} not in excluir:
                            d_nominas['encabezados'].append({k:v})

                        line = nomina.line_ids.filtered(lambda f: f.code == k)
                        if k == 'NO':
                            d_empleado['empleado'].append({k:correlativo})
                        elif k == 'EMPLEADO':
                            d_empleado['empleado'].append({k:nomina.employee_id.name})
                        elif k == 'FECHAINGRESO':
                            d_empleado['empleado'].append({k:nomina.contract_id.date_start.strftime('%d/%m/%Y')})
                        elif k == 'DIASLAB':
                            d_empleado['empleado'].append({k:self._get_dis_laborados(nomina)})
                        elif k == 'FORMAPAGO':
                            d_empleado['empleado'].append({k:str(nomina.contract_id.forma_pago).upper()})      
                        elif k == 'TOTALBONOS':
                            total_de_bonos=self._get_nominas_bonos(nomina)
                            d_empleado['empleado'].append({k: total_de_bonos if total_de_bonos > 0 else 0.00})  
                        elif k == 'OBSERVACIONES':
                             d_empleado['empleado'].append({k:''})  
                        elif k=='INICIOCALCULO':
                            inicio=nomina.contract_id.date_start
                            if inicio < nomina.date_from:
                               inicio=nomina.date_from
                            d_empleado['empleado'].append({k: inicio})  
                        elif k=='FINALIZACALCULO':
                            d_empleado['empleado'].append({k: nomina.date_to})  
                        else:
                            if {k:v} not in excluir:
                                d_empleado['empleado'].append({k:line.total if line else 0.00})
                d_departamento['detalle'].append(d_empleado)
            total_bonos_general+=total_bonos_depto
            #SUMATORIAS POR DEPARTAMENTO
            for codigo in codigos_encabezados:
                for k,v in codigo.items():
                    suma_codigo = sum([line.total for line in nominas.line_ids.filtered(lambda f: f.code == k and f.contract_id.department_id.id==departamento.id)])
                    if k not in no_sumar:
                        if k =='TOTALBONOS':
                            d_departamento['totales'].append({k:total_bonos_depto})
                        else:
                            if {k:v} not in excluir:
                                d_departamento['totales'].append({k:suma_codigo})
                    else:
                        d_departamento['totales'].append({k:''})
            if d_departamento['detalle'] !=[]:
                d_nominas['departamentos'].append(d_departamento)
        #SUMATORIAS GENERALES
        nominas = model.slip_ids
        for codigo in codigos_encabezados:
            for k,v in codigo.items():
                suma_codigo = sum([line.total for line in nominas.line_ids.filtered(lambda f: f.code == k)])
                if k not in no_sumar:
                    if k =='TOTALBONOS':
                        d_nominas['totales'].append({k:total_bonos_general})
                    else:
                        if {k:v} not in excluir:
                            d_nominas['totales'].append({k:suma_codigo})
                else:
                    d_nominas['totales'].append({k:''})
        #RESUMEN
        formas_pago=['transferencia','ach','cheque','fondofijo','cajachica']
        formas_pago_incluir=['cheque','fondofijo','cajachica']


        correlativo=0
        for forma in sorted(formas_pago):
            total_forma=0
            nomina=nominas.line_ids.filtered(lambda f: f.code == 'LIQRE' and f.contract_id.forma_pago==forma)
            for line in nomina.sorted(lambda s: s.employee_id.name):
                total_forma+=line.total
                formapago=str(line.slip_id.contract_id.forma_pago).upper()
                if forma in formas_pago_incluir:
                    correlativo+=1
                    d_nominas['resumen']['formapago'].append({'correlativo':correlativo,'empleado':line.employee_id.name,'total':line.total,'forma_pago':formapago})#'forma_pago':formapago})
                d_nominas['resumen']['totales'][formapago]=total_forma
        # print(d_nominas)
        return d_nominas

    def generar_excel_dinamico(self, workbook, model):
        nombre_archivo = str(model.id)+' '+model.name
        sheet = workbook.add_worksheet(nombre_archivo)
        estructura_id=model.slip_ids.struct_id.id
        estructura_finmes= model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id
        estructura_quincena=model.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id
        #FORMATOS DE CELDA
        formato_titulo = workbook.add_format({'bold': 1,'border': 1,'align':'center',
                                            'valign':'vcenter','fg_color': '#1C1C1C', 'font_color': 'white'})
        formato_grupo = workbook.add_format({'fg_color': 'white','bold': True, })
        formato_celda = workbook.add_format({'fg_color': 'white','border': 1, })
        formato_fecha = workbook.add_format({'num_format': 'dd/mm/yyyy', 'fg_color': 'white', 'border': 1})
        formato_sumatoria = workbook.add_format({'bold': True, 'num_format': '#,##0.00'})
        formato_header = workbook.add_format({'bold': 1,'border': 0,'align': 'center',
                                            'valign':'vcenter','fg_color': 'white', 'font_color': 'black'})
        formato_numero = workbook.add_format({'num_format': '#,##0.00', 'fg_color': 'white', 'border': 1})
        formato_gran_total = workbook.add_format({'num_format': '#,##0.00', 'fg_color': '#1C1C1C', 'bold': True,'font_color': 'white'})
        
        #INICIA LA CONSTRUCCION DE LOS TITULOS DE ACUERDO A LA ESTRUCTURA
        d_nominas = self.constructor_planilla_dinamica(model)
        abc = self.get_abc()
        columna = 0
        fila=4
        descuentos=['HRCLI','ISR','BTRAB','JURID','DESANTI','ANTI','DESFAC','DESOTROS','COMISION','ANTIQUI']
        encabezado_dinamico=[]     
        for encabezado in d_nominas['encabezados']:
            columna += 1
            for k, v in encabezado.items():
                if k not in descuentos and estructura_id in(estructura_quincena,estructura_finmes):
                    range=abc[columna]+'5:'+abc[columna]+'6'
                    sheet.merge_range(range, str(v).upper(),formato_titulo)                    
                else:
                    range=abc[columna]+'6:'+abc[columna]+'6'                   
                    sheet.write(5,columna-1, str(v).upper(),formato_titulo)
                if k in descuentos:
                    encabezado_dinamico.append(columna)

        #SE DEFINEN LOS ENCABEZADOS DINÁMICAMENTE PARA QUE SE ADAPTEN AL ANCHO DE LAS COLUMNAS DE LA PLANILLA.
        #ANCHO DE LAS COLUMNAS
        sheet.set_column('A:A', 5)
        sheet.set_column('B:C', 30)
        sheet.set_column('D:Z', 25)
        sheet.merge_range(abc[1]+'1:'+abc[columna]+'2', d_nominas['empresa'],formato_header)
        sheet.merge_range(abc[1]+'3:'+abc[columna]+'3', d_nominas['titulo'],formato_header)
        sheet.merge_range(abc[1]+'4:'+abc[columna]+'4', '(CIFRAS EXPRESADAS EN ' + d_nominas['moneda']+')',formato_header)

        if estructura_id ==estructura_quincena:
            inicio,fin=0,0
            if len(encabezado_dinamico)>0 and len(encabezado_dinamico)<= 1:
                inicio,fin=encabezado_dinamico[0],encabezado_dinamico[0]
                sheet.merge_range(abc[inicio]+'5:'+abc[fin]+'5', 'DESCUENTOS',formato_titulo)
            elif len(encabezado_dinamico)>1:
                inicio,fin=encabezado_dinamico[0],encabezado_dinamico[-1]
                sheet.merge_range(abc[inicio]+'5:'+abc[fin]+'5', 'DESCUENTOS',formato_titulo)
        elif estructura_id ==estructura_finmes:
            sheet.merge_range('K5:K6', 'COMISION',formato_titulo)   
            sheet.merge_range('M5:U5', 'DESCUENTOS',formato_titulo)   
        #INICIA LA CONSTUCCIÓN DL DETALLE DE LA PLANILLA
        #DEPARTAMENTOS
        fila=6
        for departamento in d_nominas['departamentos']:
            fila+=1
            sheet.merge_range('A'+str(fila)+':B'+str(fila), departamento['departamento'],formato_grupo)
            #EMPLEADOS
            for empleado in departamento['detalle']:
                fila += 1
                columna = 0
                #RECORRO EL DETALLE
                for codigo in empleado['empleado']:
                    for k, v in codigo.items():
                        #DETALLE DE LAS LINEAS DE EMPLEADOS
                        columna+=1
                        range=abc[columna]+str(fila)+':'+abc[columna]+str(fila)
                        if isinstance(v, date):
                            sheet.write(range,v,formato_fecha)
                        elif isinstance(v, str):
                            sheet.write(range,v,formato_celda)
                        else:
                            sheet.write(range,v,formato_numero)
            #TOTALES POR DEPARTAMENTO
            fila+=1
            columna = 0
            for codigo in departamento['totales']:
                for k,v in codigo.items():
                    columna+=1
                    range=abc[columna]+str(fila)+':'+abc[columna]+str(fila)
                    sheet.write(range,v,formato_sumatoria)
        #TOTALES GENERALES
        fila+=1
        columna = 0
        columna_dinamica=0
        fila_dinamica=0
        for codigo in d_nominas['totales']:
            for k,v in codigo.items():
                columna+=1
                range=abc[columna]+str(fila+1)+':'+abc[columna]+str(fila+1)
                if estructura_id == estructura_finmes:
                    sheet.write(range,v,formato_sumatoria)
                else:
                    sheet.write(range,v,formato_gran_total)
                if k=='BASIC':
                    columna_dinamica=columna

        range=abc[1]+str(fila+1)+':'+abc[columna_dinamica-1]+str(fila+1)
        sheet.merge_range(range,'TOTALES',formato_titulo)     
        #RESUMEN
        sheet = workbook.add_worksheet('RESUMEN')
        sheet.set_column("A:B", 15)
        sheet.set_column("D:D", 10)
        sheet.set_column("E:E", 30)
        sheet.set_column("F:F", 15)
        sheet.set_column("G:G", 20)
        fila=-1
        columna=-1
        for k,v in d_nominas['resumen']['totales'].items():
            fila+=1
            sheet.write(fila,0,k,formato_titulo)
            sheet.write(fila,1,v,formato_numero)
        #LISTADO DE EMPLEADOS POR FORMA DE PAGO
        fila=0
        sheet.write(0,3,'NO',formato_titulo)
        sheet.write(0,4,'EMPLEADO',formato_titulo)
        sheet.write(0,5,'MONTO',formato_titulo)
        sheet.write(0,6,'FORMA DE PAGO',formato_titulo)
        for forma in d_nominas['resumen']['formapago']:
            columna=2
            fila+=1
            for k,v in forma.items():
                columna+=1
                if isinstance(v,float):
                    sheet.write(fila,columna,v,formato_numero)
                else:
                    sheet.write(fila,columna,v,formato_celda) 

    def generate_xlsx_report(self, workbook,data, model):
        self.generar_excel_dinamico(workbook, model)

