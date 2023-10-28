from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import AccessError, UserError, ValidationError


class CustomerTypeSelector(models.TransientModel):
    _name = "customer.type.selector"
    _description = "Wizard used to make and change the customer  by bach"

    customer_type = fields.Selection([('free', 'Regular Customers'),
                                      ('discount', 'Discounted Clients')], default='discount', required=True,
                                     string='Custom Type')
    price_list = fields.Many2one(comodel_name="product.pricelist", string="price list")

    def change_type(self):
        active_ids = self.env.context.get("active_ids")
        partners = self.env['res.partner'].search([('id', 'in', active_ids)])
        for line in partners:
            line.customer_type = self.customer_type
            if self.customer_type == 'discount' and self.price_list:
                line.property_product_pricelist = self.price_list.id
            else:
                line.property_product_pricelist = 1