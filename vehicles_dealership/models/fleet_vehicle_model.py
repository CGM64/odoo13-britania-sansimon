# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

"""Fleet Vehicle and products models."""

from odoo import api, fields, models

class FleetVehicle(models.Model):
    """Fleet Vehicle model."""

    _inherit = 'fleet.vehicle.model'
    
    is_publish = fields.Boolean(string='Publicar modelo en pagina web',help='Publicar modelo', default=False)