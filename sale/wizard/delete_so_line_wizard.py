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

class delete_so_line_wzd(osv.osv_memory):
    _name = 'delete.so.line.wzd'
    _description = 'Delete SO Line'

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        res = super(delete_so_line_wzd, self).default_get(cr, uid, fields, context=context)
        for lines in sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            qty_delivery = 0.00
            move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',lines.id),('state','!=','cancel')])
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
            if 'qty_allocated_onhand' in fields:
                res.update({'qty_allocated_onhand': lines.qty_onhand_count - qty_delivery})

        return res

    def delete_line(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        sale_order_obj = self.pool.get('sale.order')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.qty_received > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because some qty has received from this line'))
            if obj.qty_allocated_onorder > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because find some allocated po in this line. unallocated it to process.'))
            if obj.qty_allocated_onhand > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because find some allocated onhand in this line. unallocated it to process.'))
            so_id = sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context).order_id.id
            amount_untaxed = sale_order_obj.browse(cr, uid, so_id, context=context).amount_untaxed
            amount_tax = sale_order_obj.browse(cr, uid, so_id, context=context).amount_tax
            amount_total = sale_order_obj.browse(cr, uid, so_id, context=context).amount_total
            sol_val = sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context)
            line_untax =  sol_val.price_subtotal
            line_tax = sale_order_obj._amount_line_tax(cr, uid, sol_val, context=context)
            sale_order_line_obj.write(cr, uid, context.get(('active_ids'), []), {'product_uom_qty': 0}, context=context)
            sale_order_line_obj.unlink(cr, uid, context.get(('active_ids'), []))
#            amount_untaxed -= line_untax
#            amount_tax -= line_tax
#            amount_total -= (line_untax + line_tax)
##            raise osv.except_osv(_('Error !'), _(str(amount_total)))
#            sale_order_obj.write(cr, uid, so_id, {'amount_untaxed': amount_untaxed,'amount_tax': amount_tax,'amount_total': amount_total}, context=context)
            
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
        'qty_received': fields.float('Qty Received', readonly=True),
        'qty_allocated_onorder': fields.float('Qty Allocated On Order', readonly=True),
        'qty_allocated_onhand': fields.float('Qty Allocated On Hand', readonly=True),
    }

delete_so_line_wzd()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
