# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.http import request
class testExport(models.Model):
    _inherit = "hr.payroll_igss"
    _description = "Planilla IGSS"

    def export_xls(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['mes_planilla', 'anio_planilla', 'tipo_planilla', 'tipo_liquidacion'])[0]
        return self.env['ir.actions.report'].search([('report_name', '=', 'hr_payroll_igss.payroll_id'),
            ('report_type', '=', 'xlsx')]).report_action(self,data=data)
