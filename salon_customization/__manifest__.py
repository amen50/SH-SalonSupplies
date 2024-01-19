{
    "name": "salon customization",
    "summary": """This module help to make sales, inventory and invoice  
        more suitable for salon
    """,
    "author": "Amen Mesfin",
    "website": "https://www.prettyneat.io/",
    "category": "Sale Management",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": ["base", "sale_management", "sale", "stock",],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/product_template.xml",
        "views/sale_order_line.xml",
        "views/product_variant.xml",
        "views/account_move.xml",
        "wizard/customer_type_selector.xml",
        "views/product_line.xml",
        "wizard/select_product.xml",
    ],
}
