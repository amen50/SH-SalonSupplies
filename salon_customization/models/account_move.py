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
        for line in res.invoice_line_ids:
            product_id = line.product_id.line
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
            product_id = line.product_id.line
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
        print("record", record)
        print("arr", arr)
        self.write({'product_group': arr})
        print("self.product_group", self.product_group)


class ProductGroup(models.Model):
    _name = 'product.group'

    name = fields.Char(string="line name", store=True)
    qty = fields.Float(string="quantity", store=True)
    move_rev = fields.Many2one('account.move', string="inverse field")
