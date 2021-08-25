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
        # order = super(SaleOrderInherit,self).action_confirm()
        porcentaje_maximo=self.team_id.porcentaje_maximo
        cont=0
        for line in self.order_line:
            if line.discount >porcentaje_maximo:
                cont+=1
        
        print('Porcentaje Team->',porcentaje_maximo,' Contador',cont,' Team',self.team_id.name)
        if cont ==0:
            return super(SaleOrderInherit,self).action_confirm()
        else:
            raise UserError(_("El porcentaje de descuento es mayo al porcentaje permitido."))
