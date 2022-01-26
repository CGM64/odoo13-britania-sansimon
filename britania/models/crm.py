# -*- coding: utf-8 -*-
from odoo import models ,fields , api
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def write(self, vals):
        if not vals.get('stage_id'):
            return super(CrmLead, self).write(vals)

        if self.user_has_groups('britania.crm_group_gerente_ventas'):
            return super(CrmLead, self).write(vals)

        if not self.user_has_groups('britania.crm_group_gerente_ventas'):
            valores = request.env['crm.stage'].search([('id', '=',vals.get('stage_id'))])

            if valores.sequence < self.stage_id.sequence:
                raise ValidationError(("No tiene permisos para realizar esta accion."))
            else:
                res = super(CrmLead, self).write(vals)
        return res
