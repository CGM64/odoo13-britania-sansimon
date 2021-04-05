from odoo import models,fields

class ContactPage(models.Model):
    _name = "model.contacto"

    departamento = fields.Selector([('departamento1','Departamento 1'),('departamento2','Departamento 2')], help="Seleccionar")
    modelo = fields.Selector([('modelo1','Modelo 1'),('modelo2','Modelo 2')], help="Seleccionar")
    medio = fields.Selector([('medio1','Medio 1'),('medio2','Medio 2')], help="Seleccionar")
