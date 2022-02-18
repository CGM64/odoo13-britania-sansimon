# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp

class HrTallaCamisas(models.Model):
    _name = 'hr.talla.camisa'
    _description = 'Talla de Camisa'

    name = fields.Char(string='Talla', required=True, index=True)

    _sql_constraints = [
        ('hr_talla_camisa_duplicado', 'UNIQUE (name)',
         'El dato a insertar ya existe.'),
    ]

class HrNivelAcademico(models.Model):
    _name = 'hr.contrato.lugar'
    _description = 'Lugar de Contrato'

    name = fields.Char(string='Lugar', required=True, index=True)

    _sql_constraints = [
        ('hr_contrato_lugar_duplicado', 'UNIQUE (name)',
         'El dato a insertar ya existe.'),
    ]