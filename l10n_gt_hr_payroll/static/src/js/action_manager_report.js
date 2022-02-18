/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import framework from 'web.framework';
import session from 'web.session';

registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        // action.data = {
        //     type: 'ir.actions.report',
        //     data: {
        //         model: 'report.l10n_gt_hr_payroll.report_planilla_excel',
        //         options: JSON.stringify({
        //             ids: action.context.active_ids,
        //             model: action.context.active_model
        //         }),
        //         output_format: 'xlsx',
        //         report_name: 'Current Stock History',
        //     },
        //     report_type: 'xlsx'
        // }
        action.data = {
            model: 'report.l10n_gt_hr_payroll.report_planilla_excel',
            options: JSON.stringify({
                ids: action.context.active_ids,
                model: "report.l10n_gt_hr_payroll.report_planilla_excel"
            }),
            output_format: 'xlsx',
            report_name: 'Current Stock History',
        }
        console.log("ACTION XLSX");
        console.log(action);
        framework.blockUI();

        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_planilla',
            data: action.data,
            success: def.resolve.bind(def),
            error: (error) => this.call('crash_manager', 'rpc_error', error),
            complete: framework.unblockUI,
        });
        return def;
    }
});
