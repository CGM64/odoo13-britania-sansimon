# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

#Tipos de planilla para ser asignados en el informe del IGSS
class HrTipoPlanilla(models.Model):
    _name = 'hr.tipo.planilla'
    _description = 'Tipos de Planilla'
    _order = 'code'

    name = fields.Char(string='Descripcion', required=True, help="2. Nombre o descripción del tipo de planilla (Planilla del IGSS)")
    code = fields.Integer(string='Codigo', required=True, help="1. Identificación de Tipo de planilla (Planilla del IGSS)")
    active = fields.Boolean(default=True)
    tipo_afiliados = fields.Selection([
        ('C', 'Trabajador Con IVS'),
        ('S', 'Trabajador Sin IVS'), 
        ], string="Tipo de Afiliados", default='C', required=True, help="3. Tipo de afiliados, (S)Trabajador Sin IVS         (C) Trabajador Con IVS")
    periodo_planilla = fields.Selection([
        ('M', 'Mensual'), 
        ('C', 'Catorcenal'), 
        ('S', 'Semanal'),
        ], string="Periodo de Planilla", default='M', required=True, help="4. Periodo de planilla, (M)Mensual (C)Catorcenal (S)Semanal. (Planilla del IGSS)")
    
    country_id = fields.Many2one('res.country', string='Pais', required=True, readonly=True, default=lambda self: self.env.ref('base.gt'))
    departamento_id = fields.Many2one('res.country.state', string='Departamento', required=True, domain="[('country_id','=', country_id)]")
    codigo_departamento = fields.Char(string='Codigo IGSS', related='departamento_id.code_igss', readonly=True)
    code_actividad_economica = fields.Many2one('hr.actividad.economica.iggs', string="Actividad Económica", help="Código de actividad económica.", required=True)
    clase_planilla = fields.Selection([
        ('N', 'Normal'), 
        ('V', 'Sin movimiento'), 
        ], string="Clase de Planilla", default='N', required=True, help="7. Clase de Planilla,        (N) Normal,   (V) Sin movimiento")
    
   

    _sql_constraints = [
        ('_unique', 'unique (name)', "El nombre no puede estar duplicado"),
    ]