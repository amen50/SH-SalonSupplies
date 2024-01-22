from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTypeSelector(models.TransientModel):
    _name = "product.type.selector"
    _description = "Wizard used to make and change product the   by batch"

    change_type = fields.Selection([('product_type', 'Product Type'),
                                    ('tax_type', 'Tax type')], default='product_type', required=True,
                                   string='Type of change')
    customer_type = fields.Selection([('can_be_added', 'can be mixed'),
                                      ('not_add', 'can not be mixed')], default='can_be_added', required=True,
                                     string='Free Item calculation')
    taxes_id = fields.Many2many(comodel_name='account.tax', string="Customer Taxes",
                                domain=[('type_tax_use', '=', 'sale')],
                                help="Taxes used for deposits")
    lst_price = fields.Float(string="Sales price")

    def change_type_fun(self):
        active_ids = self.env.context.get("active_ids")
        partners = self.env['product.product'].search([('id', 'in', active_ids)])
        for line in partners:
            if self.change_type == 'product_type':
                line.product_type = self.customer_type
            elif self.change_type == 'tax_type':
                line.taxes_id = self.taxes_id.ids
            elif self.change_type == 'sale_price':
                line.lst_price = self.lst_price
