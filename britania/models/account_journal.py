# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    template_invoice = fields.Selection(selection=[
            ('britania.invoice_britania', 'Plantilla Factura FEL Britania'),
            ('britania.invoice_royal', 'Plantilla Factura FEL Royal Enfield'),
        ], string='Plantilla Invoice', default='britania.invoice_britania')

    def get_tipo_dte_info(self,dte):
        if dte:
            type_dte = dict(self.sudo()._fields['tipo_documento'].selection)
            return type_dte[dte].upper()
        else:
            return ''