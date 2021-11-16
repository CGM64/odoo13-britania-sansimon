# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from datetime import datetime,date
ALMACEN_TALLER_DEFAULT = 30


class RepairType(models.Model):
    _name = "repair.type"
    _description = "Tipos de ordenes de reparación"

    name = fields.Char('Tipo de orden', required=True)
    sequence = fields.Integer(
        help='Used to order repair types in the dashboard view', default=10)
    active = fields.Boolean(string="Activo", default=True,
                            help="Activa o desctiva tipos de orden")

    state = fields.Selection([
        ('borrador', 'Borrador'),
    ], default='borrador', string='Estado', copy=False, index=True, readonly=True, help="Estado de la Conversión.")

    @api.onchange('active')
    def _update_active(self):
        return

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un registro con este nombre!"),
    ]

class repairOrder(models.Model):
    _inherit = "repair.order"

    #CALCULANDO EL COSTO PARA COLOCARLO EN EL INFORME DE REPARACIONES
    guarantee_limit = fields.Date('Warranty Expiration', default=datetime.today(),states={'draft': [('readonly', True)]})
    pricelist_id = fields.Many2one(default=lambda self:self.env.ref('britania.product_pricelist_04').id,  readonly=True)
    costo = fields.Float(string="Costo",store=True, compute="_compute_costo")

    @api.depends('pricelist_id','product_qty','fees_lines.product_id','fees_lines.product_uom_qty','fees_lines.price_unit','fees_lines.discount',)
    def _compute_costo(self):
        print("--------------------------------------------------")
        print("test de que llego al _compute_standard_price ")
        print("--------------------------------------------------")
        costo = sum(line.costo for line in self.fees_lines)
        print("Costo> ",costo)
        self.costo=costo

    #Función para asignar el costo a las órdenes que no tienen.
    def asignar_costo(self):
        print("--------------------------Entro a asignar costo--------------------------")
        repair_orders=self.env['repair.order'].search([('costo','=',0)])
        for order in repair_orders:
            print("Orden de reparacion",order.name)
            costo=0
            for line in order.fees_lines:
                costo+= (line.product_id.product_tmpl_id.standard_price) * (line.product_uom_qty)
                print('     >',line.product_id.product_tmpl_id.standard_price,' Producto ', line.product_id.name, ' Tipo', line.product_id.type)

    @api.model
    def _default_stock_location(self):
        return ALMACEN_TALLER_DEFAULT

    location_id = fields.Many2one(
        'stock.location', 'Location',
        default=_default_stock_location,
        index=True, readonly=True, required=True,
        help="This is the location where the product to repair is located.",
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    @api.model
    def _get_default(self):
        type = self.env['repair.type'].search([('active', '=', True)])
        tipos = []
        if type:
            for tipo in type:
                tipos.append(tipo.sequence)
            minimo = min(tipos)
            t = self.env['repair.type'].search([('sequence', '=', minimo)]).id
            return t
        else:
            return

    def unlink(self):
        for move in self:
            if move.name != '/' and not self._context.get('force_delete'):
                raise UserError(_("No se puede eliminar."))
            move.line_ids.unlink()
        return super(repairOrder, self).unlink()

    tipo_orden = fields.Many2one(
        'repair.type', 'Tipo de orden', index=True, default=_get_default)

    def update_detail(self, search=''):

        Fleet = request.env['fleet.vehicle']
        lista_fleet = Fleet.search(
            [('product_tmpl_id', '=', self.product_id.id)], limit=1)

        for i in self.fees_lines:
            product = request.env['fleet.model.repair']
            lista_product = product.search(
                [('model_id', '=', lista_fleet.model_id.id), ('product_id', '=', i.product_id.id)], limit=1)

            if lista_product.labour_time != 0.0:
                if i.product_uom_qty > 1.0:
                    i.product_uom_qty = i.product_uom_qty
                else:
                    i.product_uom_qty = lista_product.labour_time

    #Juan Carlos: Funcion que se copio de repair.order para poder agregar en el detalle de la factura los descuentas
    #de la orden de servicio.
    def _create_invoices(self, group=False):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        grouped_invoices_vals = {}
        repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
                                               and not repair.invoice_id
                                               and repair.invoice_method != 'none')
        for repair in repairs:
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            # Fallback on the user company as the 'company_id' is not required.
            company = repair.company_id or self.env.user.company_id

            journal = self.env['account.move'].with_context(force_company=company.id, type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

            if (partner_invoice.id, currency.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id)]

            if not group or len(current_invoices_list) == 0:
                fp_id = repair.partner_id.property_account_position_id.id or self.env['account.fiscal.position'].get_fiscal_position(repair.partner_id.id, delivery_id=repair.address_id.id)
                invoice_vals = {
                    'type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'partner_shipping_id': repair.address_id.id,
                    'currency_id': currency.id,
                    'narration': narration,
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fp_id
                }
                if partner_invoice.property_payment_term_id:
                    invoice_vals['invoice_payment_term_id'] = partner_invoice.property_payment_term_id.id
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not invoice_vals['narration']:
                    invoice_vals['narration'] = narration
                else:
                    invoice_vals['narration'] += '\n' + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                if group:
                    name = repair.name + '-' + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % operation.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': operation.product_uom_qty,
                    'tax_ids': [(6, 0, operation.tax_id.ids)],
                    'product_uom_id': operation.product_uom.id,
                    'price_unit': operation.price_unit,
                    'discount': operation.discount,
                    'product_id': operation.product_id.id,
                    'repair_line_ids': [(4, operation.id)],
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(operation.product_uom_qty * operation.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + '-' + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_('No product defined on fees.'))

                account = fee.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % fee.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': fee.product_uom_qty,
                    'tax_ids': [(6, 0, fee.tax_id.ids)],
                    'product_uom_id': fee.product_uom.id,
                    'price_unit': fee.price_unit,
                    'discount': fee.discount,
                    'product_id': fee.product_id.id,
                    'repair_fee_ids': [(4, fee.id)],
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list = []
        for invoices in grouped_invoices_vals.values():
            for invoice in invoices:
                invoices_vals_list.append(invoice)
        self.env['account.move'].with_context(default_type='out_invoice').create(invoices_vals_list)

        repairs.write({'invoiced': True})
        repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
        repairs.mapped('fees_lines').write({'invoiced': True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

class RepairFee(models.Model):
    _inherit = "repair.fee"

    amount_total = fields.Float(string="Total", compute="_get_amount_total")
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)

    costo = fields.Float(string="Costo",store=True, compute="_compute_costo")
    
    @api.depends('product_id','product_uom_qty','price_unit','discount',)
    def _compute_costo(self):
        print("---------------------------------------------")
        print("test de que llego al _compute_costo ")
        print("---------------------------------------------")
        costo=0
        for line in self:
            costo+= ((line.product_id.product_tmpl_id.standard_price) * (line.product_uom_qty)) - ((line.discount/100) * ((line.product_id.product_tmpl_id.standard_price) * (line.product_uom_qty)))
            print(line.product_id.product_tmpl_id.standard_price,' Producto ', line.product_id.name)
        print("Costo Total=", costo)
        self.costo=costo


    def _get_amount_total(self):
        for fee in self:
            fee.amount_total = fee.price_unit * fee.product_uom_qty

   #Funcion que se copio de sale.order.line para el calculo de la linea tomando en cuenta el descuento asignado
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    #Funcion que se copio de sale.order.line para el calculo de la linea tomando en cuenta el descuento asignado
    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        print("jajajajaj si llego hasta aqui, vamos a ver que pasa ------------------------------")
        print(self.name)
        if not (self.product_id and self.product_uom and
                self.repair_id.partner_id and self.repair_id.pricelist_id and
                self.repair_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.repair_id.partner_id.lang,
            partner=self.repair_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.repair_id.create_date,
            pricelist=self.repair_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.repair_id.partner_id.id, date=self.repair_id.create_date, uom=self.product_uom.id)

        price, rule_id = self.repair_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.repair_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.repair_id.pricelist_id.id)

        if new_list_price != 0:
            if self.repair_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.repair_id.pricelist_id.currency_id,
                    self.repair_id.company_id or self.env.company, self.repair_id.create_date or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                print("---------------dfdasdf-------- entro al descuento")
                print(discount)
                self.discount = discount


