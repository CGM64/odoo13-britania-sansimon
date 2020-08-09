# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_import_intelisis(self):
        query = """
select top 100 Articulo, Descripcion1 from art
        """
        sql_server = self.env["connect.mssql"].search([],limit=1)
        res = sql_server.execute_query(query)
        product_templates = []
        for row in res:
            product = {}
            product["name"] = self._format_description(row["Descripcion1"])
            product["default_code"] = row["Articulo"]
            product_templates.append(product)

        self.create_products(product_templates)

    def create_products(self, products):
        i = 1
        for product in products:
            print("Creando producto %s codigo %s" % (i, product["name"]))
            self.env['product.template'].create(product)
            i+=1

    def _format_description(self, name):

        name = self._format_description_sincomillas(name)

        return name

    def _format_description_sincomillas(self, name):
        if name is None or name == '':
            return "Sin Definicion"
        if name[0] == '"':
            name = name[1:]
        if name[len(name) - 1:len(name)] == '"':
            name = name[ 1:len(name) - 1]
        return name
