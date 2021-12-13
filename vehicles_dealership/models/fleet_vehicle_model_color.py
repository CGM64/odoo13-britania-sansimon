""" Colores para cada vehiculo """

import base64
from odoo import api, fields, models
from odoo.modules.module import get_module_resource

class FleetVehicle(models.Model):

    _name = "fleet.vehicle.model.color"
    
    name = fields.Char(string="Nombre del color", placeholder="Nombre")
    #color = fields.Integer(string="Indice del color")
    color_name = fields.Selection([
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('lightgreen', 'Light Green'),
        ('lightblue', 'Light Blue'),
        ('lightyellow', 'Light Yellow'),
        ('magenta', 'Magenta'),
        ('lightcyan', 'Light Cyan'),
        ('black', 'Black'),
        ('lightpink', 'Light Pink'),
        ('brown', 'Brown'),
        ('violet', 'Violet'),
        ('lightcoral', 'Light Coral'),
        ('lightsalmon', 'Light Salmon'),
        ('lavender', 'Lavender'),
        ('wheat', 'Wheat'),
        ('ivory', 'Ivory')], string='Color', default='red')

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())
        pass

    image_vehicle_color = fields.Image(default=_default_image)
    fleet_model_id = fields.Many2one("fleet.vehicle.model", store=True)