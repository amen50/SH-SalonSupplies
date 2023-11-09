from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import json
import datetime
import pytz
import io
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import itertools


class SalesReportButton(models.TransientModel):
    _name = 'wizard.sales.report'

    partner_select = fields.Many2many('res.users', string='Assigned to')
    stage_select = fields.Many2many('project.task.type', string="Stage")
    # partner_select = fields.Many2many('res.users', string='Sales Rep')
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

        sale_orders = self.env['sale.order'].search([
            ('state', 'in', ['draft','sale', 'done'])])
        print("sale_orders", sale_orders)
        # ], order='date_order, partner_id, user_id')


        # Sort the sale_orders by date_order
        sorted_orders = sorted(sale_orders, key=lambda order: order.date_order)

        # Group the sorted_orders by calendar month, customer, and sales representative
        grouped_orders = []
        # for key, group in itertools.groupby(sorted_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.partner_id, order.user_id)):
        #     group_orders = list(group)
        #     total_amount = sum(order.amount_total for order in group_orders)
        #     grouped_orders.append((key, group_orders))

        for key, group in itertools.groupby(sale_orders, key=lambda order: (order.date_order.strftime('%Y-%m'), order.user_id, order.partner_id)):
            group_orders = list(group)
            total_amount = str(sum(order.amount_total for order in group_orders))
            # key.appen(total_amount)
            grouped_orders.append((key, group_orders,str(total_amount)))
        print("grouped_orders", grouped_orders)

            
        for key, orders,total in grouped_orders:
            month = key[0]
            customer = key[1].name
            sales_rep = key[2].name
            total_amount = str(total)

            vals.append({
                'customer_id': customer if customer else '',
                'sales_rep': sales_rep if sales_rep else '',
                'product_cat': 'All',
                'total_amount': total_amount if total_amount else '',
               
                })
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
        if data['datefrom']:
            sheet.merge_range('B6:D6', "Date Period From:      "+data['datefrom'], format5)
            # sheet.merge_range('D6:E6', data['datefrom'], format3)
            # sheet.merge_range('E6:', '', format5)

        # sheet.merge_range('D8:E8', "Project Manager:", format5)
        if data['dateto']:
            # sheet.merge_range('H6:H6', "To:     ", format5)
            sheet.merge_range('E6:K6', "To:     "+data['datefrom'], format3)
            sheet.merge_range('L6:M6', "Customer: ALL", format5)
            sheet.merge_range('N6:P6', "Sales Rep: ALL", format5)
            sheet.merge_range('Q6:AG6', "Product Category:  ALL", format5)

        



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
        for val in vals:
            # _logger.info("Val:%s",val)
            # _logger.info("Val:%s",row_number)
            # sheet.merge_range(row_number, column_number, row_number, column_number, val['user_id'], format3)
            # sheet.merge_range(row_number, 0, row_number, 1, ' ', format5)
            # sheet.merge_range(row_number, 1, row_number, 2, val['user_id'], format5)
            # sheet.merge_range(row_number, 3, row_number, 4, val['name'], format5)
            # sheet.merge_range(row_number, 6, row_number, column_number, val['name'], format5)
            # sheet.merge_range(row_number, 1 + 1, row_number, column_number, '', format5)
            # sheet.merge_range(row_number, 1 + 2, row_number, column_number, '', format5)
            # sheet.merge_range(row_number, column_number, row_number, column_number, val['user_id'], format3)
            # sheet.merge_range(row_number, column_number , row_number, column_number +1, val['user_id'], format3)
            # sheet.merge_range(row_number, column_number  +1, row_number, column_number +1, val['user_id'], format5)
            # sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, '', format5)
            # sheet.merge_range(row_number, column_number  +2, row_number, column_number +4, val['name'], format5)
            # sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['name'], format5)
            sheet.merge_range(row_number, column_number + 0, row_number, column_number + 1, val['customer_id'], format55)
            sheet.merge_range(row_number, column_number + 2, row_number, column_number + 3, val['sales_rep'], format55)
            sheet.merge_range(row_number, column_number + 4, row_number, column_number + 5, val['product_cat'], format56)
            sheet.merge_range(row_number, column_number + 6, row_number, column_number + 7, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 8, row_number, column_number + 9, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 10, row_number, column_number + 11, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 12, row_number, column_number + 13, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 14, row_number, column_number + 15, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 16, row_number, column_number + 17, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 18, row_number, column_number + 19, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 20, row_number, column_number + 21, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 22, row_number, column_number + 23, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 24, row_number, column_number + 25, val['total_amount'], format3)
            sheet.merge_range(row_number, column_number + 26, row_number, column_number + 27, val['total_amount'], format3)
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

