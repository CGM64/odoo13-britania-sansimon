from odoo import models ,fields , api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medio_conocio = fields.Many2one('utm.medium', 'Medio')
    depto = fields.Many2one('res.country.state', 'Departamento')
    modelo = fields.Many2one('fleet.vehicle.model', 'Modelo')
    medio_contacto = fields.Many2one('crm.medio.contacto', string='Medio de contacto', help='Medio por el cual el cliente desea que lo contacten.')

class Leads(models.Model):
    _name = "crm.medio.contacto"
    _description = "Medio por el cual el cliente desea ser contactado"

    name = fields.Char(string='Medio', required=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado del medio.")