# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

EMPRESA = 'SANSI'
SUCURSAL = 901

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_import_intelisis(self):
        self.delete_all_date()

        query = """
select top 100 a.Articulo, a.Descripcion1, a.categoria, a.grupo, a.familia, a.linea,
isnull(a.preciolista,0.0) * m.tipocambio precio, isnull(c.costopromedio,0.0) costopromedio
from art a
join mon m on m.moneda = 'Dolar'
left outer join ArtCostoSucursal c on a.articulo = c.articulo and c.empresa = '%s' AND c.sucursal = %s
--where articulo = '3116 325'
        """
        sql_server = self.env["connect.mssql"].search([],limit=1)
        query = query % (EMPRESA, SUCURSAL,)
        res = sql_server.execute_query(query)
        product_templates = []
        for row in res:
            product = {}
            product["name"] = self._format_description(row["Descripcion1"])
            product["default_code"] = row["Articulo"]
            product["categ_id"] = self._get_Categoria(row["categoria"], row["grupo"], row["familia"], row["linea"])
            product["list_price"] = row["precio"]
            product["standard_price"] = row["costopromedio"]
            product_templates.append(product)

        self.create_products(product_templates)

    def _get_Categoria(self, name, grupo_name, familia_name, linea_name):
        categoria_padre = self.env["product.category"].search([("name","=", "Saleable")])
        categoria = categoria_padre
        if name:
            categoria = self.env["product.category"].search([("name","=", name)])
            if not categoria:
                categoria = self.env["product.category"].create({
                "name": name,
                "parent_id": categoria_padre.id
                })

        if grupo_name:
            categoria_padre = categoria
            categoria = self.env["product.category"].search([("name","=", grupo_name)])
            if not categoria:
                categoria = self.env["product.category"].create({
                "name": grupo_name,
                "parent_id": categoria_padre.id
                })

        if familia_name:
            categoria_padre = categoria
            categoria = self.env["product.category"].search([("name","=", familia_name)])
            if not categoria:
                categoria = self.env["product.category"].create({
                "name": familia_name,
                "parent_id": categoria_padre.id
                })

        if linea_name:
            categoria_padre = categoria
            categoria = self.env["product.category"].search([("name","=", linea_name)])
            if not categoria:
                categoria = self.env["product.category"].create({
                "name": linea_name,
                "parent_id": categoria_padre.id
                })

        #Si trae null la categoria de intelisis entonce se le asigna la categoria padre.
        return categoria.id

    def delete_all_date(self):

        self._cr.execute('select distinct categ_id from product_template')
        ids = tuple(categ[0] for categ in self._cr.fetchall())

        self.env.cr.execute('Delete from product_template')

        if ids:
            self.env.cr.execute("Delete from product_category where id in %s and name <> 'Saleable' " , (ids,))

    def create_products(self, products):
        i = 1
        for product in products:

            find_codigo = self.search([("default_code","=",product["default_code"])])
            if not find_codigo:
                _logger.info("Creando producto %s codigo %s" % (i, product["name"]))
                self.env['product.template'].create(product)
            else:
                find_codigo["name"] = product["name"]
                _logger.info("Actualizado, producto %s codigo %s" % (i, product["name"]))
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
