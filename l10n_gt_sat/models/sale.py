# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):

    _inherit = "sale.order"

    partner_ref = fields.Char(string='Cod. Cliente', related='partner_id.default_code')

    def action_confirm(self):
        for linea in self.order_line:
            if linea.product_id.type == 'product' and linea.qty_available_today < linea.product_uom_qty:
                raise UserError(_('No hay suficiente existenca para el producto %s') % linea.name)
        res = super(SaleOrder, self).action_confirm()
        return res
