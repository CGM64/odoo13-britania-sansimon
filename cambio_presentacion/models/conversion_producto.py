# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import email_split, float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.http import request

class ConversionProducto(models.Model):
    _name = "conversion.producto"
    _description = "Conversion Producto"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'

    state = fields.Selection(selection=[
        ('draft', 'Borrador'),
        ('posted', 'Convertido'),
        ('adjustment', 'Ajustado'),
        ('cancel', 'Cancelado'),
    ], string='Estado',tracking=True, required=True, readonly=True, default='draft')

    name = fields.Char(string='Number', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.uid)
    product_id = fields.Many2one('product.template', string='Producto',tracking=True,required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 domain=lambda self: [("id", "in", self.env['conversion.factor'].search([]).mapped("conversion_factor_id").ids)])
    warehouse_id = fields.Many2one('stock.warehouse', string='Bodega',required=True, domain=lambda self:[('id','=',self.env.ref('cambio_presentacion.stock_warehouse_desglose').id)],readonly=True,default=lambda self:self.env.ref('cambio_presentacion.stock_warehouse_desglose').id, states={'draft': [('readonly', False)]})

    stock_location_id = fields.Many2one('stock.location', string='Ubicación de origen', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date(string='Fecha', default=fields.Date.context_today,required=True,tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    standard_price = fields.Float(string='Costo', readonly=True, compute="compute_costo")
    amount = fields.Float(string="Cantidad", readonly=True, default=1,tracking=True, states={'draft': [('readonly', False)]})
    unidades_requeridas = fields.Float(string="Unidades requeridas", readonly=True, compute="compute_unidades_requeridas")
    amount_total = fields.Float(string="Total", readonly=True, compute="compute_total")
    total_standard_price = fields.Float(string="Costo Total", readonly=True, compute="compute_total_costo")
    total_pickings = fields.Float(compute='_compute_pickings_quantity')
    # Relacion a conversion.producto.detalle
    conversion_producto_ids = fields.One2many('conversion.producto.detalle', 'conversion_producto_line_id',
                                              'Lineas', copy=True, ondelete="cascade", store=True, readonly=True, states={'draft': [('readonly', False)]})

    factor_id = fields.Selection([
        ('bigger', 'Mas grande que la unidad de referencia.'),
        ('reference', 'Igual que la unidad de referencia.'),
        ('smaller', 'Mas pequeña que la unidad de referencia')], default='reference', tracking=True,string='Tipo Factor', readonly=True, states={'draft': [('readonly', False)]})

    _sql_constraints = [('cantidad_zero', 'CHECK (amount!=0)', 'Cantidad no puede ser cero!'),
                        ('costo_zero', 'CHECK (standard_price!=0)','Costo unitario en detalle no puede ser cero!'),
                        ]
    
    def reporte_pdf(self):
        lista_conversion=[]
        lista_detalle=[]
        for linea in self.conversion_producto_ids:
            detalle={
                'warehouse_name':self.warehouse_id.name,
                'product_name':linea.product_id.name,
                'factor_name':linea.factor_id,
                'amount':linea.amount,
                'amount_total':linea.amount_total,
            }
            lista_detalle.append(detalle)
        encabezado={
            'product_name':self.product_id.name,
            'user_name':self.user_id.name,
            'conversion_name':self.name,
            'warehouse_name':self.warehouse_id.name,
            'date':self.date.strftime('%d-%m-%Y'),
            'unidades_requeridas':self.unidades_requeridas,
            'detalle':lista_detalle,
        }
        lista_conversion.append(encabezado)
        return lista_conversion

    def contar_pickings(self):
        origin=self.name
        pickings =  request.env['stock.picking'].search([('origin', '=', origin),('state','=','done')])
        if len(pickings) > 1:
            return True
        else:
            return False

    def download_report(self):
        return self.env['ir.actions.report'].search([('report_name', '=', 'cambio_presentacion.conversion_producto_pdf_report')]).report_action(self)
   
    def _compute_pickings_quantity(self):
        origin=self.name
        consulta_stock_picking = request.env['stock.picking'].search([('origin', '=',origin),('state','=','done')])
        cantidad=len(consulta_stock_picking)
        self.total_pickings=cantidad

    def action_view_picking(self):
        origin=self.name
        proveedor_desglose = self.env.ref('cambio_presentacion.res_partner_desglose')
        action = self.env.ref('cambio_presentacion.stock_picking_window').read()[0]

        pickings =  request.env['stock.picking'].search([('origin', '=', origin),('state','=','done')])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif self.total_pickings==0:
            raise UserError(_('No hay pickings asignados a esta conversión.'))
        picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=proveedor_desglose.id)
        return action

    def action_generar_movimientos(self):
        origin=self.name
        pickings =request.env['stock.picking'].search([('origin', '=', origin),('state','=','done')])
        if len(pickings) >=2:
            # raise Warning("Esa conversión ya tiene movimientos de inventario.")
            self.write({'state': 'adjustment'})
        else:
            self.generar_recepcion_in()
            self.generar_recepcion_out()
            self.write({'state': 'adjustment'})

    def generar_recepcion_out(self):
        proveedor_desglose = self.env.ref('cambio_presentacion.res_partner_desglose')
        returns = self.env['stock.picking'].search([])
        origin=self.name

        producto=self.env['product.product'].search([('product_tmpl_id','=',self.product_id.id)])  
        datos={
                'partner_id': proveedor_desglose.id,
                'origin': origin,
                'picking_type_id': self.env['stock.picking.type'].search([('warehouse_id','=',self.warehouse_id.id),('code','=','outgoing'),('sequence_code','=','DES-OUT')]).id,
                'location_id': self.stock_location_id.id, 
                'location_dest_id': proveedor_desglose.property_stock_supplier.id,
                'move_ids_without_package': [(0, 0, {
                    'product_id': producto,
                    'product_uom_qty': self.unidades_requeridas,
                    'quantity_done': self.unidades_requeridas,
                    'name': self.product_id.name,
                    'product_uom': self.product_id.uom_id.id,
                    'description_picking': str(self.product_id.id) +' '+ self.product_id.name,
                    'price_unit': self.standard_price,
                                                    })],
                }
        returns.create(datos)
        
        consulta_stock_picking = request.env['stock.picking'].search([('origin', '=', origin),('state','=','draft')])
        self.env['stock.picking'].search([('id', '=', consulta_stock_picking.id)]).action_confirm()    
        self.env['stock.picking'].search([('id', '=', consulta_stock_picking.id)]).button_validate() 
        message = _("Este movimiento fue generado a partir de la Conversión: <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>") % (self.id, self.name)
        consulta_stock_picking.message_post(subject='Conversion', body=message)

    def generar_recepcion_in(self):
        proveedor_desglose = self.env.ref('cambio_presentacion.res_partner_desglose')
        returns = self.env['stock.picking'].search([])
        origin=self.name
        refund_line_list = []

        for line in self.conversion_producto_ids:
            producto=self.env['product.product'].search([('product_tmpl_id','=',line.product_id.id)])  
            refund_line_list.append((0, 0, {
                'product_id': producto,
                'product_uom_qty': line.amount,
                'quantity_done': line.amount,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'description_picking': str(line.product_id.id) +' '+ line.product_id.name,
                'price_unit': line.unit_amount
                }))
 
        returns.create({
                'partner_id': proveedor_desglose.id,
                'origin': origin,
                'picking_type_id': self.env['stock.picking.type'].search([('warehouse_id','=',self.warehouse_id.id),('code','=','incoming'),('sequence_code','=','DES-IN')]).id,
                'location_dest_id': self.stock_location_id.id,
                'location_id': proveedor_desglose.property_stock_supplier.id,
                'move_ids_without_package': refund_line_list,
                })
        
        consulta_stock_picking = request.env['stock.picking'].search([('origin', '=', origin),('state','=','draft')])
        self.env['stock.picking'].search([('id', '=', consulta_stock_picking.id)]).action_confirm()    
        self.env['stock.picking'].search([('id', '=', consulta_stock_picking.id)]).button_validate()    
        message = _("Este movimiento fue generado a partir de la Conversión: <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a>") % (self.id, self.name)
        consulta_stock_picking.message_post(subject='Conversion', body=message)
   
    @api.onchange('warehouse_id')
    def set_stock_location_id(self):
        self.stock_location_id = self.warehouse_id.lot_stock_id.id
    
    def _picking_type_id(self):
        consulta_stock_picking_type = request.env['stock.picking.type'].search(
                [('sequence_code', '=', 'IN'), ('warehouse_id', '=', self.warehouse_id.id)])
        picking_type_id=consulta_stock_picking_type.id
        return  picking_type_id

    def _validar_cantidad(self):
        cont =0
        suma=[]
        lista_factor_diferente=['bigger','reference']
        cantidad_requerida=0
        for rec in self.conversion_producto_ids:
            cont+=1
            factor=rec.factor_id
            cantidad=rec.amount
            if factor in lista_factor_diferente:
                suma.append(cantidad)
            if factor=="smaller":
                valor_factor=rec.factor_amount
                suma.append(cantidad/valor_factor)
        if cont>0:
            cantidad_requerida=sum(suma)/cont 
        return cantidad_requerida

    def _proveedor_data(self):
        proveedor_desglose = self.env.ref('cambio_presentacion.res_partner_desglose').id
        return proveedor_desglose

    def button_approved(self):
        qry_existencias=self._qry_productos_con_existencia((self.product_id.id,),self.stock_location_id.id)
        existencia=0
        cont =0 
        cantidad=self._validar_cantidad()

        consulta_stock_picking = request.env['stock.picking'].search([('origin', '=',self.name),('state','=','done')])
        total_pickings=len(consulta_stock_picking)

        for val in qry_existencias:
            existencia=val['quantity']
        
        for rec in self.conversion_producto_ids:
            cont+=1

        if existencia < self.unidades_requeridas and total_pickings ==0:
            raise Warning("Bodega sin existencia suficiente.")
        elif cont ==0:
            raise Warning("El detalle no contienen ningún elemento.")
        elif cantidad != self.amount:
            raise Warning("La cantidad del encabezado con el detalle no son iguales.")
        else:
            self.write({'state': 'posted'})

    def button_draft(self):
        self.write({'state': 'draft'})

    def button_cancel(self):
        self.write({'state': 'cancel'})

    def _qry_productos_con_existencia(self,product_ids,stock_location_id):
        query = """
                SELECT T.ID, T.NAME,
                Q.ID,Q.PRODUCT_ID,Q.LOCATION_ID,Q.QUANTITY,
                L.ID,L.COMPLETE_NAME,L.LOCATION_ID  FROM PRODUCT_TEMPLATE T
                INNER JOIN STOCK_QUANT Q ON Q.PRODUCT_ID=T.ID
                INNER JOIN STOCK_LOCATION L ON L.ID=Q.LOCATION_ID
                WHERE T.ID IN %s AND Q.QUANTITY>0 AND L.ID=%s
                """
        self.env.cr.execute(query, (product_ids,stock_location_id,))
        query_result = self.env.cr.dictfetchall()
        return query_result

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'conversion.producto') or 'New'
            result = super(ConversionProducto, self).create(vals)
            return result

    @api.onchange('product_id')
    def compute_costo(self):
        consulta_costo = request.env['product.template'].search(
            [('id', '=', self.product_id.id)])
        costo = 0
        for producto in consulta_costo:
            costo = producto.standard_price
        self.standard_price = costo

    @api.onchange('conversion_producto_ids')
    def compute_total_costo(self):
        for rec in self:
            total = 0
            for line in rec.conversion_producto_ids:
                total += line.amount_total
            self.total_standard_price = total

    @api.onchange('conversion_producto_ids')
    def compute_total(self):
        for rec in self:
            total = 0
            for line in rec.conversion_producto_ids:
                total += line.amount_total
            self.amount_total = total

    @api.onchange('conversion_producto_ids')
    def compute_unidades_requeridas(self):
        suma_linea = []
        factor_diferente = ['bigger', 'reference']
        for line in self.conversion_producto_ids:
            if line.factor_id in factor_diferente:
                suma_linea.append(line.factor_amount*line.amount)
            elif line.factor_id == 'smaller':
                suma_linea.append(line.amount/line.factor_amount)
        self.unidades_requeridas = sum(suma_linea)

    @api.onchange('product_id', 'amount', 'factor_id')
    def llenar_detalle_conversion(self):

        head_factor_tipo = self.factor_id
        head_costo = self.standard_price
        head_factor_tipo = self.factor_id
        head_cantidad = self.amount

        if head_factor_tipo != False:
            consulta_factor = request.env['conversion.factor'].search(
                [('conversion_factor_id', '=', self.product_id.id), 
                ('factor_id', '=', self.factor_id),
                ('product_id', '!=', self.product_id.id),])
        else:
            consulta_factor = request.env['conversion.factor'].search(
                [('conversion_factor_id', '=', self.product_id.id),
                ('product_id', '!=', self.product_id.id),])

        detalle = self
        for linea in detalle:
            linea.conversion_producto_ids = [(5, 0, 0)]

        sum_total_detalle = []
        lista_lineas_diferentes = ['bigger', 'reference']
        for dato in consulta_factor:
            linea_producto = dato.product_id.id
            linea_factor_tipo = dato.factor_id
            linea_factor = dato.factor_amount
            linea_costo_unitario = head_costo*linea_factor
            linea_cantidad = head_cantidad
            linea_total_linea = linea_costo_unitario*linea_cantidad

            diccionario_lineas = {'product_id': linea_producto,
                                  'factor_id': linea_factor_tipo,
                                  'standard_price': head_costo,
                                  'factor_amount': linea_factor, }
            if head_factor_tipo in lista_lineas_diferentes or linea_factor_tipo in lista_lineas_diferentes:
                diccionario_lineas['amount'] = linea_cantidad
                diccionario_lineas['unit_amount'] = linea_costo_unitario
                diccionario_lineas['amount_total'] = linea_total_linea
                sum_total_detalle.append(diccionario_lineas['amount_total'])

            if head_factor_tipo == "smaller" or linea_factor_tipo == 'smaller':
                diccionario_lineas['amount'] = linea_factor*linea_cantidad
                diccionario_lineas['unit_amount'] = head_costo/linea_factor
                diccionario_lineas['amount_total'] = (
                    linea_factor*linea_cantidad)*(head_costo/linea_factor)
                sum_total_detalle.append(diccionario_lineas['amount_total'])

            self.conversion_producto_ids = [(0, 0, diccionario_lineas)]

        sumatoria_detalle = sum(sum_total_detalle)
        self.amount_total = sumatoria_detalle
        self.total_standard_price = sumatoria_detalle

