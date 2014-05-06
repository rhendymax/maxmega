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
    'name': 'Maxmega Reports',
    'version': '1.1',
    "category": "report",
    'description': """
Customise report
""",
    'author': 'Sunil Kumar Singh',
    'website': 'http://www.openerp.com',
    'depends': ["account", "base_setup", "product", "analytic", "process", "board", "edi", "base", "product", "purchase", "sale","so_workflowchange","stock","price_methodology", "upgrade_all"],
    'init_xml': [],
    'update_xml': [
        'menu_view.xml',
        'purchase_wizard/po_outstanding_report_view.xml',
        'purchase_wizard/booking_report_by_brand_view.xml',
        'purchase_wizard/po_issued_report_view.xml',
        'purchase_wizard/goods_received_from_supplier_report_view.xml',
        'sale_wizard/so_outstanding_report_view.xml',
        'sale_wizard/booking_report_by_salesperson_view.xml',
        'sale_wizard/credit_note_report_view.xml',
        'general_wizard/account_report_trial_balance_view.xml',
        'general_wizard/account_gl_report_view.xml',
        'general_report_view.xml',
        'ar_wizard/payment_register_by_customer_report_view.xml',
        'ar_wizard/ar_payment_register_report_view.xml',
        'ar_wizard/ar_posted_checklist_report_view.xml',
        'ap_wizard/ap_posted_checklist_report_view.xml',
        'ap_wizard/ap_payment_register_report_view.xml',
        'ap_wizard/payment_register_by_supplier_report_view.xml',
    ],
    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
