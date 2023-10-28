from odoo import fields, models, api


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    free_product = fields.One2many(string="Free items", comodel_name='free.product', inverse_name='product_template')


class FreeProduct(models.Model):
    _name = 'free.product'

    sale_qty = fields.Float(string="Sales quantity From")
    sale_qty_to = fields.Float(string="Sales quantity To")
    free_qty = fields.Float(string="Free quantity")
    free_product = fields.Many2one(
        'product.product',
        string='Product Variant', required=True)
    product_template = fields.Many2one('product.template', string="reveres field")
    