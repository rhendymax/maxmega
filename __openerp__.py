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
    'name': 'Price Methodology at Product',
    'version': '1.1',
    "category": "Product",
    'description': """
add price methodology at product master.
""",
    'author': 'Yanto Chen',
    'website': 'http://www.openerp.com',
    'depends': ["account", "base_setup", "product", "analytic", "process", "board", "edi", "base", "partner_child", "product", "purchase", "sale", "upgrade_all","stock"],
    'init_xml': [],
    'update_xml': [
        'product/product_supplier_view.xml',
        'product/product_customer_view.xml',
        'product/inh_product_view.xml',
        'purchase/wizard/change_eta_view.xml',
        'purchase/wizard/change_etd_view.xml',
        'purchase/inh_purchase_view.xml',
        'sale/wizard/change_cod_view.xml',
        'sale/wizard/change_confirm_view.xml',
        'sale/inh_sale_view.xml',
        'security/ir.model.access.csv',
    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
