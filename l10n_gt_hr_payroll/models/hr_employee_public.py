# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    # These are required for manual attendance
    afiliacion_igss = fields.Char(readonly=True)
    afiliacion_irtra = fields.Char(readonly=True)
    fecha_emision_irtra = fields.Char(readonly=True)
    fecha_cambio_irtra = fields.Char(readonly=True)
    padre = fields.Char(readonly=True)
    madre = fields.Char(readonly=True)
    conyugue = fields.Char(readonly=True)
    
    solicitud_empleo = fields.Char(readonly=True)
    recibo_luz = fields.Char(readonly=True)
    fotos = fields.Char(readonly=True)
    infor_net = fields.Char(readonly=True)
    papaleria_completa = fields.Char(readonly=True)
    talla_camisa = fields.Char(readonly=True)
    contrato_ind_trab = fields.Char(readonly=True)
    lectura_reglamento = fields.Char(readonly=True)
    acta_responsabilidad = fields.Char(readonly=True)
    contrato_registrado = fields.Char(readonly=True)
    
    state_id = fields.Char(readonly=True)
    municipio_id = fields.Char(readonly=True)
    
    municipio_dpi_id  = fields.Char(readonly=True)
    

    
    #Ministerio de Trabajo
    discapacidad_id = fields.Char(readonly=True)
    documento_identificacion_id = fields.Char(readonly=True)
    nivel_academico_id = fields.Char(readonly=True)
    nivel_educativo_id = fields.Char(readonly=True)
    pueblo_pertenencia_id = fields.Char(readonly=True)
    comunidad_linguistica_id = fields.Char(readonly=True)
    ocupacion_id = fields.Char(readonly=True)
    distribucion_nombres=fields.Char(readonly=True)
    numero_expediente_extranjero = fields.Char(readonly=True)
    
      
