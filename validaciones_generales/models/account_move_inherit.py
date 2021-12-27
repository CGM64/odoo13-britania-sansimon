# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request
import datetime
from odoo.tools.float_utils import float_compare

class AccountMovInherit(models.Model):
    _inherit = "account.move"
    _description = "Validaciones para el modelo account.move"

    def action_post(self):
        self.ensure_one()
        if  self.journal_id.fel_setting_id.id!=False  and self.journal_id.tipo_operacion=='FACT' and self.journal_id.tipo_documento in('FACT','NCRE'):
            for line in self.invoice_line_ids:
                # if line.tax_ids.id==False:
                if len(line.tax_ids)==0:
                    raise UserError(_('El siguiente producto no tiene impuesto asociado:\n%s ,por favor rectifique.') % line.product_id.name)       
        rslt = super(AccountMovInherit, self).action_post()    
        return rslt