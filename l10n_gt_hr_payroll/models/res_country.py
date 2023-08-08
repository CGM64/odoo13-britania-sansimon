# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.tools import date_utils


class ResCountry(models.Model):
    _inherit = 'res.country'

    codigo_nacionalidad = fields.Char(string="Codigo Nacionalidad", help="Codigo de nacionalidad para el reporte del ministerio de trabajo.")
