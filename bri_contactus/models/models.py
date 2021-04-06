from odoo import models ,fields , api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medio_conocio = fields.Char('Medio por el cual nos conocio')
