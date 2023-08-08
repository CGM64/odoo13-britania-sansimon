# -*- coding:utf-8 -*-
import logging

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _ # , Command # Command no existe dentro de odoo 13
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class HrBonosDescuentos(models.Model):
    _name = 'hr.bonos.descuentos'
    _description = 'Ingreso de Bonos o Descuentos'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _order = 'date desc'
    
    name = fields.Char(string='Order Reference', 
                       required=True, copy=False, readonly=True, 
                       index=True, 
                       default=lambda self: _('New'))
    date = fields.Date(
        string='Fecha', readonly=True, required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()),
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Rejected')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* Cuando no a sido aplicado a ninguna nomina \'Borrador\'
                \n* Ya fue aplicada a una nomina \'Hecho\'.
                \n* Cuando la nomina fue Cancelada \'Cancelada\'.""")
    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        store=True, readonly=False,
        default=lambda self: self.env.company,
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    bono_descuentos_line_ids = fields.One2many('hr.bonos.descuentos.line', 'bono_descuento_id', 
        string='Detalle', readonly=True, copy=True,
        states={'draft': [('readonly', False)]})
    struct_id = fields.Many2one(
        'hr.payroll.structure', string='Structure',
        store=True, readonly=False, copy=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)],},)
    
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.bonos.descuentos', sequence_date=seq_date) or _('New')
        result = super(HrBonosDescuentos, self).create(vals)
        return result
    
    def action_payslip_done(self):
        return True
    
    def action_payslip_paid(self):
        return True
    
    def action_bonos_descuentos_cancel(self):
        #if not self.env.user._is_system() and self.filtered(lambda slip: slip.state == 'done'):
        #    raise UserError(_("Cannot cancel a payslip that is done."))        
        self.write({'state': 'cancel'})
    
    def action_bonos_descuentos_draft(self):
        self.write({'state': 'draft'})
        

class HrBonosDescuentosLine(models.Model):
    _name = 'hr.bonos.descuentos.line'
    _description = 'Ingreso de Bonos o Descuentos Detalle'

    name = fields.Char(string="Description")
    company_id = fields.Many2one(
        'res.company', string='Company', copy=False, required=True,
        store=True, readonly=False,
        default=lambda self: self.env.company,
        )
    bono_descuento_id = fields.Many2one(
        'hr.bonos.descuentos', string='Bono o Descuento', readonly=True,
        copy=False, ondelete='cascade',
        domain="[('company_id', '=', company_id)]")
    contract_id = fields.Many2one(
        'hr.contract', string='Contrato', domain="[('company_id', '=', company_id)]",
        store=True, readonly=False,
       )
    amount = fields.Float(string='Monto', store=True, copy=True)
    
    _allowed_input_type_ids = fields.Many2many('hr.payslip.input.type', 
        related='bono_descuento_id.struct_id.input_line_type_ids')
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Tipo', 
        required=True)
   
    
    