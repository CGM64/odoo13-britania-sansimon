# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    display_street = fields.Char('Direccion Completa', compute='_compute_street_name')
    display_website = fields.Char('Display WebSite', compute='_compute_street_name')

    def _compute_street_name(self):
        for record in self:
            direccion = ''
            if record.street:
                direccion += record.street
            if record.street2:
                direccion += " " + record.street2
            if record.state_id:
                direccion += " " + record.state_id.name
            record.display_street = direccion
            
            if record.website:
                encontrar = record.website.rfind('/')+1
                record.display_website = record.website[encontrar:]
