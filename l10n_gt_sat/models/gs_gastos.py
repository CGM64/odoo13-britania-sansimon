# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp


class GsComprasGastos(models.Model):
    _inherit = 'purchase.order'

    def aplicar_pago(self):
        proveedor = self.partner_id.id
        monto = round(self.amount_total, 2)

        self.env.context = dict(self.env.context)
        self.env.context.update({
            'default_communication': self.name,
            'default_payment_type': 'outbound',
            'default_partner_type': 'supplier',
            'default_amount': abs(self.amount_total),
            'default_partner_id': proveedor,
            'default_payment_method_id': 4,
            'default_journal_id': 56,
            'default_check_no_negociable': 1,
        })

        self.ensure_one()
        return {
            'name': 'Registrar Pago',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_invoice_form').id,
            'target': 'new',
            'context': self.env.context,
            'view_type': 'form',
            # 'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
        }
