# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.tools import date_utils


class ResStateMunicipio(models.Model):
    _inherit = 'res.state.municipio'

    code_igss = fields.Char(string="Codigo IGSS", help="Codigo para planilla electronica IGSS")

class ResStateCountry(models.Model):
    _inherit = 'res.country.state'

    code_igss = fields.Char(string="Codigo IGSS", help="Codigo para planilla electronica IGSS")
