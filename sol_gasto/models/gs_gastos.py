# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero


class GsGastos(models.Model):
    _name = "gs.gastos"
    _description = "Gastos"

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
            raise ValidationError(
                _('The current user has no related employee. Please, create one.'))
        return employee

    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)]  # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
            # Then, domain accepts everything
            res = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
                '|', ('company_id', '=', False), ('company_id',
                                                  '=', employee.company_id.id),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id), '|', ('company_id', '=',
                                                   False), ('company_id', '=', employee.company_id.id)]
        return res

    is_ref_editable = fields.Boolean(
        "Reference Is Editable By Current User", default='draft')

    reference = fields.Char("Referencia")
    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True,  change_default=True, tracking=True,help="Puedes buscar por Nombre, NIF, Email or Referencia.")

    name = fields.Char('Descripción', readonly=True, required=True, states={'draft': [(
        'readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})

    product_id = fields.Many2one('product.product', string='Product', readonly=True, tracking=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [
                                 ('readonly', False)]}, domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", ondelete='restrict')

    unit_amount = fields.Float("Monto", compute='_compute_from_product_id_company_id', store=True, required=True, copy=True,
                               states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, digits='Product Price')

    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True, states={'draft': [(
        'readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)

    description = fields.Text('Notas...', readonly=True, states={'draft': [(
        'readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]})

    payment_mode = fields.Selection([
        ("own_account", "Empleado reembolsa"),
        ("company_account", "Empresa")
    ], default='own_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="¿Quién reintegra?")

    date = fields.Date(readonly=True, states={
        'draft': [('readonly', False)], 
        'reported': [('readonly', False)], 
        'refused': [('readonly', False)]}, 
        default=fields.Date.context_today, string="Fecha Entrega")

    employee_id = fields.Many2one('hr.employee', compute='_compute_employee_id', string="Employee",
                                  store=True, required=True, readonly=False, tracking=True,
                                  states={'approved': [('readonly', True)], 'done': [
                                      ('readonly', True)]},
                                  default=_default_employee_id, domain=lambda self: self._get_employee_id_domain(), check_company=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={
        'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'A ENVIAR'),
        ('reported', 'ENVIADO'),
        ('approved', 'APROBADO'),
        ('done', 'PAGADO'),
        ('refused', 'RECHAZADO'),
        ('cancelled', 'CANCELADO')
    ], default='draft', string='Status', copy=False, index=True, readonly=True, help="Status of the expense.")
