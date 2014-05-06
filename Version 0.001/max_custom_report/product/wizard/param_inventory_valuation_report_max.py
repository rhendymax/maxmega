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

from osv import fields, osv
import time

class param_inventory_valuation_report_max(osv.osv_memory):
    _name = 'param.inventory.valuation.report.max'
    _description = 'Param Inventory Valuation Report'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'product_from':fields.many2one('product.product', 'Supplier Part No From', required=False),
        'product_to':fields.many2one('product.product', 'Supplier Part No To', required=False),
        'location_from':fields.many2one('stock.location', 'Location From', required=False),
        'location_to':fields.many2one('stock.location', 'Location To', required=False),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d')
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.inventory.valuation.report.max'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.valuation.report.max_landscape',
            'datas': datas,
        }

param_inventory_valuation_report_max()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
