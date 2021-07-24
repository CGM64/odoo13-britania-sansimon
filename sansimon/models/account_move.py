# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero

import logging
import pytz

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    #Metodo heredado de la clase principal, y sobreescrito
    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.invoice_sent).write({'invoice_sent': True})
        if self.journal_id.template_print in ('template_factura'):
            return self.env.ref('sansimon.account_invoices').report_action(self)
        elif self.journal_id.template_print in ('template_ticket'):
            return self.env.ref('sansimon.account_invoices_ticket').report_action(self)
