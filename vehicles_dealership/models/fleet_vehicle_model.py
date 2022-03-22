# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

"""Fleet Vehicle and products models."""

from odoo import api, fields, models
from odoo import exceptions

class FleetVehicle(models.Model):
    """Fleet Vehicle model."""

    _inherit = 'fleet.vehicle.model'
    
    is_publish = fields.Boolean(string='Publicar modelo en pagina web',help='Publicar modelo', default=False)

    # Atributos para el cotizador
    descripcion_vehiculo = fields.Text(string="Descripción del Modelo", required=False, copy=True)
    cuota_desde = fields.Char(string="Cuota desde", required=False, copy=True)
    descripcion_motor = fields.Char(string="Descripción del motor", required=False, copy=True)
    potencia_par_maximo = fields.Char(string="Potencia par máximo", required=False, copy=True)
    caja_y_transmicion = fields.Char(string="Caja y transmisión", required=False, copy=True)
    peso_motocicleta = fields.Char(string="Peso motocicleta", required=False, copy=True)
    altura_sin_espejos = fields.Char(string="Altura sin espejos", required=False, copy=True)
    altura_del_asiento = fields.Char(string="Altura del asiento", required=False, copy=True)
    ficha_tecnica = fields.Binary('Ficha Técnica', help="Archivo pdf con la ficha técnica del vehículo", attachment=False)
    nombre_ficha_tecnica = fields.Char("Nombre archivo")
    informacion = fields.Text(string="Información general", required=False, copy=True)
    fleet_model_ids = fields.One2many("fleet.vehicle.model.color","fleet_model_id", string="Colores")
    imagen_portada = fields.Image(string="Imagen de portada", help="Imagen que aparecerá como portada en el encabezado del cotizador.")
    
    # ================================================================================