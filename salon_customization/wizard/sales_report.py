from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SalonSalesReport(models.TransientModel):
    _name = "salon.sales.report"
    _description = "Salon Sales Report Wizard"

    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")


    def button_export_pdf(self):
        print("button_export_pdf")
        # self.ensure_one()
        # report_type = "qweb-pdf"
        # return self._export(report_type)

    def button_export_xlsx(self):
        print("button_export_xlsx")
        report = self.env.ref('salon_customization.customer_sale_order_report')
        return report.report_action(self)
        # self.ensure_one()
        # report_type = "xlsx"
        # return self._export(report_type)