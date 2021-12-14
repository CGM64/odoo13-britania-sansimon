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
    cotizacion_dolar = fields.Text(string="Pagos en dólares", required=False, copy=True, default="""
    <p class="p-0 m-0">El valor total es dividido en 3 partes</p>
    <h2 class="" style="text-align: center;">3 VECES MÁS FÁCIL</h2>
    <ul>
        <li>33% De enganche inicial de:</li>
    </ul>
    <h2 class="" style="text-align: right;">$ 0,000.00</h2>
    <ul>
        <li>33% Se divide en 33 bajas cuotas
            mensuales de:</li>
    </ul>
    <h2 class="" style="text-align: right;">$ 0,000.00</h2>
    <ul>
        <li>33% Pago final de:</li>
    </ul>
    <h2 class="" style="text-align: right;">$ 0,000.00</h2>
    <p>o renueva tu motocicleta por una nueva*’</p>
    """)
    cotizacion_quetzal = fields.Text(string="Pagos en quetzales", required=False, copy=True, default="""
    <p class="p-0 m-0">El valor total es dividido en 3 partes</p>
    <h2 class="" style="text-align: center;">3 VECES MÁS FÁCIL</h2>
    <ul>
        <li>33% De enganche inicial de:</li>
    </ul>
    <h2 class="" style="text-align: right;">Q 0,000.00</h2>
    <ul>
        <li>33% Se divide en 33 bajas cuotas
            mensuales de:</li>
    </ul>
    <h2 class="" style="text-align: right;">Q 0,000.00</h2>
    <ul>
        <li>33% Pago final de:</li>
    </ul>
    <h2 class="" style="text-align: right;">Q 0,000.00</h2>
    <p>o renueva tu motocicleta por una nueva*’</p>
    """)
    ficha_tecnica = fields.Binary('Ficha Técnica', help="Archivo pdf para con la ficha técnica del vehículo", attachment=False)
    nombre_ficha_tecnica = fields.Char("Nombre archivo")
    informacion = fields.Text(string="Información general", required=False, copy=True)
    fleet_model_ids = fields.One2many("fleet.vehicle.model.color","fleet_model_id", string="Colores")
    # ================================================================================