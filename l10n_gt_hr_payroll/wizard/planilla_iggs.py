# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class HrPlanillaIgssWizard(models.TransientModel):
    _name = "planilla.igss.wizard"
    _description = "Planilla IGSS"

    rango_fecha_inicio = fields.Date(string="Fecha de Inicio", index=True,  default=datetime.today() + relativedelta(months=-1, day=1), required=True)
    rango_fecha_fin = fields.Date(string="Fecha final", index=True, default=datetime.today() + relativedelta(day=1, days=-1), required=True)

    #MÉTODO PARA GENERAR EL ARCHIVO EXCEL
    def generate_xlsx(self):
        print("Llego al export_xls.")
        self.ensure_one()
        data = {}
        data['form'] = self.read(['rango_fecha_inicio', 'rango_fecha_fin'])[0]

        return self.env['ir.actions.report'].search([('report_name', '=', 'l10n_gt_hr_payroll.planilla_igss_xlsx'),
            ('report_type', '=', 'xlsx')]).report_action(self,data=data)
    
    def generate_txt(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['rango_fecha_inicio', 'rango_fecha_fin',])[0]
        return self.env.ref('l10n_gt_hr_payroll.l10n_gt_planilla_electronica_igss_txt').with_context(landscape=True).report_action(self, data=data)