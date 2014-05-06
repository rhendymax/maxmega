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

import time
from osv import osv, fields
from tools.translate import _
import decimal_precision as dp

class reallocated_qty(osv.osv_memory):
    _name = 'reallocated.qty'
    _description = 'Reallocated Quantity'

    def _qty_order_alllocated(self, cursor, user, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        sale_order_line_obj = self.pool.get("sale.order.line")
        product_uom_obj = self.pool.get("product.uom")
        stock_move_obj = self.pool.get("stock.move")
        sale_allocated_obj = self.pool.get("sale.allocated")
        for obj in self.browse(cursor, user, ids, context=context):
            sale_allocated = sale_allocated_obj.browse(cursor, user, obj.sale_allocated_id.id, context=context)
            sol = sale_order_line_obj.browse(cursor, user, sale_allocated.sale_line_id.id, context=context)
            qtyp = product_uom_obj._compute_qty(cursor, user, sol.product_uom.id, sol.product_uom_qty, sale_allocated.product_uom.id)
            qty_onhand_allocated = sol.qty_onhand_allocated
            sale_allocated_ids = sale_allocated_obj.browse(cursor, user, sale_allocated_obj.search(cursor, user, [('sale_line_id','=',sol.id)]), context=context)
            qty_allocated1 = sale_allocated.quantity
            qty_allocated2 = 0.00
            if sale_allocated_ids:
                for val in sale_allocated_ids:
                     qty_allocated2 = qty_allocated2 + val.quantity
            res[obj.id] = (qtyp - (qty_onhand_allocated + qty_allocated2)) + (qty_allocated1)
#            raise osv.except_osv(_('Debug !'), _(str(qtyp) + ' qty onhand allocated ' + str(qty_onhand_allocated) + ' qty allocated all ' + str(qty_allocated2) + ' qty allocated ' + str(qty_allocated1)))

        return res

    def _qty_order_unallocated(self, cursor, user, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        purchase_order_line_obj = self.pool.get("purchase.order.line")
        product_uom_obj = self.pool.get("product.uom")
        stock_move_obj = self.pool.get("stock.move")
        sale_allocated_obj = self.pool.get("sale.allocated")
        for obj in self.browse(cursor, user, ids, context=context):
            sale_allocated = sale_allocated_obj.browse(cursor, user, obj.sale_allocated_id.id, context=context)
            purchase_order_line = purchase_order_line_obj.browse(cursor, user, sale_allocated.purchase_line_id.id, context=context)
            qtyp = 0.00
            if purchase_order_line.state != 'done' and purchase_order_line.state != 'draft' and purchase_order_line.state != 'cancel':
                qtyp = product_uom_obj._compute_qty(cursor, user, purchase_order_line.product_uom.id, purchase_order_line.product_qty, sale_allocated.product_uom.id)
                sale_allocated_ids = sale_allocated_obj.browse(cursor, user, sale_allocated_obj.search(cursor, user, [('purchase_line_id','=',purchase_order_line.id),('receive','=',False)]), context=context)
                qty_allocated = 0.00
                qty_received = 0.00
                incoming_qty = 0.00
                if sale_allocated_ids:
                    for val in sale_allocated_ids:
                        qty_allocated = qty_allocated + val.quantity
                        qty_received = qty_received + val.received_qty
        #        if pol.id == 46:
        #            raise osv.except_osv(_('Debug !'), _(str(qty_allocated) + '----' + '' + '----' + ''))
    
                if qtyp > 0:
                    stock_move_ids = stock_move_obj.search(cursor, user, [('purchase_line_id','=',purchase_order_line.id),('state','=','done')])
                    if stock_move_ids:
                        for stock_move_id in stock_move_ids:
                            stock_move = stock_move_obj.browse(cursor, user, stock_move_id, context=context)
                            incoming_qty = incoming_qty + product_uom_obj._compute_qty(cursor, user, stock_move.product_uom.id, stock_move.product_qty, sale_allocated.product_uom.id)
        #        if pol.id == 46:
        #            raise osv.except_osv(_('Debug !'), _(str(qtyp) + '----' + str(qty_allocated) + '----' + str(incoming_qty)))

                qtyp = qtyp - (incoming_qty - qty_received) - qty_allocated

            res[obj.id] = qtyp
        return res

    def onchange_allocated_qty(self, cr, uid, ids, allocated_qty, spq):
        if allocated_qty > 0:
            if allocated_qty%spq != 0:
                allocated_qty= spq * ((allocated_qty-(allocated_qty%spq))/spq)
        else:
            allocated_qty = 0
        return {'value': {'allocated_qty': allocated_qty}}

    def onchange_qty_reallocated(self, cr, uid, ids ,qty_reallocated, total_qty_reallocated, spq):
        if qty_reallocated > 0:
            if qty_reallocated%spq != 0:
                qty_reallocated= spq * ((qty_reallocated-(qty_reallocated%spq))/spq)
        else:
            qty_reallocated = 0
        if qty_reallocated > total_qty_reallocated:
            warning = {'title': _('Warning'), 'message': _("the Qty for Re-Allocated cannot more than Total Qty can Re-Allocated.")}
            return {'value':{'qty_reallocated': total_qty_reallocated}, 'warning':warning}
        return {'value':{'qty_reallocated': qty_reallocated}}

    def do_reallocated(self, cr, uid, ids, context=None):
        sale_allocated_obj = self.pool.get('sale.allocated')
        sale_order_line_obj = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            sol = sale_order_line_obj.browse(cr, uid, obj.sale_allocated_id.sale_line_id.id, context=context)
            qty_onhand_allocated = sol.qty_onhand_allocated
            if obj.qty_reallocated < 1:
                if obj.qty_received > 0:
                    sale_order_line_obj.write(cr, uid, sol.id,
                        {'qty_onhand_allocated': qty_onhand_allocated + obj.qty_received}, context=context)
                sale_allocated_obj.unlink(cr, uid, obj.sale_allocated_id.id, context=context)
            else:
                if obj.qty_reallocated < obj.qty_received:
                    sale_order_line_obj.write(cr, uid, sol.id,
                        {'qty_onhand_allocated': qty_onhand_allocated + (obj.qty_received - obj.qty_reallocated)}, context=context)
                    sale_allocated_obj.write(cr, uid, obj.sale_allocated_id.id, {'quantity': obj.qty_reallocated, 'received_qty': obj.qty_reallocated}, context=context)
                else:
                    sale_allocated_obj.write(cr, uid, obj.sale_allocated_id.id, {'quantity': obj.qty_reallocated}, context=context)
        return {'type': 'ir.actions.act_window_close'}


    def _total_qty_reallocated(self, cursor, user, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        for obj in self.browse(cursor, user, ids, context=context):
            qty_order_unallocated = (obj.qty_allocated + obj.qty_order_unallocated)
            if obj.qty_order_alllocated  < qty_order_unallocated:
                res[obj.id] = obj.qty_order_alllocated
            else:
                res[obj.id] = qty_order_unallocated
        return res

    _columns = {
        'sale_allocated_id': fields.many2one('sale.allocated', 'Sale Allocated', ondelete='cascade'),
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'qty_allocated': fields.related('sale_allocated_id', 'quantity', type='float', string='Qty Allocated to this sale order', readonly=True),
        'qty_received': fields.related('sale_allocated_id', 'received_qty', type='float', string='Qty Received', readonly=True),
        'qty_order_unallocated': fields.function(_qty_order_unallocated, type='float', string='Qty Un-Allocated on this purchase order'),
        'total_qty_reallocated': fields.function(_total_qty_reallocated, type='float', string='Total Qty can Re-Allocated'),
        'qty_order_alllocated': fields.function(_qty_order_alllocated, type='float', string='Qty Sales Order can Allocated'),
        'qty_reallocated': fields.float("Qty Re-Allocated", digits_compute=dp.get_precision('Product UoM')),
    }

reallocated_qty()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
