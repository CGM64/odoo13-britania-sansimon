# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime


TIPOS_DE_LIBROS = [
            ('all', 'Todo'),
            ('sale', 'Ventas'),
            ('purchase', 'Compras'),
        ]

MESES = [
            ('1','Enero'),
            ('2','Febrero'),
            ('3','Marzo'),
            ('4','Abril'),
            ('5','Mayo'),
            ('6','Junio'),
            ('7','Julio'),
            ('8','Agosto'),
            ('9','Septiembre'),
            ('10','Octubre'),
            ('11','Noviembre'),
            ('12','Diciembre'),
        ]
class AccountLibroFiscalReport(models.TransientModel):
    _name = "l10n_gt_sat.librofiscal.report"
    _description = "Libro Fiscal Report"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    libro = fields.Selection(TIPOS_DE_LIBROS, string='Libro', required=True, default='all')
    tipo = fields.Selection([('detallado', 'Detallado'),
                             ('resumido', 'Resumido'),
                            ], string='Tipo', required=True, default='detallado')
    now = datetime.datetime.now()
    periodo = fields.Selection(MESES,string='Periodo',default=str(now.month))
    ejercicio = fields.Integer(string='Ejercicio', default=now.year)
    vendedor = fields.Boolean(string='Vendedor', default=True)

    #reporte de inventario
    fecha_inicio = fields.Date(string='Fecha inicio')
    fecha_fin = fields.Date(string='Fecha fin')

    def check_report(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['libro', 'tipo', 'periodo', 'ejercicio', 'company_id'])[0]
        return self.env.ref('l10n_gt_sat.action_report_librofiscal').with_context(landscape=True).report_action(self, data=data)

    def export_xls(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['libro', 'tipo', 'periodo', 'ejercicio', 'company_id', 'vendedor'])[0]
        return self.env['ir.actions.report'].search([('report_name', '=', 'l10n_gt_sat.account_librofiscal_report_xls'),
                ('report_type', '=', 'xlsx')], limit=1).report_action(self,data=data)


    def export_invetory_xls(self):
        self.ensure_one()
        data = {}
        data['form'] = self.read(['fecha_inicio', 'fecha_fin'])[0]
        return self.env['ir.actions.report'].search([('report_name', '=', 'l10n_gt_sat.account_inventario_report_xls'),
                ('report_type', '=', 'xlsx')], limit=1).report_action(self,data=data)