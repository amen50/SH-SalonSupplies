from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import json
import datetime
import pytz, pprint
import io
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import date_utils
from collections import defaultdict

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import itertools
import logging

_logger = logging.getLogger(__name__)


class SalesReportButton(models.TransientModel):
    _name = 'wizard.sales.report'

    partner_select = fields.Many2one('res.users', string='Assigned to')
    datefrom = fields.Date()
    dateto = fields.Date()
    partner_select = fields.Many2many('res.users', string='Sales Rep')
    datefrom = fields.Date()
    dateto = fields.Date()
    customer_id = fields.Many2one('res.partner', string='Customers')
    product_cat = fields.Many2one('product.category')
    customer_boolean = fields.Boolean(string='All customer', default=True)
    partner_boolean = fields.Boolean(string='All sales rep', default=True)
    date_boolean = fields.Boolean(string='All Date', default=True)
    cat_boolean = fields.Boolean()


    def print_project_report_xls(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'datefrom': self.datefrom,
            'dateto': self.dateto,
            'customer': self.customer_id.id,
            'all_customrer': self.customer_boolean,
            'all_date': self.date_boolean,
            'sales_rep': self.partner_select.id,
            'all_sales_rep': self.partner_boolean
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'wizard.sales.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Sales Report',
                     },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        print("date", data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # name = data['record']
        user_obj = self.env.user
        wizard_record = request.env['wizard.sales.report'].search([])[-1]
        sale_obj = request.env['sale.order']
        users_selected = []
        stages_selected = []
        vals = []
        sale_order = sale_obj.search([])
        domain = []
        if data.get('datefrom') and data.get('dateto') and not data.get('all_date'):
            date_from = data.get('datefrom')
            date_to = data.get('dateto')
            domain.append(('date_order', '>', date_from))
            domain.append(('date_order', '<', date_to))
        if data['customer'] and not data.get('all_customrer'):
            domain.append(
                ('partner_id', '=', data['customer'])
            )
        if data['sales_rep'] and not data.get('all_sales_rep'):
            domain.append(
                ('user_id', '=', data['sales_rep']))
        print(domain)
        sale_orders = self.env['sale.order'].search(domain)
        print("sale_orders",sale_orders)
        tot = 0
        for sale in sale_orders:
            tot +=  sale.amount_total
            print("sale.amount_total", sale.amount_total ,sale.name)
        print("tot", tot)

        # Sort the sale_orders by date_order
        sorted_orders = sorted(sale_orders, key=lambda order: order.date_order)

        # Group the sorted_orders by calendar month, customer, and sales representative
        grouped_orders = []
        total_amounts = defaultdict(float)

        # Iterate over the grouped orders
        for key, group in itertools.groupby(sale_orders, key=lambda order: (
                order.date_order.strftime('%Y-%m'), order.user_id, order.partner_id)):
            group_orders = list(group)
            total_amount = str(sum(order.amount_total for order in group_orders))
            # key.appen(total_amount)
            grouped_orders.append((key, group_orders, str(total_amount)))
            # Print the summed total amounts
        summed_amounts = defaultdict(float)

        # Create a dictionary to store the grouped orders
        grouped_orders = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # Iterate over the sale_orders
        for order in sale_orders:
            # Extract the relevant information from the order
            month = order.date_order.strftime('%Y-%m')
            customer = order.partner_id
            sales_rep = order.user_id
            total_amount = str(order.amount_total)

            # Append the total_amount to the corresponding key in the grouped_orders dictionary
            grouped_orders[customer][month][sales_rep].append(total_amount)

        # Create a new list to store the grouped orders with total amount
        grouped_orders_with_total = []
        print("grouped_orders", grouped_orders)
        # Iterate over the grouped_orders dictionary
        for customer, customer_orders in grouped_orders.items():
            print("customer", customer.name)
            for month, month_orders in customer_orders.items():
                # Create a new dictionary to store the total amounts for different sales representatives
                # print("month",month)
                total_amounts = defaultdict(list)
                # print("total_amounts", total_amounts)

                for sales_rep, group_orders in month_orders.items():
                    # Calculate the total amount for the group
                    total_amount = str(sum(float(amount) for amount in group_orders))
                    total_amounts[sales_rep].append(total_amount)
                    # print("sales_rep", sales_rep.name, total_amount)

                # Append the key, group_orders, and total amount to the grouped_orders_with_total list
                grouped_orders_with_total.append(((customer, month), month_orders, total_amounts))

        # Print the grouped orders with the total amount
        loop = 0
        for key, month_orders, total_amounts in grouped_orders_with_total:
            customer, month = key
            print("customet",customer.name)
            for sales_rep, group_orders in month_orders.items():
                        average = round((float(total_amounts[sales_rep][0])/12),2)
                        monthly = round(float(total_amounts[sales_rep][0]),2)
                        vals.append({
                            'customer_id': customer.name if customer.name else '',
                            'sales_rep': sales_rep.name if sales_rep.name else '',
                            'product_cat': 'All',
                            'month': str(month).split('-')[1] if str(month).split('-')[1] else '01',
                            'total_amount': str(monthly)+'€',
                            'average': str(average)+'€'

                        })

        sheet = workbook.add_worksheet("Sales Report")
        format1 = workbook.add_format({'font_size': 22, 'bg_color': '#D3D3D3'})
        format4 = workbook.add_format({'font_size': 22})
        format2 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format55 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format56 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7.set_align('center')
        format3.set_align('center')
        format55.set_align('right')
        format56.set_align('center')

        sheet.merge_range('A1:AG2', '', format5)
        sheet.merge_range('A3:AG3', '', format5)
        sheet.merge_range('A4:AG4', '', format5)
        sheet.merge_range('A5:AG5', '', format5)
        sheet.merge_range('A7:AG7', '', format5)
        sheet.merge_range('A9:AG9', '', format5)
        if data['customer']:
            client = self.env['res.partner'].sudo().search([('id', '=', data['customer'])])
            sheet.merge_range('L6:O6', "Customer:   " + client.name, format5)
        else:
            sheet.merge_range('L6:O6', "Customer:   All", format5)

        if data['sales_rep']:
            sales_rep = self.env['res.users'].sudo().search([('id', '=', data['sales_rep'])])
            sheet.merge_range('P6:S6', "Sales Rep:  " + sales_rep.name, format5)
        else:
            sheet.merge_range('P6:S6', "Sales Rep:  All", format5)

        if data['datefrom']:
            sheet.merge_range('B6:D6', "Date Period From:      " + data['datefrom'], format5)

        if data['dateto']:
            sheet.merge_range('E6:K6', "To:     " + data['datefrom'], format3)
            sheet.merge_range('T6:AG6', "Product Category:  ALL", format5)

        sheet.merge_range('B8:C8', 'Customer', format5)
        sheet.merge_range('D8:E8', 'Sales Rep', format5)
        sheet.merge_range('F8:G8', '', format5)
        sheet.merge_range('H8:I8', "Jan", format5)
        sheet.merge_range('J8:K8', "Feb", format5)
        sheet.merge_range('L8:M8', "March", format5)
        sheet.merge_range('N8:O8', "Apr", format5)
        sheet.merge_range('P8:Q8', "May", format5)
        sheet.merge_range('R8:S8', "Jun", format5)
        sheet.merge_range('T8:U8', "July", format5)
        sheet.merge_range('V8:W8', "Aug", format5)
        sheet.merge_range('X8:Y8', "Sep", format5)
        sheet.merge_range('Z8:AA8', "Oct", format5)
        sheet.merge_range('AB8:AC8', "Nov", format5)
        sheet.merge_range('AD8:AE8', "Dec", format5)
        sheet.merge_range('AF8:AG8', "Average", format5)
        row_number = 9
        column_number = 0
        column_A = 0
        # _logger.info("vals",vals)
        for val in vals:
            # _logger.info("oooooooooooo",val)

            if val['month'] == '01':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '02':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '03':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '04':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '05':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '06':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '07':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '08':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '09':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                
                row_number += 1
            if val['month'] == '10':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                
                row_number += 1
            if val['month'] == '11':
                print("11")
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, val['total_amount'],
                                  format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1
            if val['month'] == '12':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'],
                                  format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'],
                                  format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'],
                                  format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 30, row_number, column_number + 32,  val['average'], format3)
                row_number += 1

        for line in range(row_number, (int(row_number) + 100)):
            sheet.merge_range(line, 34, line, column_number+1, '', format5)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())

        output.close()
