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
    'name': 'Maxmega Custom Report',
    'version': '1.1',
    "category": "report",
    'description': """
Customise report
""",
    'author': 'Yanto Chen',
    'website': 'http://www.openerp.com',
    'depends': ["account", "base_setup", "product", "analytic", "process", "board", "edi", "base", "product", "purchase", "sale","so_workflowchange","stock","price_methodology", "upgrade_all"],
    'init_xml': [],
    'update_xml': [
        'menu_view.xml',
        'purchase/wizard/param_po_oustanding_report_view.xml',
        #RT 20140602
        'purchase/wizard/param_purchase_order_issued_report_view.xml',
        #
        'sale/wizard/param_allocated_sale_order_checklist_report_view.xml',
        'sale/wizard/param_sale_order_issued_report_view.xml',
        #RT 20140602
        'sale/wizard/param_so_oustanding_report_view.xml',
        'sale/wizard/param_monthly_sale_report_view.xml',
        #
        'product/wizard/param_inventory_valuation_report_view.xml',
        'product/wizard/param_inventory_valuation_report__max_view.xml',
        'product/wizard/param_inventory_ledger_details_report_view.xml',
        'product/wizard/param_incoming_report_view.xml',
        'product/wizard/param_gross_profit_by_brand_report_view.xml',
        'product/wizard/param_inventory_free_balance_report_view.xml',
        'product/wizard/param_inventory_stock_aging_report_view.xml',
        #RT 20140630
        'product/wizard/param_outgoing_report_view.xml',
        'product/wizard/param_gross_margin_product_report_view.xml',
        #
        'account/wizard/param_sales_journal_by_customer_report_view.xml',
        'account/wizard/param_purchase_journal_by_supplier_report_view.xml',
        'account/wizard/param_profit_and_lost_report_view.xml',
        'account/wizard/param_balance_sheet_report_view.xml',
        'account/wizard/param_purchase_tax_report_view.xml',
        'account/wizard/param_sales_tax_report_view.xml',
        'account/wizard/param_posted_payment_check_list_view.xml',
        'account/wizard/param_posted_receipt_check_list_view.xml',
        'account/wizard/param_monthly_pos_report_view.xml',
        'account/wizard/param_monthly_pos_with_sale_order_report_view.xml',
        'account/wizard/param_margin_sales_report_view.xml',
        'account/wizard/param_payable_ledger_report_view.xml',
        'account/wizard/param_receivable_ledger_report_view.xml',
        'account/wizard/param_payable_aging_report_view.xml',
        'account/wizard/param_receivable_aging_report_view.xml',
        # 11-06-2014
        'account/wizard/param_gl_report_view.xml',
        #03-09-2014
        'account/wizard/param_trial_balance_report_view.xml',
        'account/wizard/param_sales_journal_by_voucher_report_view.xml',
        'account/wizard/param_payment_register_by_deposit_bank_view.xml',
        'account/wizard/param_receipt_register_by_deposit_bank_view.xml',

    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
