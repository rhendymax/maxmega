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

class delete_po_line_wzd(osv.osv_memory):
    _name = 'delete.po.line.wzd'
    _description = 'Delete PO Line'

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        res = super(delete_po_line_wzd, self).default_get(cr, uid, fields, context=context)
        for lines in purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            qty_delivery = 0.00
            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',lines.id),('state','!=','cancel')])
            if move_ids:
                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)

            qty_all_order = 0.00
            for all in lines.allocated_ids:
                qty_all_order = qty_all_order + all.quantity
            if 'qty_received' in fields:
                res.update({'qty_received': qty_delivery})
            if 'qty_allocated_onorder' in fields:
                res.update({'qty_allocated_onorder': qty_all_order})

        return res

    def delete_line(self, cr, uid, ids, context=None):
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        purchase_order_obj = self.pool.get('purchase.order')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.qty_received > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because some qty has received from this line'))
            if obj.qty_allocated_onorder > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because find some allocated po in this line. unallocated it to process.'))
            po_id = purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context).order_id.id
            amount_untaxed = purchase_order_obj.browse(cr, uid, po_id, context=context).amount_untaxed
            amount_tax = purchase_order_obj.browse(cr, uid, po_id, context=context).amount_tax
            amount_total = purchase_order_obj.browse(cr, uid, po_id, context=context).amount_total
            pol_val = purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context)
            line_untax =  pol_val.price_subtotal
            #line_tax = purchase_order_obj._amount_line_tax(cr, uid, pol_val, context=context)
            purchase_order_line_obj.write(cr, uid, context.get(('active_ids'), []), {'product_uom_qty': 0}, context=context)
            purchase_order_line_obj.unlink(cr, uid, context.get(('active_ids'), []))
#            amount_untaxed -= line_untax
#            amount_tax -= line_tax
#            amount_total -= (line_untax + line_tax)
##            raise osv.except_osv(_('Error !'), _(str(amount_total)))
#            sale_order_obj.write(cr, uid, so_id, {'amount_untaxed': amount_untaxed,'amount_tax': amount_tax,'amount_total': amount_total}, context=context)
            
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
        'qty_received': fields.float('Qty Received', readonly=True),
        'qty_allocated_onorder': fields.float('Qty Allocated On Order', readonly=True),
    }

delete_po_line_wzd()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
