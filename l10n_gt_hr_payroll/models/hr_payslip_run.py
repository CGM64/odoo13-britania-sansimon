#-*- coding:utf-8 -*-

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta, MO, SU
from dateutil import rrule
from collections import defaultdict
from datetime import date
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import re

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    bono_descuento_id = fields.Many2one('hr.bonos.descuentos', string='Bono o Descuento', readonly=True, copy=False)

    #Funcion que me permite volver a estado borrador la nomina, siempre y cuando las nominas no esten confirmadas ni canceladas.
    def action_draft(self):
        for nom in self.slip_ids:
            if nom.state == 'verify':
                nom.action_payslip_cancel()
                nom.action_payslip_draft()
                nom.unlink()
            elif nom.state == 'draft':
                nom.unlink()
            else:
                raise ValidationError(_("Existen nominas en estatus Validado o Cancelado. No se puede anular la nomina."))
        if self.bono_descuento_id:
            bonos_descuentos = self.env['hr.bonos.descuentos'].browse(self.bono_descuento_id.id)
            bonos_descuentos.write({'state' : 'draft'})
        return self.write({'state': 'draft'})

    def action_validate(self):
        res = super().action_validate()
        regexLetras = "[^a-zA-Z0-9_:, ]"

        emp_sin_cuenta=[]
        emp_sin_cod_ach=[]
        for payslip in self.slip_ids.filtered(lambda x: x.employee_id.contract_id.forma_pago in ('transferencia','ach')):
            if not payslip.employee_id.bank_account_id:
                emp_sin_cuenta.append(payslip.employee_id.name)
            if payslip.employee_id.bank_account_id.bank_id.ach_quetzales==0 and payslip.employee_id.contract_id.forma_pago=="ach":
                emp_sin_cod_ach.append(payslip.employee_id.name)
            if payslip.employee_id.bank_account_id.bank_id.ach_dolares==0 and payslip.employee_id.contract_id.forma_pago=="ach":
                emp_sin_cod_ach.append(payslip.employee_id.name)
        errores={
            "SIN CUENTA BANCARIA":emp_sin_cuenta,
            "SIN CODIGO ACH":emp_sin_cod_ach,
        }
        errores_modificado = re.sub(regexLetras, "", str(errores))

        if errores['SIN CUENTA BANCARIA']!=[] or errores['SIN CODIGO ACH']!=[]:
            raise ValidationError(_("Existen errores en los siguientes empleados:\n"+errores_modificado))
        
        if self.bono_descuento_id:
            bonos_descuentos = self.env['hr.bonos.descuentos'].browse(self.bono_descuento_id.id)
            bonos_descuentos.write({'state' : 'done'})
        
        return res
