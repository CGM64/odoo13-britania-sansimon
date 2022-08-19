#-*- coding:utf-8 -*-
from . import letras
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta, MO, SU
from dateutil import rrule
from collections import defaultdict
from datetime import date
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips

dias_lab_mes = 30.416

class Payslip(models.Model):
    _inherit = 'hr.payslip'

    number_of_hours = fields.Float(string='Number of Hours', readonly=True)

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'dias_lab_mes': dias_lab_mes,
            'horas_totales_lab': self.number_of_hours,
            'compute_sueldo_x_dia': compute_sueldo_x_dia,
            'compute_sueldo_x_dia_porcentaje': compute_sueldo_x_dia_porcentaje,
            'compute_codigo_nomina_anterior': compute_codigo_nomina_anterior,
        })
        return res

    def _get_cuenta_analitica_resultados(self, account_id, line):
        analytic_account_id = line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id
        account = self.env['account.account'].browse(account_id)
        if account.user_type_id.include_initial_balance == True:
            return None
        return analytic_account_id

    #Funcion heredada, para poder asignar cuenta analitica solo cuando las cuentas son de resultado
    def _prepare_line_values(self, line, account_id, date, debit, credit):
        return {
            'name': line.name,
            'partner_id': line.partner_id.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_account_id': self._get_cuenta_analitica_resultados(account_id, line),
        }

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        existing_lines = (
            line_id for line_id in line_ids if
            line_id['name'] == line.name
            and line_id['account_id'] == account_id
            and line_id['analytic_account_id'] == (self._get_cuenta_analitica_resultados(account_id, line))
            and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
        return next(existing_lines, False)
    
    #Funcion que permete agregar automaticamente, las otras entradas  a la nomina de cada empleado segun estructura salarial.
    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        res = super()._onchange_employee()
        for payslip in self:
            estructura_otras_entradas = payslip.struct_id.input_line_type_ids
            input_line_vals = []
            calendar = payslip.contract_id.resource_calendar_id

            #Las seguientes lineas son porque necesito saber cuantas horas default debiera trabajar cada empleado en el periodo de tiempo asignado
            date_start = fields.Datetime.to_datetime(payslip.date_from)
            date_stop = datetime.combine(fields.Datetime.to_datetime(payslip.date_to), datetime.max.time())
            payslip.number_of_hours = payslip.contract_id._get_horas_completas(date_start, date_stop)

            if not payslip.input_line_ids:
                for entrada in estructura_otras_entradas.sorted(lambda line: line.name):
                    monto = 0
                    if entrada.name == 'Anticipo de Quincena':
                        monto = payslip._monto_nomina_anticipo()
                    elif entrada.name == 'Bono de Produccion':
                        monto = payslip._monto_nomina_produccion()
                    elif entrada.name == 'Comision':
                        monto = payslip._monto_nomina_comision()
                    elif entrada.name == 'Bono Especial':
                        monto = (0 or payslip.contract_id.bono_especial) / 2
                    elif entrada.code == 'INPBONO14':
                        monto =payslip._monto_nomina_bono14()
                    elif entrada.code == 'INPAGUINALDO':
                        monto =payslip._monto_nomina_aguinaldo()


                    input_line_vals.append((0, 0, {
                        'amount': monto,
                        'input_type_id': entrada.id,
                    }))
                payslip.update({'input_line_ids': input_line_vals})
        self._calcular_bonos_descuentos()
        return res

    def _get_new_worked_days_lines(self):
        
        valor = [(5, False, False)]
        if self.struct_id.use_worked_day_lines:
            valor = [(5, 0, 0)] + [(0, 0, vals) for vals in self._get_worked_day_lines()]
            valor += [(0, 0, vals) for vals in self._get_new_worked_days_septimo(valor)]
        return valor
    
    # Odoo 13, no existe la función '_get_worked_day_lines_hours_per_day'
    def _get_worked_day_lines_hours_per_day(self):
        self.ensure_one()
        return self.contract_id.resource_calendar_id.hours_per_day

    def _get_new_worked_days_septimo(self, valor):
        domain=None
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        # Odoo 13, la función '_get_work_hours' no tiene parametro 'domain'
        # work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        
        add_days_rounding = 0
        horas = 0
        dias_promedio = 0
        work_entry_type_septimo = self.env.ref('l10n_gt_hr_payroll.work_entry_type_septimo')
        for dato in valor:
            if dato[0] == 0:
                hours = dato[2]['number_of_hours']
                work_entry_type_id = dato[2]['work_entry_type_id']
                work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)              
                days = round(hours / hours_per_day, 5) if hours_per_day else 0
                days += add_days_rounding
                day_rounded = self._round_days(work_entry_type, days)
                add_days_rounding += (days - day_rounded)
                if work_entry_type.es_afecto_septimo:
                    horas += hours
                    dias_promedio += day_rounded
        if horas == 0:
            horas = 16
            dias_promedio = 2
        elif horas > 0 and horas <= 44:
            horas = 8
            dias_promedio = 1
        else:
            horas = 0
            dias_promedio = 0
            
        attendance_line = {
            'sequence': work_entry_type_septimo.sequence,
            'work_entry_type_id': work_entry_type_septimo.id,
            'number_of_days': dias_promedio,
            'number_of_hours': horas,
        }
        res.append(attendance_line)
        #raise UserError(_('Hola mundo.'))
        return res
    
    def action_payslip_cancel(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        #if self.filtered(lambda slip: slip.state == 'done'):
        #    raise UserError(_("Cannot cancel a payslip that is done."))
        return self.write({'state': 'cancel'})

    def _get_anio_biciesto(self):
        year = datetime.now().year
        if year % 4 == 0:
            if año % 100 == 0:
                if año % 400 == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False

    #Funcion para calcular el bono14
    def _monto_nomina_bono14_deactivar_temporalmente(self):
        year = int(self.date_from.strftime('%Y'))-1
        # year = datetime.now().year - 1
        fecha_inicio =  datetime.today().strftime(str(year) + '-07-01')
        fecha_fin =  datetime.today().strftime('%Y-06-30')
        dominio_nominas = [
            ('state','=','done'),
            ('contract_id','=', self.contract_id.id),
            ('date_from','>=',fecha_inicio),
            ('date_to','<=',fecha_fin)
        ]

        #La siguiente funcion es para ir a traer todos los sueldos en el año y promediarlo
        empleado_nominas = self.env['hr.payslip'].search(dominio_nominas + [('struct_id','=',(self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id)),])
        # sueldo_total = sum(sueldo_dia.total for sueldo_dia in empleado_nominas.line_ids.filtered(lambda payslip: payslip.code == 'HRSUD'))
        sueldo_total = sum(calculo.total for calculo in empleado_nominas.line_ids.filtered(lambda payslip: payslip.code == 'BASIC'))
        sueldo_promedio = sueldo_total / 12

        # dias_del_anio = 366 if self._get_anio_biciesto() else 365
        #
        # Las sig. lineas es para ir a traer los dias que faltaron en el año.
        # empleado_nominas = self.env['hr.payslip'].search(dominio_nominas + [
        #     ('struct_id','in',(
        #         self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id,
        #         self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id
        #         )
        #     ),
        # ])
        # dias_falta_empleado = sum(dia_falta.number_of_days for dia_falta in empleado_nominas.worked_days_line_ids.filtered(lambda payslip: payslip.work_entry_type_id.code == 'AUSENCIAINJUS'))
        # total_dias_trabajados = dias_del_anio - dias_falta_empleado
        #
        # sueldo_bono14 = sueldo_promedio / dias_del_anio * total_dias_trabajados
        # sueldo_bono14 = round(sueldo_bono14,2)

        return sueldo_promedio

    #Funcion para calcular el bono14 cuando no hay historia de bono
    def _monto_nomina_bono14(self):
        
        sueldo_promedio = 10
        
        year = int(self.date_from.strftime('%Y'))-1
        bono14_fecha_inicio = datetime.strptime(str(year) + '-07-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        bono14_fecha_fin =  datetime.strptime(str(year+1) + '-06-30 23:59:59', '%Y-%m-%d %H:%M:%S')
        dias_del_anio = bono14_fecha_fin - bono14_fecha_inicio        
        fecha_inicio_contrato = datetime.strptime(fields.Date.to_string(self.contract_id.date_start) + ' 00:00:00', "%Y-%m-%d %H:%M:%S")
        
        if fecha_inicio_contrato > bono14_fecha_inicio:
            bono14_fecha_inicio = fecha_inicio_contrato
        
        dias_laborados = bono14_fecha_fin - bono14_fecha_inicio
        
        sueldo_promedio = dias_laborados / dias_del_anio * self.contract_id.wage
        return sueldo_promedio

    def _obtener_periodo_bono14(self):
        year = int(self.date_to.strftime('%Y'))-1
        bono14_fecha_inicio = datetime.strptime(str(year) + '-07-01 00:00:00', '%Y-%m-%d %H:%M:%S')

        string_fecha_inicio = str(year) + '-07-01 00:00:00' if not self.contract_id.date_start else str(self.contract_id.date_start) + ' 00:00:00'
        string_fecha_fin = str(year+1) + '-07-01 00:00:00' if not self.contract_id.date_end else str(self.contract_id.date_end) + ' 00:00:00'

        fecha_inicio_contrato = datetime.strptime(string_fecha_inicio, '%Y-%m-%d %H:%M:%S')
        fecha_fin_contrato = datetime.strptime(string_fecha_fin ,'%Y-%m-%d %H:%M:%S')

        if bono14_fecha_inicio < fecha_inicio_contrato:
            bono14_fecha_inicio = fecha_inicio_contrato
        
        bono14_fecha_fin =  datetime.strptime(str(year+1) + '-07-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        if fecha_fin_contrato < bono14_fecha_fin:
            bono14_fecha_fin = fecha_fin_contrato
        
        dias_laborados = bono14_fecha_fin - bono14_fecha_inicio
        ret = { "dias_laborados": dias_laborados.days, "periodo_inicio": bono14_fecha_inicio, "periodo_fin": bono14_fecha_fin}
        return ret

    #Funcion para calcular el aguinaldo
    def _monto_nomina_aguinaldo(self):
        year = int(self.date_from.strftime('%Y'))-1
        # year = datetime.now().year - 1
        fecha_inicio =  datetime.today().strftime(str(year) + '-12-01')
        fecha_fin =  datetime.today().strftime('%Y-11-30')
        dominio_nominas = [
            ('state','=','done'),
            ('contract_id','=', self.contract_id.id),
            ('date_from','>=',fecha_inicio),
            ('date_to','<=',fecha_fin)
        ]
        
        estructuras_salariales = (
            self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id,
            self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id,
        )

        #La siguiente funcion es para ir a traer todos los sueldos en el año y promediarlo
        empleado_nominas = self.env['hr.payslip'].search(dominio_nominas + [('struct_id','in',estructuras_salariales),])
        
        horas_trabajados = 0
        sueldo_total = 0
        for empleado_nomina in empleado_nominas:
            numero_horas_total = empleado_nomina.number_of_hours
            horas_trabajados = 0
            for dias in empleado_nomina.worked_days_line_ids:
                if dias.work_entry_type_id.code in ('WORK100','SUSINGSSENFERMEDAD'):
                    horas_trabajados += dias.number_of_hours

            sueldo_mensual = sum(lineas.total for lineas in empleado_nomina.line_ids.filtered(lambda payslip: payslip.code in ('BASIC')))
            sueldo_mensual = sueldo_mensual / 2
            sueldo_diario = sueldo_mensual / numero_horas_total
            sueldo_mensual_trabajado = sueldo_diario * horas_trabajados 
            sueldo_comision = sum(lineas.total for lineas in empleado_nomina.line_ids.filtered(lambda payslip: payslip.code in ('COMISION')))
            sueldo_total += sueldo_mensual_trabajado + sueldo_comision
        
            #print("%s|%s|%s|%s|%s|%s|%s" % (empleado_nomina.name,sueldo_mensual,numero_horas_total,sueldo_diario,horas_trabajados,sueldo_mensual_trabajado,sueldo_comision))
        sueldo_promedio = sueldo_total / 12
                    


        return sueldo_promedio

    #Funcion para ir a calcular el anticipo
    def _monto_nomina_anticipo(self):
        fecha_inicio = self.date_from.replace(month=self.date_from.month, day=1, year=self.date_from.year)
        empleado_nomina_anticpo = self.env['hr.payslip'].search([
                ('struct_id','in',(
                    self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t1_7_30').id,
                    self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t1_8_30').id,
                    self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t2_7_30').id,
                    self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t2_8_30').id,
                    self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id)
                ),
                #('state','in',('done','paid')),
                ('contract_id','=', self.contract_id.id),
                ('date_from','>=',fecha_inicio)
                ])
        print("$$$$$$ %s", empleado_nomina_anticpo.id)
        for calculo in empleado_nomina_anticpo.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE'):
            print("0000000 %s = %s", calculo.code, calculo.total)
        for calculo in empleado_nomina_anticpo.line_ids.filtered(lambda payslip: payslip.code == 'LIQRE'):
            return calculo.total
        return 0

    #Funcion para ir a calcular la comision en base al reporte de comisiones
    def _monto_nomina_produccion(self):
        #Calculo de comision o de bono en la nomina de fin de mes, obtiene el monto en base a la suma de todas las nominas de bono del mes.
        # if self.struct_id.id == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_emp').id:
        #     fecha_inicio = self.date_from.replace(month=self.date_from.month, day=1, year=self.date_from.year)
        #     empleado_nomina_anticpo = self.env['hr.payslip'].search([
        #             ('struct_id','=',self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id),
        #             ('state','=','done'),
        #             ('contract_id','=', self.contract_id.id),
        #             ('date_from','>=',fecha_inicio)
        #             ])
        #     return sum(calculo.total for calculo in empleado_nomina_anticpo.line_ids.filtered(lambda payslip: payslip.code == 'BONO'))
        #Calculo de la comision o bono, este se basa del reporte de comision de ventas del mes anterior y solo aplica en la nomina de bono.
        if self.struct_id.id == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id:
            mes_anterior = self.date_from + relativedelta(months=-1)
            periodo = mes_anterior.month
            ejercicio = mes_anterior.year
            reporte_comision = self.env['venta.comision'].search([('state','=','done'),('periodo','=',periodo),('ejercicio','=',ejercicio)])
            if reporte_comision:
                empleado_usuario = self.employee_id.user_id
                return sum(empleado.comision for empleado in reporte_comision.sales_commision_line.filtered(lambda r: r.vendedor_id.id == empleado_usuario.id and r.tipo_bono_nomina=='productividad'))
        return 0

    def _monto_nomina_comision(self):
        if self.struct_id.id == self.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id:
            mes_anterior = self.date_from + relativedelta(months=-1)
            periodo = mes_anterior.month
            ejercicio = mes_anterior.year
            reporte_comision = self.env['venta.comision'].search([('state','=','done'),('periodo','=',periodo),('ejercicio','=',ejercicio)])
            if reporte_comision:
                empleado_usuario = self.employee_id.user_id
                return sum(empleado.comision for empleado in reporte_comision.sales_commision_line.filtered(lambda r: r.vendedor_id.id == empleado_usuario.id and r.tipo_bono_nomina=='comision'))
        return 0
    
    def _calcular_bonos_descuentos(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        for payslip in payslips:
            bonos_descuentos = self.env['hr.bonos.descuentos'].search([('state','=','draft'),('date','>=',payslip.date_from),('date','<=',payslip.date_to),('struct_id','=',payslip.struct_id.id)])
            descuentos_empleado = bonos_descuentos.bono_descuentos_line_ids.filtered(lambda r: r.contract_id.id == payslip.contract_id.id)
            payslip.payslip_run_id.bono_descuento_id = bonos_descuentos.id
            
            for entrada_montos in payslip.input_line_ids:
                
                descuento = descuentos_empleado.filtered(lambda r: r.input_type_id.id == entrada_montos.input_type_id.id)
                if descuento:
                    entrada_montos.amount = descuento.amount
                    entrada_montos.name = descuento.name
    
    def action_refresh_from_work_entries(self):
        self._calcular_bonos_descuentos()
        return super().action_refresh_from_work_entries()
    
    def monto_letras(self,importe):
        #Verificar el tipo de moneda
        if not importe or importe == 0.0:
            return ""
        enletras = letras
        cantidadenletras = enletras.to_word(importe)
        if self.company_id.currency_id.name == 'USD':
            cantidadenletras = cantidadenletras.replace('QUETZALES','DOLARES')
        elif self.company_id.currency_id.name == 'EUR':
            cantidadenletras = cantidadenletras.resultado('QUETZALES','EUROS')
        else:
            cantidadenletras = cantidadenletras
        return cantidadenletras

    

#Funcion para el salario devengado menos las ausencias.
def compute_sueldo_x_dia(payslip, categories, worked_days, inputs, code):
    employee = payslip.contract_id.employee_id
    wage = categories.BASIC
    dias_trabajados = 0
    numero_dias_total = payslip.number_of_hours
    for dias in payslip.worked_days_line_ids:
        if dias.work_entry_type_id.code == code:
            dias_trabajados = dias.number_of_hours
    sueldo_quincena = wage / 2
    if numero_dias_total == 0:
        return 0
    sueldo_diario = sueldo_quincena / numero_dias_total
    sueldo_total = sueldo_diario * dias_trabajados
    total = sueldo_total
    #print("--%s=%s" % (code, total))
    
    return round(total,2)

def compute_sueldo_x_dia_porcentaje(payslip, categories, worked_days, inputs, code, code_septimo, porcentaje):
    employee = payslip.contract_id.employee_id
    wage = categories.BASIC
    dias_trabajados = 0
    dias_septimo = 16 # mas 16 para sumar los 2 septimos
    numero_dias_total = payslip.number_of_hours
    for dias in payslip.worked_days_line_ids:
        # if (dias.work_entry_type_id.code == code_septimo):
        #     dias_septimo = dias.number_of_hours
        if dias.work_entry_type_id.code == code:
            dias_trabajados = dias.number_of_hours
    sueldo_quincena = wage * (porcentaje/100)
    if numero_dias_total == 0:
        return 0
    dias_trabajados += dias_septimo
    sueldo_diario = sueldo_quincena / numero_dias_total
    sueldo_total = sueldo_diario * dias_trabajados
    total = sueldo_total
    #print("--%s=%s" % (code, total))
    
    return round(total,2)

#Busca el valor del codigo enlas nominas anteriores, esto es para obtener el total de bono especial entre todas las nominas del me..
def compute_codigo_nomina_anterior(payslip, clave):
    fecha_inicio = payslip.date_from.replace(month=payslip.date_from.month, day=1, year=payslip.date_from.year)
    fecha_fin = payslip.date_to
    empleado_nomina_anticpo = payslip.env['hr.payslip'].search([
            ('struct_id','in',(
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t1_7_30').id,
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t1_8_30').id,
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t2_7_30').id,
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_t2_8_30').id,
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_anticipo_emp').id,
                payslip.env.ref('l10n_gt_hr_payroll.hr_payroll_salary_structure_gt_bonos_emp').id)),
            #('state','in',('done','paid')),
            ('contract_id','=', payslip.contract_id.id),
            ('date_from','>=',fecha_inicio),
            ('date_to','<=',fecha_fin)
            ])
    total = sum(calculo.total for calculo in empleado_nomina_anticpo.line_ids.filtered(lambda payslip: payslip.code == clave))
    print("Si entro con la %s=%s" % (clave,total))
    return total

# class HrPayslipRun(models.Model):
#     _inherit = 'hr.payslip.run'

#     #Funcion que me permite volver a estado borrador la nomina, siempre y cuando las nominas no esten confirmadas ni canceladas.
#     def action_draft(self):
#         for nom in self.slip_ids:
#             if nom.state == 'verify':
#                 nom.action_payslip_cancel()
#                 nom.action_payslip_draft()
#                 nom.unlink()
#             elif nom.state == 'draft':
#                 nom.unlink()
#             else:
#                 raise ValidationError(_("Existen nominas en estatus Validado o Cancelado. No se puede anular la nomina."))

#         return self.write({'state': 'draft'})
