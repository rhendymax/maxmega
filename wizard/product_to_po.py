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

class total_qty_po(osv.osv_memory):
    _name = "total.qty.po"
    _description = "Total Qty From Which PO View"

    def purchase_order_get(self, cr, uid, product_id, context=None):
        purchase_order_obj = self.pool.get("purchase.order")
        purchase_order_line_obj = self.pool.get("purchase.order.line")
        pp_qry = (product_id and (("pol.product_id = " + str(product_id) + " ") or "pol.product_id IN " \
                              + str(tuple(product_id)) + " ")) or "pol.product_id IN (0) "
        
        print product_id
        result1 = []
        cr.execute(
            "SELECT po.name as po_name, (pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.state = 'done' And sm.purchase_line_id = pol.id group by sm.product_id),0)) as oustanding " \
                    "FROM purchase_order_line pol " \
                    "INNER JOIN purchase_order po on pol.order_id = po.id " \
                    "WHERE " + (pp_qry) + \
                    " And po.state IN ('approved') " \
                    " And (pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) > 0 " \
                    " order by po.name")

        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                result1.append({
                             'po_id' : t['po_name'],
                             'qty_po' : t['oustanding'],
                             })
        return result1

    def default_get(self, cr, uid, fields, context=None):
        product_product_obj = self.pool.get('product.product')
        result1 = []
        if context is None:
            context = {}
        res = super(total_qty_po, self).default_get(cr, uid, fields, context=context)
        for product in product_product_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            result1 = self.purchase_order_get(cr, uid, product.id, context=context)
        if 'lines_ids' in fields:
            res.update({'lines_ids': result1})
        return res
# 
    _columns = {
        'lines_ids' : fields.one2many('product.po.lines', 'wizard_id', 'Purchase Order Lines', readonly=True),
    }

total_qty_po()

class product_po_lines(osv.osv_memory):
    _name = 'product.po.lines'
    _description = 'Purchases Order Lines'
 
    _columns = {
#         'po_no': fields.char('PO No', size=64, readonly=True),
        'wizard_id': fields.many2one('total.qty.po', 'wizard id', ondelete='cascade'),
#         'po_id': fields.many2one('purchase.order', 'PO', readonly=True),
        'po_id': fields.char('PO No', size=64, readonly=True),
        'qty_po': fields.float('QTY', readonly=True),
    }
 
product_po_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
