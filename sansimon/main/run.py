# -*- coding: utf-8 -*-
import xmlrpc.client

class SanSimonOdoo(object):
    """docstring for ."""


url = 'http://localhost:8013'
db = 'Odoo13_SanSimonProd'
username = 'admin'
password = 'asdf'
url = 'http://192.168.99.100:29013'
db = 'Odoo13_SanSimon'
datos = []
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

uid = common.authenticate(db, username, password, {})

#models.execute_kw(db, uid, password, 'product.template', 'delete_all_date', [[]])
#models.execute_kw(db, uid, password, 'product.template', 'get_import_intelisis', [[]])
#models.execute_kw(db, uid, password, 'stock.inventory', 'getInventoryIntelisis', [[]])
models.execute_kw(db, uid, password, 'account.account.template', 'actualizarPlantillaID', [[]])
#models.execute_kw(db, uid, password, 'account.chart.template', 'try_loading', [[]])
