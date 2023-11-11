from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTypeSelector(models.TransientModel):
    _name = "product.type.selector"
    _description = "Wizard used to make and change product the   by batch"

    customer_type = fields.Selection([('can_be_added', 'can be add'),
                                     ('not_add', 'can not be add'),
                                     ('no_free', 'no free item')], default='can_be_added', required=True,
                                    string='Free Item calculation')

    def change_type(self):
        active_ids = self.env.context.get("active_ids")
        partners = self.env['product.product'].search([('id', 'in', active_ids)])
        for line in partners:
            line.product_type = self.customer_type