# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools import float_is_zero, format_date
from odoo.exceptions import UserError

from datetime import date


class HrEmployeeInformeEmpleadorWizard(models.TransientModel):
    _name = 'hr.employee.informe.empleador.wizard'
    _description = 'Informe del Empleador y Nomina 29-89 Y Zonas Francas'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    periodos = fields.Char('Periodo', default=fields.Date.today().strftime('%Y'))
    

            
    
    def informe_empleador(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['company_id', 'periodos'])[0]
            
        return self.env.ref('l10n_gt_hr_payroll.hr_informe_empleador').report_action(self,data=data)

