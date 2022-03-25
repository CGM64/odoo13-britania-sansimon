# -*- coding:utf-8 -*-

from datetime import date, datetime, time,timedelta
from calendar import monthrange
from collections import defaultdict
from email.policy import default
from odoo import api, fields, models
from odoo.tools import date_utils

import pytz

class RestBankInherit(models.Model):
    _inherit = 'res.bank'
    _description = 'Res Bank'


    ach_quetzales = fields.Integer(string="ACH Quetzales", help="ACH Quetzales.")
    ach_dolares = fields.Integer(string="ACH Dolares", help="ACH Dolares.")

