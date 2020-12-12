# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    display_street = fields.Char('Direccion Completa', compute='_compute_street_name')
    display_website = fields.Char('Display WebSite', compute='_compute_street_name')

    def _compute_street_name(self):
        for record in self:
            record.display_street = record.street + " " + record.street2 + ", " + record.state_id.name
            encontrar = record.website.rfind('/')+1
            record.display_website = record.website[encontrar:]
