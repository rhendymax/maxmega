# -*- encoding: utf-8 -*-
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

import decimal_precision as dp
from osv import fields, osv
from tools.translate import _
import netsvc
import math
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from operator import itemgetter

class total_qty_so(osv.osv_memory):
    _name = "total.qty.so"
    _description = "Total Qty From Which SO View"

    def sales_order_get(self, cr, uid, product_id, context=None):
        sale_order_obj = self.pool.get("sale.order")
        sale_order_line_obj = self.pool.get("sale.order.line")
        
        pp_qry = (product_id and (("sol.product_id = " + str(product_id) + " ") or "sol.product_id IN " \
                              + str(tuple(product_id)) + " ")) or "sol.product_id IN (0) "
        
        result1 = []
        cr.execute(
            "SELECT so.name as so_name, (sol.product_uom_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.state = 'done' And sm.sale_line_id = sol.id group by sm.product_id),0)) as oustanding " \
                    "FROM sale_order_line sol " \
                    "INNER JOIN sale_order so on sol.order_id = so.id " \
                    "WHERE " + (pp_qry) + \
                    " And so.state IN ('progress') " \
                    " And (sol.product_uom_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id group by sm.product_id),0)) > 0 " \
                    " order by so.name")

        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                result1.append({
                             'so_id' : t['so_name'],
                             'qty_so' : t['oustanding'],
                             })
        
        return result1

    def default_get(self, cr, uid, fields, context=None):
        product_product_obj = self.pool.get('product.product')
        result1 = []
        if context is None:
            context = {}
        res = super(total_qty_so, self).default_get(cr, uid, fields, context=context)
        for product in product_product_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            result1 = self.sales_order_get(cr, uid, product.id, context=context)
        if 'lines_ids' in fields:
            res.update({'lines_ids': result1})
        return res
# 
    _columns = {
        'lines_ids' : fields.one2many('product.so.lines', 'wizard_id', 'Sales Order Lines', readonly=True),
    }

total_qty_so()

class product_so_lines(osv.osv_memory):
    _name = 'product.so.lines'
    _description = 'Sales Order Lines'
 
    _columns = {
        'wizard_id': fields.many2one('total.qty.so', 'wizard id', ondelete='cascade'),
#         'so_id': fields.many2one('sale.order', 'SO', readonly=True),
        'so_id': fields.char('SO No', size=64, readonly=True),
        'qty_so': fields.float('QTY', readonly=True),
    }
 
product_so_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
