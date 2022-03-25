# -*- coding: utf-8 -*-
from email.policy import default
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    
    vat = fields.Char(related='address_home_id.vat', readonly=True, copy=False, string="NIT")
    cui = fields.Char(related='address_home_id.cui', readonly=True, copy=False, string="CUI")
    afiliacion_igss=fields.Char(string="Afiliación IGSS", help="Numero de afiliacion del IGSS")
    afiliacion_irtra=fields.Char(string="Afiliación IRTRA", help="Numero de afiliacion del IRTRA")
    fecha_emision_irtra = fields.Date(string="Fecha Emision", help="Fecha de Emision del carnet del IRTRA")
    fecha_cambio_irtra = fields.Date(string="Fecha Cambio", help="Fecha de Cambio del carnet del IRTRA")
    padre=fields.Char(string="Padre", help="Nombre del Padre.")
    madre=fields.Char(string="Madre", help="Nombre de la Madre.")
    conyugue=fields.Char(string="Esposa/o", help="Nombre del esposa/o.")
    
    solicitud_empleo = fields.Boolean(string="Solicitud Empleo", help="Solicitud de empleo.")
    recibo_luz = fields.Boolean(string="Recibo de Luz", help="Recibo de Luz")
    fotos = fields.Boolean(string="Fotos", help="Fotos")
    infor_net = fields.Boolean(string="Infor. Net", help="Infor. Net")
    papaleria_completa = fields.Boolean(string="Papeleria Completa", help="Papeleria Completa")
    talla_camisa = fields.Many2one('hr.talla.camisa', string='Talla de Camisa')
    contrato_ind_trab = fields.Boolean(string="Contrato Trabajo", help="Contrato Individual de Trabajo")
    lectura_reglamento = fields.Boolean(string="Lectura Reglamento", help="Lectura del Reglamento")
    acta_responsabilidad = fields.Boolean(string="Acta Responsabilidad", help="Acta de Responsabilidad")
    contrato_registrado = fields.Many2one('hr.contrato.lugar', string='Contrato Registrado')
    
    state_id = fields.Many2one('res.country.state', string='Departamento', domain="[('country_id', '=', country_id)]",)
    municipio_id = fields.Many2one('res.state.municipio', string='Municipio', domain="[('state_id', '=', state_id)]",)
    
    municipio_of_birth_id  = fields.Many2one('res.state.municipio', string='Municipio de nacimiento' )
    
    attachment_dpi = fields.Binary('DPI', copy=False, tracking=True)
    attachment_licencia = fields.Binary('Licencia', copy=False, tracking=True)
    attachment_contrato = fields.Binary('Contrato', copy=False, tracking=True)
    
    #Ministerio de Trabajo
    discapacidad_id = fields.Many2one('hr.employee.tipo.discapacidad', string='Discapacidad', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_tipo_discapacidad_01',raise_if_not_found=False))
    documento_identificacion_id = fields.Many2one('hr.employee.documento.identificacion', string='Doc. Identificacion', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_documento_identificacion_01',raise_if_not_found=False))
    nivel_academico_id = fields.Many2one('hr.nivel.academico', string='Nivel Académico')
    nivel_educativo_id = fields.Many2one('hr.employee.nivel.educativo', string='Nivel Educativo', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_nivel_educativo_01',raise_if_not_found=False))
    pueblo_pertenencia_id = fields.Many2one('hr.employee.pueblo.pertenencia', string='Pueblo de Pertenencia', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_pueblo_pertenencia_05',raise_if_not_found=False))
    comunidad_linguistica_id = fields.Many2one('hr.employee.comunidad.linguistica', string='Comunidad Linguistica', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_comunidad_linguistica_99',raise_if_not_found=False))
    ocupacion_id = fields.Many2one('hr.employee.ocupacion', string='Ocupacion', required=True,default=lambda self: self.env.ref('l10n_gt_hr_payroll.hr_employee_ocupacion_0001',raise_if_not_found=False))
    distribucion_nombres=fields.Char(string="Distribucion de Nombres", default="1,2,4,5,6", required=True, help="Campo que ayuda a definir en que columna se posiciona cada nombre en el reporte del ministerio de trabajo")
    numero_expediente_extranjero = fields.Char(string="Exp. Extranjero", help="Número de expediente del permiso de extranjero")
    
  
    def get_estado_civil(self):
        for estado in self:
            if estado.marital == 'single':
                return 1
            if estado.marital == 'married':
                return 2
        return 3
    
    def get_genero(self):
        for dato in self:
            if dato.gender == 'male':
                return 1
        return 2
    
    def get_nombres_separados(self):
        nombre = self.name.split()
        columnas = self.distribucion_nombres.split(',')
        primer_nombre = ''
        segundo_nombre = ''
        tercer_nombre = ''
        primer_apellido = ''
        segundo_apellido = ''
        apellido_casada = ''
        cantidad_nombre = range(len(columnas))
        for n in cantidad_nombre:
            if columnas[n] == '1':
                if n < len(nombre):
                    primer_nombre = primer_nombre + ' ' + nombre[n]
            if columnas[n] == '2':
                if n < len(nombre):
                    segundo_nombre = segundo_nombre + ' ' + nombre[n]
            if columnas[n] == '3':
                if n < len(nombre):
                    tercer_nombre = tercer_nombre + ' ' + nombre[n]
            if columnas[n] == '4':
                if n < len(nombre):
                    primer_apellido = primer_apellido + ' ' + nombre[n]
            if columnas[n] == '5':
                if n < len(nombre):
                    segundo_apellido = segundo_apellido + ' ' + nombre[n]
            if columnas[n] == '6':
                if n < len(nombre):
                    apellido_casada = apellido_casada + ' ' + nombre[n]
        return primer_nombre.strip(), segundo_nombre.strip(), tercer_nombre.strip(), primer_apellido.strip(), segundo_apellido.strip(), apellido_casada.strip()
class HrEmployeeTipoDiscapacidad(models.Model):
    _name = 'hr.employee.tipo.discapacidad'
    _description = 'Tipo de Discapacidad'
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Integer(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)
 
    _sql_constraints = [
        ('hr_employee_tipo_discapacidad', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]   

class HrEmployeeDocumentoIdentificacion(models.Model):
    _name = 'hr.employee.documento.identificacion'
    _description = 'Documento de Identificacion'
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Integer(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('hr_employee_documento_identificacion', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]    
class HrNivelAcademico(models.Model):
    _name = 'hr.nivel.academico'
    _description = 'Nivel Academico'
    _order = 'name'

    name = fields.Char(string='Nivel Académico', required=True, index=True)
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('nivel_academico_duplicado', 'UNIQUE (name)',
         'El dato a insertar ya existe, no puede crear un nivel académico duplicado!'),
    ]

class HrEmployeeNivelEducativo(models.Model):
    _name = 'hr.employee.nivel.educativo'
    _description = 'Nivel Educativo'
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('hr_employee_nivel_educativo', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]

class HrEmployeePuebloPertenencia(models.Model):
    _name = 'hr.employee.pueblo.pertenencia'
    _description = 'Pueblo de pertenencia '
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Integer(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('hr_employee_pueblo_pertenencia', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]

class HrEmployeeComunidadLinguistica(models.Model):
    _name = 'hr.employee.comunidad.linguistica'
    _description = 'Comunidad Linguistica'
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Integer(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('hr_employee_comunidad_linguistica', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]
class HrEmployeeOcupacion(models.Model):
    _name = 'hr.employee.ocupacion'
    _description = 'Ocupacion'
    _order = 'name'
    
    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True,
        help="Codigo utilizaado en el reporte del ministerio de trabajo.")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('hr_employee_ocupacion', 'UNIQUE (name)',
         'El nombre no puede estar duplicado!'),
    ]