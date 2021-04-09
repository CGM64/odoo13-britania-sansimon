from odoo import models ,fields , api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medio_conocio = fields.Many2one('utm.medium', 'Medio')
    depto = fields.Many2one('res.country.state', 'Departamento')
    modelo = fields.Many2one('fleet.vehicle.model', 'Modelo')
