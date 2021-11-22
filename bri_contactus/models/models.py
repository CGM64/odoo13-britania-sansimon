from odoo import models ,fields , api
import werkzeug.urls
import random

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    medio_conocio = fields.Many2one('utm.medium', 'Medio')
    depto = fields.Many2one('res.country.state', 'Departamento')
    modelo = fields.Many2one('fleet.vehicle.model', 'Modelo')
    medio_contacto = fields.Many2one('crm.medio.contacto', string='Medio de contacto', help='Medio por el cual el cliente desea que lo contacten.')

    # Correos de confirmacion para el cliente
    opp_token = fields.Char(copy=False)
    token_url = fields.Char(compute='_generate_url', string='URL para validar la oportunidad')

    def _generate_token(self):
        chars ='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        return ''.join(random.SystemRandom().choice(chars) for _ in range(25))
        # self.opp_token = ''.join(random.SystemRandom().choice(chars) for _ in range(25))
        pass

    @api.depends('opp_token')
    def _generate_url(self):
        query = dict(db=self.env.cr.dbname, token=self.opp_token)
        base_url = self.env ['ir.config_parameter'].sudo().get_param('web.base.url')
        base = '/lead_verify/'
        validate_url = "%s?%s" % (base_url + base, werkzeug.urls.url_encode(query))
        # return validate_url
        self.token_url = validate_url
        pass

class Leads(models.Model):
    _name = "crm.medio.contacto"
    _description = "Medio por el cual el cliente desea ser contactado"

    name = fields.Char(string='Medio', required=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado del medio.")