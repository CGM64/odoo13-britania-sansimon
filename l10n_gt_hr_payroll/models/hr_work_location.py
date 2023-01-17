# -*- coding:utf-8 -*-

from datetime import date, datetime, time
from collections import defaultdict

from pkg_resources import require
from odoo import api, fields, models


class ResCompanyInherit(models.Model):
    _name = "hr.work.location"
    #_inherit = "hr.work.location"
    _description = "Centro de trabajo IGSS"
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(string="Centro de trabajo", required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    address_id = fields.Many2one('res.partner', required=True, string="Dirección de trabajo", domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    location_number = fields.Char('Número de locacion')
    zona = fields.Char(string="Zona", help="Zona donde se ubica el centro de trabajo.")
    contacto = fields.Char(string="Nombre del contacto del centro de trabajo", help="Nombre del contacto del centro de trabajo.")
    code_actividad_economica = fields.Many2one('hr.actividad.economica.iggs', string="Actividad Económica", help="Código de actividad económica.", required=True)