class ConversionProductoDetalle(models.Model):
    _name = "conversion.producto.detalle"
    _description = "Conversion Producto Detalle"

    conversion_producto_line_id = fields.Many2one(
        'conversion.producto', string='Linea Detalle', ondelete="cascade", store=True)

    product_id = fields.Many2one('product.template', string='Producto',required=True,
                                 domain=lambda self: [("id", "in", self.env['conversion.factor'].search([]).mapped("product_id").ids)])

    amount = fields.Float(string="Cantidad",required=True,)
    factor_id = fields.Char(string="Factor Tipo",required=True,)
    factor_amount = fields.Float(string="Valor Factor",required=True,)
    standard_price = fields.Float(string="Costo",required=True,)
    unit_amount = fields.Float(string="Costo Unitario",required=True,)
    amount_total = fields.Float(string="Costo Total",required=True,)

    _sql_constraints = [('detalle_cantidad_zero', 'CHECK (amount!=0)', 'Cantidad en detalle no puede ser cero!'),
                        ('detalle_costo_unitario_zero', 'CHECK (unit_amount!=0)','Costo unitario en detalle no puede ser cero!'),
                        ('detalle_costo_total_zero', 'CHECK (amount_total!=0)', 'Costo total en detalle no puede ser cero!'), ]

    @api.onchange('amount', 'unit_amount')
    def onchange_total_linea_detalle(self):
        for line in self:
            amount = line.amount
            unit_amount = line.unit_amount
            total = amount*unit_amount
        self.amount_total = total


