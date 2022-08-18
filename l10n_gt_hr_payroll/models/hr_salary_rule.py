# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'
    _description = "hr payroll structure"

    @api.model
    def _get_default_rule_ids(self):
        print("#####===== _get_default_rule_ids")
        return [
            (0, 0, {
                'name': 'Basic Salary',
                'sequence': 1,
                'code': 'BASIC',
                'category_id': self.env.ref('hr_payroll.BASIC').id,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = payslip.paid_amount',
            })
        ]