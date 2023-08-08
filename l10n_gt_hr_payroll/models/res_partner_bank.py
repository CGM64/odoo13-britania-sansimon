from odoo import api, fields, models, _

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    account_type_id = fields.Selection([
        ('monetaria', 'Monetaria'),
        ('ahorro', 'Ahorro'),
    ], default='monetaria', string='Tipo Cuenta', copy=False, index=True, required=True, help="Tipo de Cuenta Bancaria.")
