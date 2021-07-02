# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

class RepairType(models.Model):
    _name = "repair.type"
    _description = "Tipos de ordenes de reparación"

    name = fields.Char('Tipo de orden', required=True)
    default_type = fields.Boolean(string="Tipo de orden por defecto", help="Tipo de orden por defecto")

    @api.onchange('default_type')
    def _check_unique_nit(self):
        tipos = request.env['repair.type'].search([('default_type', '=', True)])
        for i in tipos:
            if i.id == self.id:
                pass
            else:
                i.update({
                    'default_type': False,
                })
        
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Conversión.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre!"),
    ]

class Repair(models.Model):
    _inherit = "repair.order"
    
    tipo_orden = fields.Many2one('repair.type', 'Tipo de orden', index=True)

    @api.model
    def create(self, vals):
        data_default = self.env['repair.type'].search([('default_type', '=', True)], limit=1).id
        vals['tipo_orden'] = data_default
        return super(Repair, self).create(vals)