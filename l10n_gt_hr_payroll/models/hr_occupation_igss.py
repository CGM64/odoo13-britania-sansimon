# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class HrOccupationIgss(models.Model):
    _name = "hr.occupation.igss"
    _description = "Ocupaciones IGSS"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Nombre de ocupación IGSS', required=True)
    complete_name = fields.Char(
        'Nombre completo', compute='_compute_complete_name', recursive=True,
        store=True)
    parent_id = fields.Many2one('hr.occupation.igss', 'Ocupación padre', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('hr.occupation.igss', 'parent_id', 'Hijos Ocupacion')
    code = fields.Char('Codigo', required=True)
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('name_uniq', 'unique (name, code)', "Ya existe un registro con estos datos"),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for hr in self:
            if hr.parent_id:
                hr.complete_name = '%s / %s' % (hr.parent_id.complete_name, hr.name)
            else:
                hr.complete_name = hr.name