from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    free_product = fields.One2many(string="Free items", comodel_name='free.product', inverse_name='product_template')


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    product_type = fields.Selection([('can_be_added', 'can be add'),
                                     ('not_add', 'can not be add'),
                                     ('no_free', 'no free item')], default='can_be_added', required=True,
                                    string='Free Item calculation')
    line = fields.Char(string="hold line variant value")
    free_product = fields.One2many(string="Free items", comodel_name='free.product.attribute', inverse_name='product_product')

    @api.model
    def create(self, vals):
       res = super(ProductProductInherit, self).create(vals)
       for line in res.product_template_attribute_value_ids:
           if line.attribute_id.is_line:
               res.line = line.name
       return res

    @api.onchange('product_type')
    def _product_type_salon_change(self):
        print("product_type", self.product_type)
        if self.product_type != 'can_be_added':
            for line in self.free_product:
                line.unlink()


class FreeProduct(models.Model):
    _name = 'free.product'

    sale_qty = fields.Float(string="Sales quantity From")
    sale_qty_to = fields.Float(string="Sales quantity To")
    free_qty = fields.Float(string="Free quantity")
    free_product = fields.Many2one(
        'product.product',
        string='Product Variant', required=False)
    product_template = fields.Many2one('product.template', string="reveres field")


class FreeProduct(models.Model):
    _name = 'free.product.attribute'

    sale_qty = fields.Float(string="Sales quantity From")
    sale_qty_to = fields.Float(string="Sales quantity To")
    free_qty = fields.Float(string="Free quantity")
    free_product = fields.Many2one(
        'product.product',
        string='Product Variant', required=False)
    product_product = fields.Many2one('product.product', string="reveres field")


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute"

    is_line = fields.Boolean(string='is used for grouping', default=False)

    @api.onchange('is_line')
    def _is_line_salon_change(self):
        if self.is_line:
            new = self.env['product.attribute'].search([('is_line', '=', True)])
            if new:
                self.is_line = False
                raise UserError(_("There is already grouping variant. you can only one groping variant"))

