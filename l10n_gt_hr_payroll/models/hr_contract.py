# -*- coding:utf-8 -*-

from datetime import date, datetime, time,timedelta
from calendar import monthrange
from collections import defaultdict
from odoo import api, fields, models
from odoo.tools import date_utils

import pytz

MESES = {
            1:'Enero',
            2:'Febrero',
            3:'Marzo',
            4:'Abril',
            5:'Mayo',
            6:'Junio',
            7:'Julio',
            8:'Agosto',
            9:'Septiembre',
            10:'Octubre',
            11:'Noviembre',
            12:'Diciembre',
        }

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    forma_pago = fields.Selection([
        ('transferencia', 'Transferencia'), 
        ('ach', 'Transferencia ACH'), 
        ('cheque', 'Cheque'),
        ('fondofijo', 'Cheque fondo fijo'),
        ('cajachica', 'Caja chica'),
        ], tracking=True, string="Forma de Pago", default='transferencia', help="Forma de pago para el empleado con cheque o transferencia.")
    bono_especial = fields.Float('Bono Especial', tracking=True)
    bono_decreto = fields.Float('Bono Decreto', tracking=True)
    isr = fields.Float('ISR', tracking=True)
    comision = fields.Float(string='Comision')
    bantrab = fields.Float(string='Bantrab', tracking=True)
    juridico = fields.Float(string='Juridico', tracking=True)
    aplica_igss = fields.Boolean(string='Aplica IGSS', default=True, tracking=True)
    tipo_contrato = fields.Selection([
                ('1', 'Verbal'),
                ('2', 'Escrito'),
                ], tracking=True, string="Tipo de Contrato MT", default='2', help="Tipos de contrato que maneja el reporte del ministerio de trabajo.")
    temporalidad_contrato = fields.Selection([
                ('1', 'Indefinido'),
                ('2', 'Definido'),
                ], tracking=True, string="Temporalidad del Contrato", default='1', help="Temporalidad de contrato (codigos del ministerio de trabajo).")
    jornada_trabajo = fields.Selection([
                ('1', 'Diurna'),
                ('2', 'Mixta'),
                ('3', 'Nocturna'),
                ('4', 'No está sujeto a jornada'),
                ], tracking=True, string="Jornada de Trabajo", default='1', help="Temporalidad de contrato (codigos del ministerio de trabajo).")
    fecha_reinicio_labores = fields.Date('Fecha de reinicio de labores', tracking=True, help="Fecha de reinicio de labores.")

    def _get_horas_completas(self, date_start, date_stop):
        """
        Genera el total de horas que un emleado debio trabajar en el
        periodo de tiempo asignado por el calendario de trabajo.
        return: entero.
        """
        for contract in self:
            employee = contract.employee_id
            calendar = contract.resource_calendar_id
            resource = employee.resource_id
            hr_contrar_entry = self.env['hr.work.entry']
            tz = pytz.timezone(calendar.tz)

            attendances = calendar._work_intervals(
                pytz.utc.localize(date_start) if not date_start.tzinfo else date_start,
                pytz.utc.localize(date_stop) if not date_stop.tzinfo else date_stop,
                resource=resource, tz=tz
            )
            
            # Attendances
            duracion = 0
            for interval in attendances:
                fecha_inicio = interval[0].astimezone(pytz.utc).replace(tzinfo=None)
                fecha_fin = interval[1].astimezone(pytz.utc).replace(tzinfo=None)
                duracion += hr_contrar_entry._get_duration(fecha_inicio, fecha_fin)
            
            duracion += 16 # Le sumo 16 horas mas por 2 dias de septimo que tienen derecho.
            return duracion
class ResourceCalendar(models.Model):

    _inherit = "resource.calendar"
    _description = "Resource Working Time"
    
    def _work_intervals(self, start_dt, end_dt, resource=None, domain=None, tz=None):
        if resource is None:
            resource = self.env['resource.resource']
        return self._work_intervals_batch(
            start_dt, end_dt, resources=resource, domain=domain, tz=tz
        )[resource.id]