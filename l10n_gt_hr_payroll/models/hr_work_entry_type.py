#-*- coding:utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta, MO, SU
from dateutil import rrule
from collections import defaultdict
from datetime import date
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta


class Payslip(models.Model):
    _inherit = 'hr.work.entry.type'
    
    es_afecto_septimo = fields.Boolean(
        string="Afecta el septimo?", default=False,
        help="Indicador que sirve para saber si el tipo de asistencia afecta el septimo o no.")
    es_informe_empleador = fields.Boolean(
        string="Asistencia, Informe Empleador", default=True,
        help="Indicador que sirve para tomar en cuenta el tipo de asistencia como dias laborados durante el periodo.")
    es_suspendido_planilla_igss = fields.Boolean(
        string="Suspendido, Planila IGSS", default=False,
        help="Indicador que sirve para tomar en cuenta si el tipo de asistencia se toma en cuenta para reportar los suspendidos en el reporte de la planilla del igss.")
