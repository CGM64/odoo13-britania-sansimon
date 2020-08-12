# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

EMPRESA = 'SANSI'
SUCURSAL = 901

class Inventory(models.Model):
    _inherit = 'stock.inventory'

    def getInventoryIntelisis(self):
        query = "spInvval"
        params = ( '023674 32','1056 653','(TODOS)','Costo Promedio','12/31/2020',EMPRESA)
        sql_server = self.env["connect.mssql"].search([],limit=1)
        #query = query % (EMPRESA,)
        res = sql_server.execute_proc(query, params)
        product_templates = []
        for row in res:
            print(row)
        return True
