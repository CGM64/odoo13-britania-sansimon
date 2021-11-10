# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from datetime import datetime,date

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    @api.onchange('property_product_pricelist')
    def _onchange_property_product_pricelist(self):
        if not self.user_has_groups('britania.res_partner_group_tarifas'):
            raise UserError(_('No tiene permisos para realizar cambios.'))
        # return print("realiza un cambio")


