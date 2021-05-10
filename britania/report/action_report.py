
# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError

class testExport(models.Model):
    _inherit = "upd.listprice"
    _description = "Exportar lista de precios"
    
    def export_xls(self):
        return self.env.ref('britania.test_xlsx').report_action(self)