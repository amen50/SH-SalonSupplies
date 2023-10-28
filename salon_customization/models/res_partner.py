from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_type = fields.Selection([('free', 'Regular Customers'),
                                      ('discount', 'Discounted Clients')], default='free', required=True,
                                     string='Custom Type')
    total_compute = fields.Float(compute="_total_sales_sum", string="compute", search=False)
    total_sales = fields.Float(string="Total sales", store=True)
    total_invoice = fields.Float(string="Total Invoice", store=True)
    total_paid = fields.Float(string="Total Paid Invoice", store=True)

    def _total_sales_sum(self):
        """this method is a compute method that will help to caluclate and store the sales my customer"""
        print("total sum")
        for rec in self:
            domain = [('partner_id', '=', rec.id)]
            domain_invoice = [('partner_id', '=', rec.id),('move_type', '=', 'out_invoice')]
            sales = self.env['sale.order'].search(domain)
            invoice = self.env['account.move'].search(domain_invoice)
            total_sales = 0
            total_paid = 0
            total_invoice = 0
            for res in sales:
              total_sales += res.amount_total
            for invoice in invoice:
                total_invoice = total_invoice + int(invoice.tax_totals['amount_total'])
                if invoice.payment_state == 'paid' or invoice.payment_state == 'partial':
                    total_paid = total_paid + (int(invoice.tax_totals['amount_total']) - invoice.amount_residual)
            self.total_sales = int(total_sales)
            self.total_compute = int(total_sales)
            self.total_invoice = total_invoice
            self.total_paid = total_paid
        return
