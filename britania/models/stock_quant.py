from odoo import fields, models, _

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    product_default_code = fields.Char(related="product_id.default_code", string="Referencia interna")
    product_chasis = fields.Char(related="product_id.chasis")
    product_standard_price = fields.Float(related="product_tmpl_id.standard_price", string="Costo unitario")
    product_name = fields.Char(related="product_tmpl_id.name", string="Nombre")
    product_uom = fields.Many2one(related="product_tmpl_id.uom_id", string="Unidad de medida")