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

class change_qty_po(osv.osv_memory):
    _name = 'change.qty.po'
    _description = 'Change Qty'

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        res = super(change_qty_po, self).default_get(cr, uid, fields, context=context)
        for lines in purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            qty_delivery = 0.00
            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',lines.id),('state','!=','cancel')])
            if move_ids:
                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
            qty_purchase = product_uom_obj._compute_qty(cr, uid, lines.product_uom.id, lines.product_qty, lines.product_id.uom_id.id)
            qty_all_order = 0.00
            for all in lines.allocated_ids:
                qty_all_order = qty_all_order + all.quantity
            if 'moq' in fields:
                res.update({'moq': lines.moq})
            if 'spq' in fields:
                res.update({'spq': lines.spq})
            if 'qty_order' in fields:
                res.update({'qty_order': qty_purchase})
            if 'qty_received' in fields:
                res.update({'qty_received': qty_delivery})
            if 'qty_remaining' in fields:
                res.update({'qty_remaining': qty_purchase - qty_delivery})
            if 'qty_allocated_onorder' in fields:
                res.update({'qty_allocated_onorder': qty_all_order})
            if 'product_uom_qty' in fields:
                res.update({'product_uom_qty': qty_purchase})

        return res

    def onchange_qty(self, cr, uid, ids ,product_uom_qty, qty_remaining, qty_allocated_onorder,qty_received,moq,spq):
#        total_all = qty_allocated_onorder + qty_order
        res = {}
#        print product_uom_qty
#        print moq
#####################
#     START
#####################
#         if product_uom_qty < moq:
#             warning = {'title': _('Warning'), 'message': _("the Qty cannot less than moq.")}
#             return {'value':{'product_uom_qty': 0}, 'warning':warning}
# END
        if product_uom_qty < spq:
            product_uom_qty = 0
        if product_uom_qty%spq != 0:
            product_uom_qty= 0
        if product_uom_qty == 0:
            warning = {'title': _('Warning'), 'message': _("the Qty entered is not in spq multiplication.")}
            return {'value':{'product_uom_qty': product_uom_qty}, 'warning':warning}
#        if product_uom_qty > qty_remaining:
#            warning = {'title': _('Warning'), 'message': _("the Qty cannot more than qty remaining.")}
#            return {'value':{'product_uom_qty': 0}, 'warning':warning}
#        print 'Xxxxxxxxxxxxxxxxxxxx'
#        print total_all
        if product_uom_qty < qty_received:
            warning = {'title': _('Warning'), 'message': _("the Qty cannot less than Qty Received.")}
            return {'value':{'product_uom_qty': 0}, 'warning':warning}
        if product_uom_qty < qty_allocated_onorder:
            warning = {'title': _('Warning'), 'message': _("the Qty cannot less than allocated qty.")}
            return {'value':{'product_uom_qty': 0}, 'warning':warning}
        return res

    def change_qty(self, cr, uid, ids, context=None):
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.product_uom_qty <= 0:
                return {'type': 'ir.actions.act_window_close'}
            purchase_order_line_obj.write(cr, uid, context.get(('active_ids'), []), {'product_qty': obj.product_uom_qty}, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
        'spq': fields.float('SPQ (*)', readonly=True, help="Standard Packaging Qty"),
        'moq': fields.float('MOQ (*)', readonly=True, help="Minimum Order Qty"),
        'qty_order': fields.float('Qty Order', readonly=True),
        'qty_received': fields.float('Qty Received', readonly=True),
        'qty_remaining': fields.float('Qty Remaining', readonly=True),
        'qty_allocated_onorder': fields.float('Qty Allocated On Order', readonly=True),
        'product_uom_qty': fields.float('Quantity (UoM)', required=True),
    }

change_qty_po()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
