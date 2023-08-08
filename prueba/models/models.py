# -*- coding: utf-8 -*-

from odoo import models, fields, api

class prueba(models.Model):
    _name = 'mi.tabla'
    _description = 'Tabla para guardar los datos del formulario de prueba'

    name = fields.Char(string='Nombre', required=True)
    age = fields.Integer(string='Edad', required=True)
    email = fields.Char(string='Correo', required=True)
    address = fields.Text(string='Dirección', required=True)
