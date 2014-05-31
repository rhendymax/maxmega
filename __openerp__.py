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
    'name': 'Maxmega Security',
    'version': '1.0',
    "category": "Development",
    'description': """

""",
    'author': 'Yanto Chen',
    'website': 'http://www.openerp.com',
    'depends': [
                "account",
                "base_setup",
                "product",
                "analytic",
                "process",
                "board",
                "edi",
                "base",
                "partner_child",
                "product",
                "purchase",
                "sale",
                "price_methodology",
                "so_workflowchange",
                "stock",
                "max_custom_report",
                "max_report",
                "max_finance_module",
                "upgrade_all"],
    'init_xml': [],
    'update_xml': [
        'sale_view.xml',
        'purchase_view.xml',
        'stock_view.xml',
        'account_view.xml',
        'modification_xml.xml',
        'security/maxmega_security.xml',
        'security/ir.model.access.csv',
    ],

    'demo_xml': [],
    "auto_install": False,
    'installable': True,
    "application": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
