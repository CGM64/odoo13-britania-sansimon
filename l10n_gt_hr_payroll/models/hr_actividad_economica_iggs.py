from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request


class EconomicActivity(models.Model):
    _name = "hr.actividad.economica.iggs"
    _description = "Actividad economica"

    display_name = fields.Char('Actividad', required=True, translate=True)
    name = fields.Char('Nombre de actividad', translate=True)
    categoria = fields.Char('Categoria', required=True, translate=True)
    complete_name = fields.Char(
        'Nombre completo', #compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('hr.actividad.economica.iggs', 'Ocupación padre')
    code = fields.Char('Codigo', translate=True)
    
    _sql_constraints = [
        ('name_uniq', 'unique (name, parent_id)', "Ya existe un registro con estos datos"),
    ]

#    @api.depends('display_name', 'parent_id.complete_name')
#    def _compute_complete_name(self):
#        for hr in self:
#            if hr.parent_id:
#                hr.complete_name = '%s / %s' % (hr.parent_id.complete_name, hr.display_name)
#                hr.name = hr.complete_name
#            else:
#                hr.complete_name = hr.display_name
#                hr.name = hr.display_name