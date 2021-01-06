# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    actualizar_moneda = fields.Boolean(string='Actualizar tasa automaticamente', default=True)
