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

class move_allocated_control(osv.osv):
    _name = 'move.allocated.control'
    _description = 'Move Allocated Control'

    def _date_done(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for fifo in self.browse(cr, uid, ids, context=context):
            if fifo.move_id.picking_id:
                res[fifo.id] = fifo.move_id.picking_id.do_date
            else:
                if fifo.move_id.stock_inventory_ids:
                    for si in fifo.move_id.stock_inventory_ids:
                        res[fifo.id] = si.date_done
        return res

    def _rec_quantity(self, cursor, user, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        fifo_control_obj = self.pool.get('fifo.control')
        stock_move_obj = self.pool.get('stock.move')
        for obj in self.browse(cursor, user, ids, context=context):
#            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %('xxx', 'xxxx'))
            rec_qty = 0.00
            stock_move_ids = stock_move_obj.search(cursor, user, [('sale_line_id','=',obj.so_line_id.id),('state','=','done')])
            if stock_move_ids:
                for stock_move_id in stock_move_ids:
                    stock_move = stock_move_obj.browse(cursor, user, stock_move_id, context=context)
                    if obj.int_move_id:
                        fifo_control_ids = fifo_control_obj.browse(cursor, user, fifo_control_obj.search(cursor, user, [('in_move_id','=',obj.move_id.id),('int_in_move_id','=',obj.int_move_id.id),('out_move_id','=',stock_move.id)]), context=context)
                    else:
                        fifo_control_ids = fifo_control_obj.browse(cursor, user, fifo_control_obj.search(cursor, user, [('in_move_id','=',obj.move_id.id),('out_move_id','=',stock_move.id)]), context=context)

                    if fifo_control_ids:
                        for val in fifo_control_ids:
#                            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(val.id, val.quantity))
                            rec_qty = rec_qty + val.quantity
            res[obj.id] = rec_qty
        return res



    _columns = {
        'product_id': fields.related(
            'so_line_id',
            'product_id',
            type='many2one',
            relation='product.product',
            string='Supplier Part No',
            store=False),
        'picking_id': fields.related(
            'move_id',
            'picking_id',
            type='many2one',
            relation='stock.picking',
            string='Grn Name',
            store=False),
        'int_move_id': fields.many2one('stock.move', 'Int Move Id'),
        'move_id': fields.many2one('stock.move', 'Move Id'),
        'so_line_id': fields.many2one('sale.order.line', 'SO Line Id'),
        'quantity': fields.float("Quantity", digits_compute=dp.get_precision('Product UoM')),
        'rec_quantity': fields.function(_rec_quantity, type='float', string='Received Qty'),
        'date_done': fields.function(_date_done, string='Out Date', type='datetime'),
    }

move_allocated_control()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