class RepairLine(models.Model):
    _inherit = "repair.line"

    amount_total = fields.Float(string="Total", compute="_get_amount_total")
    discount = fields.Float(string='Descuento (%)', digits='Discount', default=0.0)

    costo = fields.Float(string="Costo",store=True, compute="_compute_costo")
    
    @api.depends('product_id','product_uom_qty','price_unit','discount',)
    def _compute_costo(self):
        print("---------------------------------------------")
        print("test de que llego al _compute_costo ")
        print("---------------------------------------------")
        costo=0
        for line in self:
            costo+= ((line.product_id.product_tmpl_id.standard_price) * (line.product_uom_qty)) - ((line.discount/100) * ((line.product_id.product_tmpl_id.standard_price) * (line.product_uom_qty)))
            print(line.product_id.product_tmpl_id.standard_price,' Producto ', line.product_id.name)
        print("Costo Total=", costo)
        self.costo=costo


    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not self.type:
            self.location_id = False
            self.location_dest_id = False
        elif self.type == 'add':
            self.onchange_product_id()
            args = self.repair_id.company_id and [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_id = ALMACEN_TALLER_DEFAULT
            self.location_dest_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
        else:
            self.price_unit = 0.0
            self.tax_id = False
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
            self.location_dest_id = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id

    def _get_amount_total(self):
        for line in self:
            line.amount_total = line.price_unit * line.product_uom_qty

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id', 'repair_id.invoice_method', 'discount')
    def _compute_price_subtotal(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.repair_id.pricelist_id.currency_id, line.product_uom_qty, line.product_id, line.repair_id.partner_id)
            line.price_subtotal = taxes['total_excluded']

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id', 'tax_id', 'repair_id.invoice_method', 'discount')
    def _compute_price_total(self):
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.repair_id.pricelist_id.currency_id, line.product_uom_qty, line.product_id, line.repair_id.partner_id)
            line.price_total = taxes['total_included']

    #Funcion que se copio de sale.order.line para el calculo de la linea tomando en cuenta el descuento asignado
    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    #Funcion que se copio de sale.order.line para el calculo de la linea tomando en cuenta el descuento asignado
    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.repair_id.partner_id and self.repair_id.pricelist_id and
                self.repair_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.repair_id.partner_id.lang,
            partner=self.repair_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.repair_id.create_date,
            pricelist=self.repair_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.repair_id.partner_id.id, date=self.repair_id.create_date, uom=self.product_uom.id)

        price, rule_id = self.repair_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.repair_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.repair_id.pricelist_id.id)

        if new_list_price != 0:
            if self.repair_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.repair_id.pricelist_id.currency_id,
                    self.repair_id.company_id or self.env.company, self.repair_id.create_date or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount