# -*- coding: utf-8 -*-
from odoo import fields,models, api, _
from datetime import datetime, timedelta, time,date
from odoo.http import request
from odoo.tools.misc import format_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, date_utils,float_is_zero
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    porcentaje_maximo = fields.Float('Porcentaje', digits='Porcentaje')


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        porcentaje_maximo=self.team_id.porcentaje_maximo
        cont=0
        for line in self.order_line:
            if line.discount >porcentaje_maximo:
                cont+=1
        
        if cont ==0:
            return super(SaleOrderInherit,self).action_confirm()
        else:
            raise UserError(_("El porcentaje de descuento es mayor al porcentaje permitido."))


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        porcentaje_maximo=self.team_id.porcentaje_maximo
        cont=0
        for line in self.invoice_line_ids:
            if line.discount >porcentaje_maximo:
                cont+=1
        
        if cont ==0:
            return super(AccountMoveInherit,self).action_post()
        else:
            raise UserError(_("El porcentaje de descuento es mayor al porcentaje permitido."))


# class SaleAdvancePaymentInv(models.TransientModel):
#     _inherit = "sale.advance.payment.inv"

#     def create_invoices(self):

#         porcentaje_maximo=self.team_id.porcentaje_maximo
#         cont=0
#         for line in self.order_line:
#             if line.discount >porcentaje_maximo:
#                 cont+=1
#         if cont ==0:
#             return super(SaleAdvancePaymentInv,self).create_invoices()
#         else:
#             raise UserError(_("El porcentaje de descuento es mayo al porcentaje permitido."))
