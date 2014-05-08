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
    'name': 'Maxmega Report',
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
        'report_view.xml',
        'wizard/account_statement_report.xml',
        'wizard/param_sale_journal_zone_key_report.xml',
        'wizard/param_sale_journal_zone_report.xml',
        'wizard/param_payment_deposit_bank_report.xml',
        'wizard/param_receipt_deposit_bank_report.xml',
        'wizard/param_partner_enquiry.xml',
    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
