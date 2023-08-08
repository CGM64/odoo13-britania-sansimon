# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    social_whatsapp = fields.Char('WhatsApp Account')
    social_waze = fields.Char('Waze Account')
    