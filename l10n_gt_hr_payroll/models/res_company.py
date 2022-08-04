# -*- coding:utf-8 -*-

from datetime import date, datetime, time
from collections import defaultdict
from odoo import api, fields, models


class ResCompanyInherit(models.Model):
    _description = "Res Company"
    _inherit = 'res.company'

    numero_patronal = fields.Char(string="Número patronal", help="Numero patronal IGSS")