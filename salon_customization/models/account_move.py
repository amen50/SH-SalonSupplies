from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    product_group = fields.One2many('product.group', 'move_rev', string="product group", store=True)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        product_quantity = {}
        arr = []
        total = 0
        self.product_group = [(5, 0, 0)]
        for line in res.invoice_line_ids:
            product_id = line.product_id.line.name
            quantity = line.quantity
            total = total + line.quantity

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

    @api.onchange('invoice_line_ids')
    def _order_id_salon_change(self):
        """This function used to update the grouping in the invoice in case of change"""
        self.product_group = [(5, 0, 0)]
        product_quantity = {}
        arr = []
        total = 0
        for line in self.invoice_line_ids:
            product_id = line.product_id.line.name
            if not product_id:
                product_id = ' '
            quantity = line.quantity
            total = total + line.quantity

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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _compute_discount_amount(self):
        for rec in self:
           pricelist_price = rec._get_pricelist_price()
           base_price = rec._get_pricelist_price_before_discount()
           rec.discount_amt = rec.base_price - rec.pricelist_price
           rec.discount = rec.discount_amt/base_price * 100

    orginal_price = fields.Float(string='Initial price', store=True)
    discount_amt = fields.Float(
        compute='_compute_discount_amount', string="Discount Amount")


class ProductGroup(models.Model):
    _name = 'product.group'

    name = fields.Char(string="line name", store=True)
    qty = fields.Float(string="quantity", store=True)
    move_rev = fields.Many2one('account.move', string="inverse field")
    sale_rev = fields.Many2one('sale.order', string="sale field")
