
import base64
from odoo import http
from odoo.http import serialize_exception, content_disposition

class VehiclesDealership(http.Controller):

    @http.route('/web/binary/ficha_tecnica', type='http', auth='public')
    #@serialize_exception
    def download_ficha_tecnica(self, model, field, id, filename=None, **args):
        temp_model = http.request.env[model].sudo().search([
            ("id","=",int(id))
        ])
        #filecontent = base64.b64decode(temp_model.ficha_tecnica or '')
        filecontent = base64.b64decode(temp_model[field] or '')
        if not filecontent:
            return http.request.not_found()
        else:
            if not filename:
                #filename = '%s_%s' % (model.replace('.','_'), id)
                filename = temp_model.nombre_ficha_tecnica
                return http.request.make_response(filecontent,
                            [('Content-Type', 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename))])
    pass