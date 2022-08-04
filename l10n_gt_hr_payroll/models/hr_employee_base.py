from odoo import fields, models

class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"
    _description = "Basic Employee"

    work_location_id = fields.Many2one('hr.work.location', 'Centro de trabajo', store=True, readonly=False,
    domain="[('address_id', '=', address_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")