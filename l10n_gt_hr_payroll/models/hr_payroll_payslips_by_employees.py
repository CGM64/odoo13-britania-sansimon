# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime, date, time, timedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
