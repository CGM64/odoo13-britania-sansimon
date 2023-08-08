# -*- coding: utf-8 -*-
from odoo import http


class Prueba(http.Controller):
    @http.route('/prueba', auth='public')
    def index(self, **kw):
        return http.request.render("prueba.form_prueba")

    @http.route('/website_form_prueba/', type='http', auth='public', website=True, methods=['POST'])
    def website_form_prueba(self, **post):
        # Recuperar los datos del formulario
        name = post.get('name')
        age = int(post.get('age'))
        email = post.get('email')
        address = post.get('address')

        # Crear el registro en la tabla (modelo mi.tabla)
        mi_tabla = request.env['mi.tabla']
        mi_tabla.create({'nombre': name, 'edad': age, 'email': email, 'direccion': address})

        # Redirigir a una página de confirmación (opcional)
        return request.render("prueba.form_prueba")

        # O puedes retornar cualquier otra respuesta que desees mostrar al usuario

    @http.route('/prueba/prueba/objects/<model("prueba.prueba"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('prueba.object', {
            'object': obj
        })
