# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class XLSXSReportsController(http.Controller):
    
    @http.route('/xlsx_planilla', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        print("#########============================")
        print(model)
        print(options)
        print(output_format)
        print(report_name)
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        print(report_obj)
        options = json.loads(options)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(report_obj, response)
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))