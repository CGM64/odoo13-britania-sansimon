from odoo import fields, models, _
from odoo.osv import expression

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class StockQuantityHistory(models.TransientModel):
    _name = 'stock.actual.historial'
    _description = 'Stock actual historia'

    fecha_inicial = fields.Datetime('Fecha desde',
        help="Seleccione la fecha de partida del reporte",
        default=fields.Datetime.now)
    fecha_fin = fields.Datetime('Fecha hasta',
        help="Seleccione la fecha de fin del reporte",
        default=fields.Datetime.now)

    def open_at_date(self):
        tree_view_id = self.env.ref('stock.view_stock_product_tree').id
        form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
        domain = [('type', '=', 'product')]
        product_id = self.env.context.get('product_id', False)
        product_tmpl_id = self.env.context.get('product_tmpl_id', False)
        if product_id:
            domain = expression.AND([domain, [('id', '=', product_id)]])
        elif product_tmpl_id:
            domain = expression.AND([domain, [('product_tmpl_id', '=', product_tmpl_id)]])
        # We pass `to_date` in the context so that `qty_available` will be computed across
        # moves until date.
        fecha_inicio = self.fecha_inicial.strftime(DEFAULT_SERVER_DATE_FORMAT)
        fecha_fin = self.fecha_fin.strftime(DEFAULT_SERVER_DATE_FORMAT)
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'view_mode': 'tree,form',
            'name': 'Productos desde:' + fecha_inicio + ' hasta:' + fecha_fin,
            'res_model': 'product.product',
            'domain': domain,
            'context': dict(self.env.context, from_date=self.fecha_inicial, to_date=self.fecha_fin, company_owned=self.env.company.id,search_default_stock_positivo=True),
        }
        return action