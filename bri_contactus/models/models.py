from odoo import models ,fields , api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medio_conocio = fields.Many2one('utm.medium', 'Medio por el cual nos conoció.')
