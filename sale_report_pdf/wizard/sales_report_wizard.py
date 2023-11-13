from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import json
import datetime
import pytz,pprint
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
    customer_boolean = fields.Boolean()
    partner_boolean = fields.Boolean()
    cat_boolean = fields.Boolean()
    # customer_id = fields.Many2one('res.partner', string='Customers')

    def print_project_report_xls(self):
        # active_record = self._context['active_id']
        # record = self.env['sale.order'].browse(active_record)
        data = {
            'ids': self.ids,
            'model': self._name,
            # 'record': record.id,
            'datefrom': self.datefrom,
            'dateto': self.datefrom,
            'customer': self.customer_id.id,
            'all_customrer': self.customer_boolean,
            'sales_rep': self.partner_select.id,   
            'all_sales_rep':self.partner_boolean
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
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # name = data['record']
        user_obj = self.env.user
        wizard_record = request.env['wizard.sales.report'].search([])[-1]
        sale_obj = request.env['sale.order']
        users_selected = []
        stages_selected = []
        vals = []
        sale_order = sale_obj.search([])
        _logger.info("Data:%s",pprint.pformat(data))
        # sale_orders = self.env['sale.order'].search([
        #     ('state', 'in', ['draft','sale', 'done'])])
        # print("sale_orders", sale_orders)
        domain = []
        SaleOrder = self.env['sale.order']
        if data['all_customrer'] is True and data['all_sales_rep'] is True:
            domain.append([])
        if data['all_customrer'] is False and data['all_sales_rep'] is True:
            domain.append([
            ('partner_id', '=', data['customer']),

            ])
        if data['all_customrer'] is True and data['all_sales_rep'] is False:
            domain.append([
            ('user_id', '=', data['sales_rep'])
            ])
        if  data['customer']  and data['sales_rep']:
            domain.append([
            ('partner_id', '=', data['customer']),
            ('user_id', '=', data['sales_rep'])
        ])
        if  data['customer']:
            domain.append([
            ('partner_id', '=', data['customer'])
        ])
        if data['sales_rep']:
            domain.append([
            ('user_id', '=', data['sales_rep'])
        ])
        _logger.info(domain)
        sale_orders = SaleOrder.search(domain[0])
        _logger.info("OOOOOOOOOO $%s",sale_orders)
        # ], order='date_order, partner_id, user_id')


        # Sort the sale_orders by date_order
        sorted_orders = sorted(sale_orders, key=lambda order: order.date_order)

        # Group the sorted_orders by calendar month, customer, and sales representative
        grouped_orders = []
        # for key, group in itertools.groupby(sorted_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.partner_id, order.user_id)):
        #     group_orders = list(group)
        #     total_amount = sum(order.amount_total for order in group_orders)
        #     grouped_orders.append((key, group_orders))

        total_amounts = defaultdict(float)

        # Iterate over the grouped orders
        for key, group in itertools.groupby(sale_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.user_id, order.partner_id)):
            group_orders = list(group)
            total_amount = str(sum(order.amount_total for order in group_orders))
            # key.appen(total_amount)
            grouped_orders.append((key, group_orders,str(total_amount)))
            # for key, group_orders, total_amount in grouped_orders:
            #     # Extract the sales representative and month from the key
            #     month, sales_rep, _ = key

            #     # Add the total_amount to the corresponding month and sales representative in the defaultdict
            #     total_amounts[(month, sales_rep)] += float(total_amount)

            # Print the summed total amounts
        summed_amounts = defaultdict(float)

        # # Iterate over the grouped orders
        # for key, group_orders, total_amount in grouped_orders:
        #     month, sales_rep, _ = key  # Extract month and sales rep from the key
        #     summed_amounts[(month, sales_rep)] += float(total_amount)  # Add the total_amount to the corresponding key

        # # Create a new list to store the grouped orders with the summed amounts
        # grouped_orders_with_sum = []

        # # Iterate over the summed amounts dictionary
        # for (month, sales_rep), total_amount in summed_amounts.items():
        #     # Find the group_orders corresponding to the sales rep and month
        #     group_orders = [group for key, group, _ in grouped_orders if key[0] == month and key[1] == sales_rep]
        #     grouped_orders_with_sum.append((key, group_orders, str(total_amount)))

        # # Print the grouped orders with the summed amounts
        # for key, group_orders, total_amount in grouped_orders_with_sum:
            # print("Key:", key)
            # print("Group Orders:", group_orders)
            # print("Total Amount:", total_amount)
            # print()
        # for (month, sales_rep), total_amount in total_amounts.items():
        # Create a dictionary to store the summed total amounts




        # summed_amounts = defaultdict(float)

        # # Iterate over the grouped orders
        # for key, group in itertools.groupby(sale_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.user_id, order.partner_id)):
        #     group_orders = list(group)
        #     total_amount = str(sum(order.amount_total for order in group_orders))
        #     sales_rep, month, _ = key

        #     # Add the total_amount to the corresponding key in the summed_amounts dictionary
        #     summed_amounts[(sales_rep, month)] += float(total_amount)

        # # Create a new list to store the grouped orders with the summed amounts
        # grouped_orders_with_sum = []

        # # Iterate over the summed amounts dictionary
        # for (sales_rep, month), total_amount in summed_amounts.items():
        #     # Find the group_orders corresponding to the sales rep and month
        #     group_orders = [group_orders for key, group_orders, _ in grouped_orders if key[0] == sales_rep and key[1] == month]
        #     grouped_orders_with_sum.append((sales_rep, month, group_orders, str(total_amount)))




        # Print the grouped orders with the summed amounts
        # for month,sales_rep, group_orders, total_amount in grouped_orders_with_sum:
        #     _logger.info("Month: %s", month)
        #     _logger.info("Sales Representative:%s", sales_rep)
        #     _logger.info("Total Amount:%s", total_amount)
        #     vals.append({
        #         'customer_id': sales_rep.name if sales_rep.name else '',
        #         'sales_rep': sales_rep.name if sales_rep.name else '',
        #         'product_cat': 'All',
        #         'total_amount': total_amount if total_amount else '',
            
        #         })
            
      
        # print("grouped_orders", grouped_orders)





        # # Create a dictionary to store the merged orders
        # merged_orders = defaultdict(list)

        # # Iterate over the grouped orders
        # for key, group in itertools.groupby(sale_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.user_id, order.partner_id)):
        #     group_orders = list(group)
        #     total_amount = str(sum(order.amount_total for order in group_orders))
        #     month, sales_rep, customer_id = key

        #     # Append the total_amount to the key
        #     key = (sales_rep, month, customer_id, total_amount)

        #     # Add the group_orders to the corresponding key in the merged_orders dictionary
        #     merged_orders[(month, sales_rep, customer_id)].extend(group_orders)

        # # Create a new list to store the merged grouped orders
        # merged_grouped_orders = []

        # # Iterate over the merged orders dictionary
        # for (month, sales_rep, customer_id), group_orders in merged_orders.items():
        #     total_amount = str(sum(order.amount_total for order in group_orders))
        #     merged_grouped_orders.append(((sales_rep, customer_id, month, total_amount), group_orders, total_amount))

        # # Print the merged grouped orders
        # for key, group_orders, total_amount in merged_grouped_orders:
        #     sales_rep, customer_id, month, _ = key
        #     vals.append({
        #         'customer_id': customer_id.id if customer_id.id else '',
        #         'sales_rep': sales_rep.name if sales_rep.name else '',
        #         'product_cat': str(month).split('-')[1],
        #         'month': str(month).split('-')[1],
        #         'total_amount': total_amount if total_amount else '',
            
        #         })
            

        # Create a dictionary to store the grouped orders
        # grouped_orders = defaultdict(lambda: defaultdict(list))

        # # Iterate over the sale_orders
        # for order in sale_orders:
        #     # Extract the relevant information from the order
        #     month = order.date_order.strftime('%Y-%m')
        #     customer = order.partner_id
        #     sales_rep = order.user_id
        #     total_amount = str(order.amount_total)

        #     # Append the total_amount to the corresponding key in the grouped_orders dictionary
        #     grouped_orders[customer][month].append(total_amount)

        # # Create a new list to store the grouped orders with total amount
        # grouped_orders_with_total = []

        # # Iterate over the grouped_orders dictionary
        # for customer, customer_orders in grouped_orders.items():
        #     for month, sales_rep_orders in customer_orders.items():
        #         # Calculate the total amount for the sales representative within the month
        #         total_amount = str(sum(float(amount) for amount in sales_rep_orders))

        #         # Append the key, group_orders, and total amount to the grouped_orders_with_total list
        #         grouped_orders_with_total.append(((customer, month), sales_rep_orders, total_amount))

        # # Print the grouped orders with the total amount
        # for key, group_orders, total_amount in grouped_orders_with_total:
        #     customer, month = key


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

        # Iterate over the grouped_orders dictionary
        for customer, customer_orders in grouped_orders.items():
            for month, month_orders in customer_orders.items():
                # Create a new dictionary to store the total amounts for different sales representatives
                total_amounts = defaultdict(list)

                for sales_rep, group_orders in month_orders.items():
                    # Calculate the total amount for the group
                    total_amount = str(sum(float(amount) for amount in group_orders))
                    total_amounts[sales_rep].append(total_amount)

                # Append the key, group_orders, and total amount to the grouped_orders_with_total list
                grouped_orders_with_total.append(((customer, month), month_orders, total_amounts))

        # Print the grouped orders with the total amount
        loop = 0
        for key, month_orders, total_amounts in grouped_orders_with_total:
            customer, month = key
            _logger.info("Month: %s", month)
            _logger.info("Customer: %s", customer)
            for sales_rep, group_orders in month_orders.items():
                _logger.info("Sales Representative:%s", sales_rep)
                _logger.info("Total Amount:%s", total_amounts[sales_rep])
                vals.append({
                    'customer_id': customer.name if customer.name else '',
                    'sales_rep': sales_rep.name if sales_rep.name else '',
                    'product_cat': 'All',
                    'month': str(month).split('-')[1] if str(month).split('-')[1] else '01',
                    'total_amount': str(total_amounts[sales_rep][0]),
                
                    })     

                
            
        # for key, orders,total in grouped_orders:
        #     month = key[0]
        #     customer = key[2].name
        #     sales_rep = key[1].name
        #     total_amount = str(total)

        #     vals.append({
        #         'customer_id': customer if customer else '',
        #         'sales_rep': sales_rep if sales_rep else '',
        #         'product_cat': 'All',
        #         'total_amount': total_amount if total_amount else '',
               
        #         })
        # {'2023-10': '2145.0', 'Total': '2145.0'}	

        # if sale_order:
        #     project_name = sale_order[0].project_id.name
        #     user = sale_order[0].project_id.user_id.name
        # else:
        #     project_name = sale_order.project_id.name
        #     user = sale_order.project_id.user_id.name
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
        
        sheet.merge_range('A1:AG1', '', format5)
        sheet.merge_range('A2:AG2', '', format5)
        sheet.merge_range('A3:AG3', '', format5)
        sheet.merge_range('A4:AG4', '', format5)
        sheet.merge_range('A5:AG5', '', format5)
        sheet.merge_range('A7:AG7', '', format5)
        sheet.merge_range('A9:AG9', '', format5)
        if data['customer']:
            client = self.env['res.partner'].sudo().search([('id','=',data['customer'])])
            sheet.merge_range('L6:O6', "Customer:   "+client.name, format5)
        else:
            sheet.merge_range('L6:O6', "Customer:   All", format5)
        
            
        if data['sales_rep']:
            sales_rep = self.env['res.users'].sudo().search([('id','=',data['sales_rep'])])
            sheet.merge_range('P6:S6', "Sales Rep:  "+sales_rep.name, format5)
        else:
            sheet.merge_range('P6:S6', "Sales Rep:  All", format5)
        
        if data['datefrom']:
            sheet.merge_range('B6:D6', "Date Period From:      "+data['datefrom'], format5)
            # sheet.merge_range('D6:E6', data['datefrom'], format3)
            # sheet.merge_range('E6:', '', format5)

        # sheet.merge_range('D8:E8', "Project Manager:", format5)
        if data['dateto']:
            # sheet.merge_range('H6:H6', "To:     ", format5)
            sheet.merge_range('E6:K6', "To:     "+data['datefrom'], format3)
            # sheet.merge_range('L6:M6', "Customer:   "+data['customer'], format5)
            # sheet.merge_range('N6:P6', "Sales Rep: ALL", format5)
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
        sheet.merge_range('AD8:AE8', "Des", format5)
        row_number = 8
        column_number = 0
        column_A = 0
        _logger.info("Val:%s",pprint.pformat(vals))
        for val in vals[1:]:
            _logger.info("YYYYYYYYYYYY first elemet %s",val)
            if val['month'] == '01':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['total_amount'], format3)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '02':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, val['total_amount'], format3)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '03':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '04':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '05':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '06':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '07':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '08':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '09':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '10':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '11':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
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
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '12':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1

            

        for val in vals:
           
            if val['month'] == '01':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['total_amount'], format3)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '02':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, val['total_amount'], format3)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '03':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '04':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '05':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '06':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '07':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '08':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '09':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '10':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
                sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, ' 0 ', format3)
                sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '11':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
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
                sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, val['total_amount'], format3)
                sheet.merge_range(row_number, column_number + 28, row_number, column_number + 29, '  0 ', format3)
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1
            if val['month'] == '12':
                sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
                sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
                sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
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
                sheet.merge_range(row_number, column_number + 29, row_number, column_number + 32, ' ', format5)
                row_number += 1

            

        for line in range(row_number,(int(row_number)+100)):
            # _logger.info("Line:%s",line)
            sheet.merge_range(line, 32, line, column_number, '', format5)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())

        output.close()

