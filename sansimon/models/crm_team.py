# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, date_utils,float_is_zero

class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    porcentaje_maximo = fields.Float('Porcentaje', digits='Porcentaje')
