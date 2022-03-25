def export_xls(self):
    context = self._context
    datas = {'ids': context.get('active_ids', [])}
    datas['model'] = self.env.context.get('active_model', 'ir.ui.menu')
    return self.env['ir.actions.report'].search([('report_name', '=', 'l10n_gt_hr_payroll.planilla_excel'),
                                                 ('report_type', '=', 'xlsx')], limit=1).report_action(self,data=datas)