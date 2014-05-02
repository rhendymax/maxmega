# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Workflow Change at Sale Order',
    'version': '1.1',
    "category": "Sale",
    'description': """

""",
    'author': 'Yanto Chen',
    'website': 'http://www.openerp.com',
    'depends': ["account", "base_setup", "product", "analytic", "process", "board", "edi", "base", "partner_child", "product", "purchase", "sale","price_methodology","stock", "upgrade_all"],
    'init_xml': [],
    'update_xml': [
        'security/ir.model.access.csv',
        'base/res/res_security.xml',
        'base/res/inh_res_company_view.xml',
        'base/res/consigning_note_user_view.xml',
        'base/res/contact_person_view.xml',
        'base/res/inh_res_currency_view.xml',
        'base/res/res_partner_sales_zone_view.xml',
        'base/res/inh_partner_view.xml',
        'base/res/shipping_method_view.xml',
        'base/res/fob_point_view.xml',
        'wizard/so_to_po_view.xml',
        'wizard/fifo_stock_view.xml',
        'wizard/po_value_view.xml',
        'wizard/wizard_stock_view.xml',
        'allocated/wizard/reallocated_qty_view.xml',
        'allocated/sale_allocated_view.xml',
        'product/wizard/location_wizard_view.xml',
        'product/wizard/stock_fifo_view.xml',
        'product/product_location_view.xml',
        'product/max_product_categ_view.xml',
        'product/product_brand_view.xml',
        'product/inh_product_view.xml',
        'purchase/wizard/change_price_po_view.xml',
        'purchase/wizard/change_qty_po_view.xml',
        'purchase/wizard/change_effective_po_view.xml',
        'purchase/wizard/delete_po_line_wizard_view.xml',
        'purchase/wizard/allocated_so_view.xml',
        'purchase/wizard/purchase_make_incoming_view.xml',
        'purchase/purchase_sequences_view.xml',
        'purchase/inh_purchase_view.xml',
        'sale/wizard/change_qty_view.xml',
        'sale/wizard/change_price_view.xml',
        'sale/wizard/change_effective_view.xml',
        'sale/wizard/add_so_line_wizard_view.xml',
        'sale/wizard/delete_so_line_wizard_view.xml',
        'sale/wizard/onhand_reallocated_view.xml',
        'sale/wizard/allocated_po_view.xml',
        'sale/wizard/sale_make_delivery_view.xml',
        'sale/inh_sale_view.xml',
        'stock/wizard/change_reference_view.xml',
        'stock/wizard/return_picking_view.xml',
        'stock/wizard/change_warehouse_qty_view.xml',
        'stock/inh_internal_stock_view.xml',
        'stock/inh_stock_view.xml',
        'stock/int_type_view.xml',
        'account/wizard/change_journal_view.xml',
        'account/wizard/change_number_view.xml',
        'account/inh_invoice_view.xml',
    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
