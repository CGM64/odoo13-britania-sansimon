from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.onchange('structure_id')
    def _compute_employee_ids(self):
        print("#####===== _compute_employee_ids")
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.structure_id:
                domain = [
                    ('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id),
                    ('contract_ids.structure_type_id', '=', self.structure_id.type_id.id)
                ]
            wizard.employee_ids = self.env['hr.employee'].search(domain)