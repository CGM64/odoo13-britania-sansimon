# -*- coding: utf-8 -*-
{
    'name': "Guatemala Payroll",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com
        123456789
        """,

    'description': """
Guatemala Payroll Salary Rules.
============================

    -Configuration of hr_payroll for Guatemala localization
    -All main contributions rules for Guatemala payslip.
    * New payslip report
    * Employee Contracts
    * Allow to configure Basic / Gross / Net Salary
    * Employee PaySlip
    * Allowance / Deduction
    * Integrated with Leaves Management
    * Medical Allowance, Travel Allowance, Child Allowance, ...
    - Payroll Advice and Report 1
    - Yearly Salary by Head and Yearly Salary by Employee Report
    """,

    'author': "Integratec",
    'website': "http://www.integratec.com.gt",
    'license': "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payroll Localization',
    'version': '1.1.2',

    # any module necessary for this one to work correctly
    'depends': ['hr_payroll_account','fel','l10n_gt_sat'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_employee_views_inherit.xml',
        'views/hr_nivel_academico_view_form.xml',
        'views/res_partner_views.xml',
        'views/res_bank_views.xml',
        'views/hr_bonos_descuentos_views.xml',
        'views/hr_work_entry_type.xml',
        'views/res_country_views.xml',
        #ministerio de trabajo
        'views/hr_employee_tipo_discapacidad.xml',
        'views/hr_employee_documento_identificacion.xml',
        'views/hr_employee_nivel_educativo.xml',
        'views/hr_employee_pueblo_pertenencia.xml',
        'views/hr_employee_comunidad_linguistica.xml',
        'views/hr_employee_ocupacion.xml',
        'wizard/rh_employee_informe_empleador.xml',
        'report/hr_employee_informe_empleador.xml',


        'report/hr_payslip_employee.xml',
        'report/hr_payslip_run_report.xml',
        'report/hr_employee_pdf_report.xml',
        # 'report/hr_payslip_run_excel_report.xml',
        'report/hr_report_views.xml',
        'report/hr_archivo_bancario.xml',

        'data/l10n_gt_hr_plan_trabajo_data.xml',
        'data/l10n_gt_hr_payroll_data.xml',
        'data/l10n_gt_hr_payroll_structure_bono14.xml',
        'data/l10n_gt_hr_payroll_structure_aguinaldo.xml',
        'data/l10n_gt_hr_payroll_structure_bono.xml',
        'data/l10n_gt_hr_payroll_structure_anticipo_data.xml',
        'data/l10n_gt_hr_payslip_input_type.xml',
        'data/ir_sequence_data.xml',
        'data/l10n_gt_hr_work_entry_type_data.xml',
        #Ministerio de trabajo
        'data/hr_employee_tipo_discapacidad_data.xml',
        'data/hr_employee_documento_identificacion_data.xml',
        'data/hr_employee_nivel_educativo_data.xml',
        'data/hr_employee_pueblo_pertenencia_data.xml',
        'data/hr_employee_comunidad_linguistica_data.xml',
        'data/hr_employee_ocupacion_data.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
           'l10n_gt_hr_payroll/static/src/js/action_manager_report.js',
        ],
    }
}
