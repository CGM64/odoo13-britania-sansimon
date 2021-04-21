import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class GsGastos(models.Model):
    _name = "gs.gastos"
    _description = "Gastos"

    name=fields.Char(string="Descripcion")
    date=fields.Datetime(string="Fecha")
    done=fields.Boolean(string="Realizada")
