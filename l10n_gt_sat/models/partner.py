# -*- coding: utf-8 -*-
from odoo import models ,fields , api
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('vat')
    def _check_unique_nit(self):
        if self.vat:
            valores = request.env['res.partner'].search([('vat', '=',self.vat)])
            if self.vat == valores.vat:
                raise ValidationError(("Ya existe un contacto con este NIT"))
            else:
                return
        else:
            return