from odoo import models, fields, api


class SalesOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_free = fields.Boolean(string="free", default=False)
    is_free_given = fields.Boolean(string="free", default=False, store=True)
    custom_id = fields.Float(string='custom id', store=True)
    updated = fields.Boolean(string='updated', store=True)

    @api.onchange('product_uom_qty')
    def _product_uom_qty_salon_change(self):
        for rec in self:
            if rec.is_free_given:
                rec.updated = True
                if rec.product_uom_qty == 0:
                    for new in rec.order_id.order_line:
                        if rec.custom_id == new.custom_id and rec.id != new.id and new.is_free:
                            rec.order_id.order_line = rec.order_id.order_line - new

    def unlink(self):
        for rec in self:
            if rec.is_free_given:
                for new in rec.order_id.order_line:
                    if rec.custom_id == new.custom_id and rec.id != new.id and new.is_free:
                        new.product_uom_qty = 0
        return super(SalesOrderLine, self).unlink()

    @api.model
    def create(self, vals_list):
        res = super(SalesOrderLine, self).create(vals_list)
        if res.sequence > 200 and not res.is_free:
            res.sequence = 200 - res.sequence
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    custom_id = fields.Float(string='custom id', store=True)
    seq_id = fields.Float(string='custom id', store=True, default=200)

    @api.onchange('order_line')
    def _order_id_salon_change(self):
        """This function used to create free product """
        if self.partner_id:
            if self.partner_id.customer_type == 'free':
                for line in self.order_line:
                    dup_qty = 0
                    if line.updated and line.product_id.product_type != 'no_free':
                        flag = False
                        for new in self.order_line:
                            if line.custom_id == new.custom_id and line.id != new.id and new.is_free:
                                self.order_line = self.order_line - new
                                if line.product_id.product_type == 'can_be_added':
                                    for dup in self.order_line:
                                        if line.product_template_id == dup.product_template_id and dup.product_id.product_type == 'can_be_added':
                                            if dup.product_template_id and not dup.is_free:
                                                dup_qty = dup_qty + dup.product_uom_qty
                                                dup.is_free_given = True
                                                dup.custom_id = self.custom_id + 1
                                            if dup.is_free:
                                                self.order_line = self.order_line - dup
                                if dup_qty == line.product_uom_qty or dup_qty == 0:
                                    if line.product_id.free_product:
                                        table = line.product_id.free_product
                                    else:
                                        table = line.product_template_id.free_product
                                    for free in table:
                                        if free.sale_qty <= line.product_uom_qty <= free.sale_qty_to:
                                            if free.free_product:
                                                new_line = self.env['sale.order.line'].new({
                                                    'product_id': line.product_id or free.free_product.id,
                                                    'product_template_id': line.product_tmpl_id.id,
                                                    'name': line.product_id.name_get()[0][1],
                                                    'product_uom_qty': free.free_qty,
                                                    'is_free': True,
                                                    'price_unit': 0,
                                                    'custom_id': self.custom_id + 1,
                                                    'sequence': self.seq_id,

                                                })
                                                self.order_line += new_line
                                                line.custom_id = self.custom_id + 1
                                                self.custom_id = self.custom_id + 2
                                                line.is_free_given = True
                                                line.updated = False
                                                flag = True
                                elif dup_qty != line.product_uom_qty:
                                    table = line.product_template_id.free_product
                                    for free in table:
                                        if free.sale_qty <= dup_qty <= free.sale_qty_to:
                                            try:
                                                name = free.free_product.name_get()[0][1]
                                            except:
                                                name = line.product_id.name_get()[0][1]
                                            if self.seq_id == 200:
                                                new_section = self.env['sale.order.line'].new({
                                                    'name': "Free Product",
                                                    'display_type': 'line_section',
                                                    'sequence': 200,
                                                })
                                                self.order_line += new_section
                                                self.seq_id = self.seq_id + 1
                                            new_line = self.env['sale.order.line'].new({
                                                'product_id': free.free_product.id or line.product_id,
                                                'product_template_id': free.free_product.product_tmpl_id.id or line.product_id.product_tmpl_id.id,
                                                'name': name,
                                                'product_uom_qty': free.free_qty,
                                                'price_unit': 0,
                                                'is_free': True,
                                                'custom_id': self.custom_id + 1,
                                                'sequence': self.seq_id,
                                            })
                                            self.order_line += new_line
                                            self.custom_id = self.custom_id + 2
                                            self.seq_id = self.seq_id + 1
                                            line.is_free_given = True
                                            line.updated = False
                                            flag = True
                            if not flag:
                                for upd in self.order_line:
                                    if line.product_template_id == upd.product_template_id and line.custom_id == upd.custom_id:
                                        upd.updated = False
                                        upd.is_free_given = False
                                        dup_qty = 0
                    if not line.is_free_given and not line.is_free and line.product_id.product_type != 'no_free':
                        if line.product_id.product_type == 'can_be_added':
                            for dup in self.order_line:
                                if line.product_template_id == dup.product_template_id and dup.product_id.product_type == 'can_be_added':
                                    if dup.product_template_id and not dup.is_free:
                                        dup_qty = dup_qty + dup.product_uom_qty
                                        dup.is_free_given = True
                                        dup.custom_id = self.custom_id + 1
                                    if dup.is_free:
                                        self.order_line = self.order_line - dup
                        if dup_qty == 0:
                            if line.product_id.free_product:
                                table = line.product_id.free_product
                            else:
                                table = line.product_template_id.free_product
                            for free in table:
                                if free.sale_qty <= line.product_uom_qty <= free.sale_qty_to:
                                    if self.seq_id == 200:
                                        new_section = self.env['sale.order.line'].new({
                                            'name': "Free Product",
                                            'display_type': 'line_section',
                                            'sequence': 200,
                                        })
                                        self.order_line += new_section
                                        self.seq_id = self.seq_id + 1
                                    new_line = self.env['sale.order.line'].new({
                                        'product_id': line.product_id or free.free_product.id,
                                        'product_template_id': line.product_id.product_tmpl_id.id,
                                        'name': line.product_id.name_get()[0][
                                            1],
                                        'product_uom_qty': free.free_qty,
                                        'is_free': True,
                                        'price_unit': 0,
                                        'custom_id': self.custom_id + 1,
                                        'sequence': self.seq_id,
                                    })
                                    self.order_line += new_line
                                    line.custom_id = self.custom_id + 1
                                    self.custom_id = self.custom_id + 2
                                    self.seq_id = self.seq_id + 1
                                    line.is_free_given = True
                        elif dup_qty != 0:
                            for free in line.product_template_id.free_product:
                                print("dup_qty", free.sale_qty, dup_qty, free.sale_qty_to)
                                if free.sale_qty <= dup_qty <= free.sale_qty_to:
                                    try:
                                        name = free.free_product.name_get()[0][1]
                                    except:
                                        name = line.product_id.name_get()[0][1]

                                    if self.seq_id == 200:
                                        new_section = self.env['sale.order.line'].new({
                                            'name': "Free Product",
                                            'display_type': 'line_section',
                                            'sequence': 200,
                                        })
                                        self.order_line += new_section
                                        self.seq_id = self.seq_id + 1
                                    new_line = self.env['sale.order.line'].new({
                                        'product_id': free.free_product.id or line.product_id,
                                        'product_template_id': free.free_product.product_tmpl_id.id or line.product_id.product_tmpl_id.id,
                                        'name': name,
                                        'product_uom_qty': free.free_qty,
                                        'is_free': True,
                                        'price_unit': 0,
                                        'custom_id': self.custom_id + 1,
                                        'sequence': self.seq_id,
                                    })
                                    self.order_line += new_line
                                    self.custom_id = self.custom_id + 2
                                    self.seq_id = self.seq_id + 1
                                    line.is_free_given = True
                                else:
                                    self.custom_id = self.custom_id + 2

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for line in res.order_line:
            if line.is_free:
                orginal = False
                for new in res.order_line:
                    if new.custom_id == line.custom_id and new.is_free_given:
                        orginal = True
                if not orginal:
                    line.product_uom_qty = 0
            elif line.sequence != 200:
                if line.sequence > 200:
                    line.sequence = 200 - line.sequence

        return res

    @api.onchange('partner_id')
    def _partner_id_salon_change(self):
        if self.partner_id.customer_type == 'discount':
            self.seq_id = 200
            self.custom_id = 0
            for line in self.order_line:
                if line.is_free_given:
                    line.is_free_given = False
                if line.updated:
                    line.updated = False
                if line.is_free:
                    self.order_line = self.order_line - line
                if line.name == "Free Product" and line.display_type == 'line_section':
                    self.order_line = self.order_line - line

        if self.partner_id.customer_type == 'free':
            self._order_id_salon_change()
