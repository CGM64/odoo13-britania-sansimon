# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models

class RepairReport(models.Model):
    _name = "repair.report"
    _description = "Analisis de Taller"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char('Orden', readonly=True)
    date = fields.Datetime('Fecha de la Orden', readonly=True)
    # product_id = fields.Many2one('product.product', 'Variante Producto', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)
    user_id = fields.Many2one('res.users', 'Comercial', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Producto', readonly=True)
    categ_id = fields.Many2one('product.category', 'Categoria', readonly=True)
    nbr = fields.Integer('# Línea', readonly=True)
    country_id = fields.Many2one('res.country', 'País del Cliente', readonly=True)
    # industry_id = fields.Many2one('res.partner.industry', 'Industria del Cliente', readonly=True)
    # commercial_partner_id = fields.Many2one('res.partner', 'Entidad del Cliente', readonly=True)
    order_id = fields.Many2one('repair.order', '# Orden', readonly=True)
    repair_type = fields.Many2one('repair.type', 'Tipo reparación', readonly=True)

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        ('under_repair', 'Under Repair'),
        ('ready', 'Ready to Repair'),
        ('2binvoiced', 'To be Invoiced'),
        ('invoice_except', 'Invoice Exception'),
        ('done', 'Repaired')], string='Status')

    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    product_uom_qty = fields.Float('Cantidad Ordenada', readonly=True)
    price_unit = fields.Float('Precio Unitario', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    price_subtotal = fields.Float('Total sin impuestos', readonly=True)
    costo = fields.Float('Costo', readonly=True)
    variacion = fields.Float('Margen', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            l.product_id as product_id,
            t.uom_id as product_uom,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            l.price_unit as price_unit,
            count(*) as nbr,
            s.name as name,
            s.price_subtotal as price_subtotal,
            s.create_date as date,
            s.state as state,
            s.tipo_orden as repair_type,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            extract(epoch from avg(date_trunc('day',s.create_date)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.industry_id as industry_id,
            partner.commercial_partner_id as commercial_partner_id,
            l.discount as discount,
            l.costo as costo,
            (l.price_unit * sum(l.product_uom_qty / u.factor * u2.factor)) - ((l.discount/100) *(l.price_unit *  l.product_uom_qty)) - l.costo as variacion,
            (l.price_unit *  sum(l.product_uom_qty / u.factor * u2.factor)) - ((l.discount/100) *(l.price_unit *  sum(l.product_uom_qty / u.factor * u2.factor))) as price_total,
            s.id as order_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
            repair_line l
                join repair_order s on (l.repair_id=s.id)
                join repair_fee f on (l.repair_id=f.repair_id)
                join res_partner partner on s.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom u on (u.id=l.product_uom)
                left join uom_uom u2 on (u2.id=t.uom_id)
                left join product_pricelist pp on (s.pricelist_id = pp.id)
                %s
        """ % from_clause
        
        groupby_ = """
            l.product_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.create_date,
            s.partner_id,
            s.user_id,
            s.state,
            s.tipo_orden,
            s.company_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,
            s.amount_total,
            l.costo,
            l.price_unit,
            l.product_uom_qty,
            s.id %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

class SaleOrderReportProforma(models.AbstractModel):
    _name = 'report.sale.report_saleproforma'
    _description = 'Proforma Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['repair.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'repair.order',
            'docs': docs,
            'proforma': True
        }
