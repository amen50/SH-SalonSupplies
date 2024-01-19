from odoo import models, fields, api


class SalesOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_discount_amount(self):
        for rec in self:
            pricelist_price = rec._get_pricelist_price()
            base_price = rec._get_pricelist_price_before_discount()
            rec.discount_amt = base_price - pricelist_price
            if rec.free_item != 0:
                rec.discount_per = round(((rec.orginal_price - rec.price_unit)/ base_price * 100),2)
                rec.discount_amt = round((rec.orginal_price - rec.price_unit),2)
            else:
                rec.discount_per = round((rec.discount_amt / base_price * 100),2)

    free_item = fields.Float(string='Free Item', store=True)
    is_free = fields.Boolean(string='is free', defualt=False)
    free_given = fields.Boolean(string='free given', defualt=False)
    orginal_price = fields.Float(string='Initial price', store=True)
    discount_per = fields.Float(string='Discount %', store=True)
    discount_amt = fields.Float(
        compute='_compute_discount_amount', string="Discount Amount")

    @api.onchange('product_uom_qty')
    def _product_uom_qty_salon_change(self):
        pass

    @api.onchange('product_id')
    def _product_id_salon_change(self):
        for rec in self:
            rec.orginal_price = rec.price_unit

    def unlink(self):
        return super(SalesOrderLine, self).unlink()

    @api.model
    def create(self, vals_list):
        res = super(SalesOrderLine, self).create(vals_list)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    custom_id = fields.Float(string='custom id', store=True)
    seq_id = fields.Float(string='custom id', store=True, default=200)
    product_group = fields.One2many('product.group', 'sale_rev', string="product group", store=True)

    @api.onchange('order_line')
    def _order_id_salon_change(self):
        """This function used to create free product """
        if self.partner_id:
            for line in self.order_line:
                line.free_given = False
                line.free_item = 0
                line.orginal_price = line._get_pricelist_price_before_discount()
            if self.partner_id.customer_type == 'free':
                for line in self.order_line:
                    if not line.free_given and line.product_id.product_type == 'can_be_added':
                        sorted_lines = sorted(self.order_line, key=lambda x: x.orginal_price, reverse=True)
                        qty = 0
                        free = 0
                        remain = 0
                        arr = []
                        for same in sorted_lines:
                            same.free_given = True
                            if same.product_id.line.id == line.product_id.line.id and same.product_id.product_type == 'can_be_added':
                                qty = same.product_uom_qty + qty
                        for free in line.product_id.line.free_product:
                            if free.sale_qty <= qty <= free.sale_qty_to:
                                free = free.free_qty
                                remain = free
                        for i in range(len(sorted_lines) - 1, -1, -1):
                            if sorted_lines[i].product_uom_qty - remain < 0:
                                remain = remain - sorted_lines[i].product_uom_qty
                                sorted_lines[i].price_unit = 0
                                sorted_lines[i].free_item = sorted_lines[i].product_uom_qty
                            else:
                                sorted_lines[i].price_unit = sorted_lines[i].orginal_price - (
                                        sorted_lines[i].orginal_price * remain / sorted_lines[i].product_uom_qty)
                                sorted_lines[i].free_item = remain
                                remain = 0
            """This function used to update the grouping in the report"""
            self.product_group = [(5, 0, 0)]
            product_quantity = {}
            arr = []
            total = 0
            for line in self.order_line:
                product_id = line.product_id.line.name
                if not product_id:
                    product_id = ' '
                quantity = line.product_uom_qty
                total = total + line.product_uom_qty
                if product_id in product_quantity:
                    product_quantity[product_id] += quantity  # Append quantity to existing list
                else:
                    product_quantity[product_id] = quantity
            for pr in product_quantity:
                arr.append({'name': pr, 'qty': product_quantity[pr]})
            arr.append({'name': "Total", 'qty': total})
            arr = [(0, 0, item) for item in arr]
            record = next((record for record in arr if record[2]['name'] == ' '), None)
            if record:
                arr.remove(record)
                arr.insert(0, record)
            self.write({'product_group': arr})

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        product_quantity = {}
        arr = []
        total = 0
        res.product_group = [(5, 0, 0)]
        for line in res.order_line:
            product_id = line.product_id.line.name
            quantity = line.product_uom_qty
            total = total + line.product_uom_qty
            if product_id in product_quantity:
                product_quantity[product_id] += quantity  # Append quantity to existing list
            else:
                product_quantity[product_id] = quantity
        for pr in product_quantity:
            arr.append({'name': pr, 'qty': product_quantity[pr]})
        arr.append({'name': "Total", 'qty': total})
        arr = [(0, 0, item) for item in arr]
        record = next((record for record in arr if record[2]['name'] == ' '), None)
        if not record:
            record = next((record for record in arr if record[2]['name'] == False), None)
        if record:
            arr.remove(record)
            arr.insert(0, record)
        res.write({'product_group': arr})
        return res

    @api.onchange('partner_id')
    def _partner_id_salon_change(self):
        pass
