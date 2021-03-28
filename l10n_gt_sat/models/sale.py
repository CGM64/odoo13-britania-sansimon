# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang


class PurchaseOrder(models.Model):

    _inherit = "sale.order.line"

    price_unit_access = fields.Boolean(compute='_compute_group_access', string='Price Unit Access')

    def _compute_group_access(self):
        if self.env.user.has_group('l10n_gt_sat.group_cambio_de_precios'):
            self.price_unit_access = True
        else:
            self.price_unit_access = False
