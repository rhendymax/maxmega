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
    'name': 'Maxmega Report Addons',
    'version': '1.1',
    "category": "Report",
    'description': """

""",
    'author': 'Yanto Chen',
    'website': 'http://www.openerp.com',
    'depends': ["account", "base_setup", "product", "analytic", "process", "board", "edi", "base", "partner_child", "product", "purchase", "sale","price_methodology","stock", "max_finance_module", "upgrade_all"],
    'init_xml': [],
    'update_xml': [
        'account_report.xml',
        'purchase_report.xml',
        'stock_report.xml',
        'sale_report.xml',
        'max_journal_entries_report.xml',
        'account/inh_invoice_view.xml',
        'sale/inh_sale_order_view.xml',
        'max_journal_entries/inh_max_journal_entries_view.xml',

    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
