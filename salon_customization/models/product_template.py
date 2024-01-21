from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    free_product = fields.One2many(string="Free items", comodel_name='free.product', inverse_name='product_template')
    product_type = fields.Selection([('can_be_added', 'Mix and Match'),
                                     ('not_add', 'can not be Mixed')], required=True,
                                    string='Free Item calculation')
    code = fields.Char(string="Code")
    sup_code = fields.Char(string="Suppler code")
    sup = fields.Char(string="Supplier")
    Shr_descr = fields.Char(string="Short Description")

    # def write(self, vals):
    #     if vals.get('product_type'):
    #         varants = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
    #         for var in varants:
    #             var.product_type = self.product_type

    #     return super(ProductTemplateInherit, self).write(vals)


class SalonProductLine(models.Model):
    _name = 'salon.product.line'

    name = fields.Char(string="name", store=True)
    free_product = fields.One2many(string="Free items", comodel_name='free.product', inverse_name='product_line')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_type = fields.Selection([('can_be_added', 'Mix and Match'),
                                     ('not_add', 'can not be Mixed')], default='can_be_added', required=True,
                                    string='Free Item calculation')
    line = fields.Many2one(string="Product Line", comodel_name='salon.product.line')
    size = fields.Char(string="Size")
    free_product = fields.One2many(string="Free items", comodel_name='free.product.attribute',
                                   inverse_name='product_product')
    code = fields.Char(string="Code")
    sup_code = fields.Char(string="Suppler code")
    sup = fields.Char(string="Supplier")
    Shr_descr = fields.Char(string="Short Description")
    retail = fields.Float(string='U.RRP .INC')

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        for line in res.product_template_attribute_value_ids:
            if line.attribute_id.is_line == 'line':
                line_new = self.env['salon.product.line'].search([('name', '=', line.name)])
                if not line_new:
                    line_new = self.env['salon.product.line'].create({'name': line.name})
                res.line = line_new.id
                res.product_tmpl_id.default_code = line_new.name
                res.default_code = line_new.name
                print("res.default_code", res.default_code)
            if line.attribute_id.is_line == 'size':
                res.size = line.name
        res.product_type = res.product_tmpl_id.product_type
        return res

    def write(self, vals):
        if vals.get('product_template_attribute_value_ids'):
             if vals['product_template_attribute_value_ids'][0][2] != 0:
                print(vals.get('product_template_attribute_value_ids'))
                for att in vals['product_template_attribute_value_ids'][0][2]:
                    print("att", att)
                    att_new = self.env['product.attribute.value'].search([('id', '=', att)])
                    print("att_new.attribute_id.is_line",att_new.attribute_id.is_line,att_new)
                    if att_new.attribute_id.is_line == 'line':
                        line_new = self.env['salon.product.line'].search([('name', '=', att_new.name)])
                        if not line_new:
                            line_new = self.env['salon.product.line'].create({'name': att_new.name})
                        self.line = line_new.id
                    if att_new.attribute_id.is_line == 'size':
                        self.size = att_new.name

        if vals.get('product_type') == 'not_add':
            arr = []
            for line in self.product_tmpl_id.free_product:
                arr.append((0, 0, {
                    'sale_qty': line.sale_qty,
                    'sale_qty_to': line.sale_qty_to,
                    'free_qty': line.free_qty
                }))
            self.free_product = arr
        return super(ProductProduct, self).write(vals)

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
    product_line = fields.Many2one('salon.product.line', string="reveres field")


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

    is_line = fields.Selection([
        ('size', 'Size'),
        ('line', 'Line')], string="Category")

    @api.onchange('is_line')
    def _is_line_salon_change(self):
        if self.is_line:
            new = self.env['product.attribute'].search([('is_line', '=', self.is_line)])
            if new:
                self.is_line = False
                raise UserError(_("There is already grouping variant. you can only one groping variant"))
