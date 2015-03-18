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

class sale_allocated(osv.osv):
    _name = 'sale.allocated'
    _description = 'Sale Allocated'
    _rec_name = 'sale_line_id'

    def _qty_arrived(self, cr, uid, ids, name, arg, context=None):
#        raise osv.except_osv(_('Debug!'), _('ya'))
        if not ids: return {}
        res = {}
        sale_allocated_obj = self.pool.get("sale.allocated")
        stock_move_obj = self.pool.get("stock.move")
        uom_obj = self.pool.get("product.uom")
        
        for obj in self.browse(cr, uid, ids, context=context):
            purchase_line_id = obj.purchase_line_id.id
            id = obj.id
            qty_allocated = 0.00
            qty_arrive = 0.00

            sale_allocated_ids = sale_allocated_obj.browse(cr, uid,
                sale_allocated_obj.search(cr, uid, [('purchase_line_id', '=', purchase_line_id)], order='id ASC'),
                 context=context)
#            raise osv.except_osv(_('Debug!'), _(str(purchase_line_id)))
            if sale_allocated_ids:

                purchase_order_line_id = 0
                for val in sale_allocated_ids:
                    qty_allocated = qty_allocated + val.quantity
                    if val.purchase_line_id.id != purchase_order_line_id:
                        purchase_order_line_id = val.purchase_line_id.id
                        stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id', '=', purchase_order_line_id), ('state', '=', 'done')])
                        if stock_move_ids:
#                            raise osv.except_osv(_('Debug!'), _(str(purchase_order_line_id) + '----' + str(qty_allocated) + '----' + str(stock_move_ids)))
                            for stock_move_id in stock_move_ids:
                                stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                                qty_arrive = qty_arrive + uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, obj.product_uom.id)

                    if val.id == id:
                        break
#                raise osv.except_osv(_('Debug!'), _(str(qty_arrive) + '----' + str(qty_allocated) + '----' + ''))
                if qty_arrive > qty_allocated:
                    qty_arrive = qty_allocated

            res[obj.id] = obj.quantity - (qty_allocated - qty_arrive)
        return res

    def _receive(self, cursor, user, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        for obj in self.browse(cursor, user, ids, context=context):
            receive = False
            if obj.quantity - obj.received_qty == 0:
                receive = True
            res[obj.id] = receive
        return res

    def unallocated(self, cr, uid, ids, context=None):
        sale_allocated = self.browse(cr, uid, ids[0], context=context)
        sale_order_line_obj = self.pool.get("sale.order.line")
        if sale_allocated.received_qty > 0:
            sol = sale_order_line_obj.browse(cr, uid, sale_allocated.sale_line_id.id, context=context)
            qty_onhand_allocated = sol.qty_onhand_allocated
            sale_order_line_obj.write(cr, uid, sol.id,
                {'qty_onhand_allocated': qty_onhand_allocated + sale_allocated.received_qty}, context=context)
        return self.unlink(cr, uid, ids, context=context)

    def _prepare_reallocated_qty(self, cr, uid, sale_allocated_id, product, context=None):

        reallocated_qty_vals = {
            'spq': product.spq,
            'sale_allocated_id': sale_allocated_id,
            }
        return reallocated_qty_vals

    def reallocated(self, cr, uid, ids, context=None):
#        raise osv.except_osv(
#            _('Debug!'),
#            _('Xxxx.'))
        for o in self.browse(cr, uid, ids):
            if context is None: context = {}
            context = dict(context, active_ids=ids, active_model=self._name)

            reallocated_qty_obj = self.pool.get("reallocated.qty")

            reallocated_qty_vals = self._prepare_reallocated_qty(cr, uid, o.id, o.product_id, context=context)
            reallocated_qty_id = reallocated_qty_obj.create(cr, uid, reallocated_qty_vals, context=context)

            return {
                    'name':_("Reallocated Quantity"),
                    'view_mode': 'form',
                    'view_id': False,
                    'view_type': 'form',
                    'res_model': 'reallocated.qty',
                    'res_id': reallocated_qty_id,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]',
                    'context': context,
                    }
        return True

    _columns = {
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Order Line'),
        'purchase_line_id': fields.many2one('purchase.order.line', 'Purchase Order Line'),
        'sale_id': fields.related(
            'sale_line_id',
            'order_id',
            type='many2one',
            relation='sale.order',
            string='Sale Order',
            store=False),
        'order_id': fields.related(
            'purchase_line_id',
            'order_id',
            type='many2one',
            relation='purchase.order',
            string='Purchase Order',
            store=False),
        'product_id' : fields.many2one('product.product', string="Supplier Part No", required=True),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'receive': fields.function(_receive, string='Full Receive', readonly=True, type='boolean', help="It indicates that stock has fully receive"),
        'qty_arrived': fields.function(_qty_arrived, type='float', string='Qty Receive'),
        'received_qty': fields.float("Qty Receive", digits_compute=dp.get_precision('Product UoM')),
    }

sale_allocated()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
