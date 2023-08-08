from odoo import api, fields, models, _

class ProductProduct(models.Model):
    """Product model."""

    _inherit = 'product.product'

    costo_total = fields.Float(string="Costo total", compute="_compute_costo_total", default=0.0, search=True)

    @api.depends('standard_price', 'qty_available')
    def _compute_costo_total(self):
        for product in self:
            if product.type != 'service' and product.standard_price and product.qty_available:
                product.costo_total = product.standard_price * product.qty_available
            else:
                product.costo_total = 0.0