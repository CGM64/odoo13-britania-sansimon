""" Colores para cada vehiculo """

import base64
from odoo import api, fields, models
from odoo.modules.module import get_module_resource

class FleetVehicle(models.Model):

    _name = "fleet.vehicle.model.color"
    _description = "Variantes de color para cada modelo"
    
    name = fields.Char(string="Nombre del color", placeholder="Nombre", required=True)
    #color = fields.Integer(string="Indice del color")
    color_name = fields.Selection([
        ('yellow', 'Amarillo'),
        ('blue', 'Azul'),
        ('white', 'Blanco'),
        ('gray', 'Gris'),
        ('lavender', 'Lavanda'),
        ('magenta', 'Magenta'),
        ('ivory', 'Marfil'),
        ('brown', 'Marrón'),
        ('orange', 'Naranja'),
        ('black', 'Negro'),
        ('red', 'Rojo'),
        ('pink', 'Rosado'),
        ('green', 'Verde'),
        ('violet', 'Violeta'),
        ('lightyellow', 'Amarillo claro'),
        ('lightblue', 'Azul claro'),
        ('lightcoral', 'Coral claro'),
        ('lightpink', 'Rosado claro'),
        ('lightsalmon', 'Salmón claro'),
        ('lightgreen', 'Verde claro'),
    ], string='Color', default='red')

    image_vehicle_color = fields.Image(string="Imagen del vehiculo",required=True)
    fleet_model_id = fields.Many2one("fleet.vehicle.model", store=True, required=True)