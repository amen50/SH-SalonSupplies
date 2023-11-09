
{
    'name': 'Sales Analysis Report',
    'version': '16.0.1.0.0',
    "category": "Sales",
    'author': '',
    'website': "",
    'depends': ['base', 'sale'],
    'license': 'AGPL-3',
    'data': ['security/ir.model.access.csv',
             'wizard/sales_report_wizard_view.xml',
             ],
    'assets': {
            'web.assets_backend': [
                'sale_report_pdf/static/src/js/action_manager.js',
            ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
