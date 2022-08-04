# -*- coding:utf-8 -*-

from datetime import date, datetime, time
from collections import defaultdict
from odoo import api, fields, models


class TypesPayroll(models.Model):
    _name = "hr.tipos_planilla_igss"
    _description = "Tipos de planilla IGSS"

    name = fields.Char(string="Nombre de planilla", help="Nombre o descripción de planilla",required=True)

    tipo_afiliado = fields.Selection([
        ('S', 'Trabajador sin IVS'),
        ('C', 'Trabajador con IVS')],
        string='Tipo de afiliados', index=True, help="Tipo de afiliados",required=True)

    periodo_planilla = fields.Selection([
        ('M', 'Mensual'),
        ('C', 'Catorcenal'),
        ('S', 'Semanal')],
        string='Periodo de planilla', index=True, help="Periodo planilla",required=True)
   
    clase_planilla = fields.Selection([
        ('N', 'Normal'),
        ('V', 'Sin movimiento')],
        string='Clase de planilla', index=True, help="Clase de planilla",required=True)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Conversión.")

    es_prueba = fields.Boolean(string='Es prueba', default=False, help="Marque si es planilla de prueba, deje en blanco si no no lo es.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con estos datos"),
    ]