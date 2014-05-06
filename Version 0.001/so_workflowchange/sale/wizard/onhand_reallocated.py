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

class onhand_reallocated(osv.osv_memory):
    _name = 'onhand.reallocated'
    _description = 'Change On Hand Allocated'

    def onchange_allocated_by_coulumn(self, cr, uid, ids ,allocated_by_coulumn):
        if allocated_by_coulumn == True:
            return {'value':{'allocated_by_field': False}}
        else:
            return {'value':{'allocated_by_field': True}}
        return True

    def onchange_allocated_by_field(self, cr, uid, ids ,allocated_by_field):
        if allocated_by_field == True:
            return {'value':{'allocated_by_coulumn': False}}
        else:
            return {'value':{'allocated_by_coulumn': True}}
        return True

    def onchange_qty_reallocated(self, cr, uid, ids ,qty_reallocated, qty_delivery, total_qty_reallocated, spq):
        if qty_reallocated > 0:
            if qty_reallocated%spq != 0:
                qty_reallocated= spq * ((qty_reallocated-(qty_reallocated%spq))/spq)
        else:
            qty_reallocated = 0
        if qty_reallocated < qty_delivery:
            warning = {'title': _('Warning'), 'message': _("the Qty for On hand Re-Allocated cannot less than has generated Qty.")}
            return {'value':{'qty_reallocated': qty_delivery}, 'warning':warning}
        if qty_reallocated > total_qty_reallocated:
            warning = {'title': _('Warning'), 'message': _("the Qty for On hand Re-Allocated cannot more than Total Qty can Re-Allocated.")}
            return {'value':{'qty_reallocated': total_qty_reallocated}, 'warning':warning}
        return {'value':{'qty_reallocated': qty_reallocated}}

    def do_refresh(self, cr, uid, ids, context=None):
        fifo_onhand_reallocated_obj = self.pool.get('fifo.onhand.reallocated')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.allocated_by_coulumn == True:
                fifo_qty = 0.00
                for line in obj.fifo_product_detail_ids:
                    fifo_qty = fifo_qty + line.onhand_allocated_qty
                if fifo_qty%obj.spq != 0:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated (' + str(fifo_qty) + ') not in spq rounding. the closest qty is ' + str(fifo_qty-(fifo_qty%obj.spq)) + ' or ' + str((fifo_qty-(fifo_qty%obj.spq)) + obj.spq) + '.'))
                if fifo_qty < obj.qty_delivery:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated cannot less than has generated Qty.'))
                if fifo_qty > obj.total_qty_reallocated:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated cannot more than Total Qty can Re-Allocated.'))
                self.write(cr, uid, ids, {'qty_reallocated': fifo_qty})
                return True
            else:
                qty_reallocated = obj.qty_reallocated
                
                if qty_reallocated > 0:
                    for line in obj.fifo_product_detail_ids:
                        if qty_reallocated > 0:
                            if qty_reallocated > line.qty_onhand_free:
                                qty_reallocated = qty_reallocated - line.qty_onhand_free
#                                raise osv.except_osv(_('Invalid action !'), _(str(line.qty_onhand_free)))
                                fifo_onhand_reallocated_obj.write(cr, uid, line.id, {
                                                                                     'onhand_allocated_qty': line.qty_onhand_free,
                                                                                     })
                            else:
#                                raise osv.except_osv(_('Debug !'), _(str(qty_reallocated)))

                                fifo_onhand_reallocated_obj.write(cr, uid, line.id, {
                                                      'onhand_allocated_qty': qty_reallocated,
                                                      })
                                qty_reallocated = 0
                        else:
                            fifo_onhand_reallocated_obj.write(cr, uid, line.id, {
                                                  'onhand_allocated_qty': 0.00,
                                                  })
                else:
                    for line in obj.fifo_product_detail_ids:
                        fifo_onhand_reallocated_obj.write(cr, uid, line.id, {
                                                                             'onhand_allocated_qty': 0.00,
                                                                             })
                return True
        return {'type': 'ir.actions.act_window_close'}

    def do_reallocated(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        sale_allocated_obj = self.pool.get('sale.allocated')
        move_allocated_control_obj = self.pool.get('move.allocated.control')
        for obj in self.browse(cr, uid, ids, context=context):
            sol = sale_order_line_obj.browse(cr, uid, obj.sale_line_id.id, context=context)
            qty_onhand_allocated = sol.qty_onhand_allocated
            qty_received_onorder = sol.qty_received_onorder

            if obj.allocated_by_coulumn == True:
                fifo_qty = 0.00
                for line in obj.fifo_product_detail_ids:
                    fifo_qty = fifo_qty + line.onhand_allocated_qty
                if fifo_qty%obj.spq != 0:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated (' + str(fifo_qty) + ') not in spq rounding. the closest qty is ' + str(fifo_qty-(fifo_qty%obj.spq)) + ' or ' + str((fifo_qty-(fifo_qty%obj.spq)) + obj.spq) + '.'))
                if fifo_qty < obj.qty_delivery:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated cannot less than has generated  Qty'))
                if fifo_qty > obj.total_qty_reallocated:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot process because total qty allocated cannot more than Total Qty can Re-Allocated'))
                else:
                    for line in obj.fifo_product_detail_ids:
                        if line.int_move_id:
                            move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('int_move_id','=',line.int_move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                        else:
                            move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                        if move_allocated_control_ids:
                            for all_c in move_allocated_control_ids:
                                if line.onhand_allocated_qty > 0:

                                    move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                         'quantity': line.onhand_allocated_qty + all_c.rec_quantity,
                                                                                         })
                                else:
                                    if all_c.rec_quantity > 0:
                                        move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                     'quantity': all_c.rec_quantity,
                                                                                     })
                                    else:
                                        move_allocated_control_obj.unlink(cr, uid, all_c.id, context=context)
                        else:
                            if line.onhand_allocated_qty > 0:
                                move_allocated_control_obj.create(cr, uid, {
                                                                            'int_move_id': line.int_move_id and line.int_move_id.id or False,
                                                                            'move_id': line.move_id.id,
                                                                            'so_line_id': sol.id,
                                                                            'quantity': line.onhand_allocated_qty,
                                                                            }, context=context)
                    qty_reallocated = fifo_qty - qty_received_onorder
                    sale_order_line_obj.write(cr, uid, obj.sale_line_id.id, {'qty_onhand_allocated': qty_reallocated + obj.qty_order_received}, context=context)
            else:
                qty_reallocated = obj.qty_reallocated
                sale_order_line_obj.write(cr, uid, obj.sale_line_id.id, {'qty_onhand_allocated': qty_reallocated + obj.qty_order_received}, context=context)
                if qty_reallocated > 0:
                    for line in obj.fifo_product_detail_ids:
                        if qty_reallocated > 0:
                            if qty_reallocated > line.qty_onhand_free:
                                qty_reallocated = qty_reallocated - line.qty_onhand_free
                                if line.int_move_id:
                                    move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('int_move_id','=',line.int_move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                                else:
                                    move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                                if move_allocated_control_ids:
                                    for all_c in move_allocated_control_ids:
                                        move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                     'quantity': line.qty_onhand_free + all_c.rec_quantity,
                                                                                     })
                                else:
                                    move_allocated_control_obj.create(cr, uid, {
                                                                                'int_move_id': line.int_move_id and line.int_move_id.id or False,
                                                                                'move_id': line.move_id.id,
                                                                                'so_line_id': sol.id,
                                                                                'quantity': line.qty_onhand_free,
                                                                                }, context=context)
                            else:
                                if line.int_move_id:
                                    move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('int_move_id','=',line.int_move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                                else:
                                    move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                                if move_allocated_control_ids:
                                    for all_c in move_allocated_control_ids:
                                        move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                     'quantity': qty_reallocated + all_c.rec_quantity,
                                                                                     })
                                else:
                                    move_allocated_control_obj.create(cr, uid, {
                                                                                'int_move_id': line.int_move_id and line.int_move_id.id or False,
                                                                                'move_id': line.move_id.id,
                                                                                'so_line_id': sol.id,
                                                                                'quantity': qty_reallocated,
                                                                                }, context=context)
                                qty_reallocated = 0
                        else:
                            if line.int_move_id:
                                move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('int_move_id','=',line.int_move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                            else:
                                move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                            if move_allocated_control_ids:
                                for all_c in move_allocated_control_ids:
                                    if all_c.rec_quantity > 0:
                                        move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                     'quantity': all_c.rec_quantity,
                                                                                     })
                                    else:
                                        move_allocated_control_obj.unlink(cr, uid, all_c.id, context=context)
                else:
                    for line in obj.fifo_product_detail_ids:
                        if line.int_move_id:
                            move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('int_move_id','=',line.int_move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                        else:
                            move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',line.move_id.id), ('so_line_id','=',obj.sale_line_id.id)]), context=context)
                        if move_allocated_control_ids:
                            for all_c in move_allocated_control_ids:
                                if all_c.rec_quantity > 0:
                                    move_allocated_control_obj.write(cr, uid, all_c.id, {
                                                                                 'quantity': all_c.rec_quantity,
                                                                                 })
                                else:
                                    move_allocated_control_obj.unlink(cr, uid, all_c.id, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'qty_delivery': fields.float('has generate Qty', readonly=True),
        'allocated_by_coulumn': fields.boolean('Allocated Using Coulumn Method', help="ticked if want to allocated Qty OnHand using coulumn method."),
        'allocated_by_field': fields.boolean('Allocated Using Field Method', help="ticked if want to allocated Qty OnHand using Field Fill method."),
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Order Line', required=True, ondelete='cascade'),
        'location_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', readonly=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade',readonly=True),
        'qty_onhand_count' : fields.float("Qty on Hand Allocated", readonly=True),
        'qty_free' : fields.float("Quantity On Hand Free", readonly=True),
        'qty_order_allocated' : fields.float("Qty Sales Order can Allocated", readonly=True),
        'qty_order_received' : fields.float("Qty Sales Order has Received", readonly=True),
        'total_qty_reallocated' : fields.float("Total Qty can Re-Allocated", readonly=True),
        'qty_reallocated': fields.float("Qty On hand Re-Allocated", digits_compute=dp.get_precision('Product UoM')),
        'fifo_product_detail_ids' : fields.one2many('fifo.onhand.reallocated', 'wizard_id2', 'Fifo Product Detail View', readonly=True),
    }

onhand_reallocated()


class fifo_onhand_reallocated(osv.osv_memory):
    _name = 'fifo.onhand.reallocated'
    _description = 'Fifo OnHand Reallocated'

    _columns = {
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True),
        'wizard_id2' : fields.many2one('onhand.reallocated', string="Wizard", ondelete='cascade'),
        'int_move_id': fields.many2one('stock.move', 'Int move id',),
        'move_id': fields.many2one('stock.move', 'move id',),
        'document_no': fields.char('Number', size=64, readonly=True),
        'document_date': fields.datetime('Date Done', readonly=True),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True),
        'product_qty': fields.float('Qty On_Hand', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', readonly=True),
        'qty_allocated': fields.float('Qty Allocated', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'qty_onhand_free': fields.float('Qty On_Hand Free', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'onhand_allocated_qty': fields.float('Qty.(On Hand)', digits_compute= dp.get_precision('Product UoM')),
    }

    def onchange_onhand_allocated_qty(self, cr, uid, ids, onhand_allocated_qty, qty_free):
        if onhand_allocated_qty > 0:
            if onhand_allocated_qty > qty_free:
                warning = {'title': _('Warning'), 'message': _("the Qty.(On Hand) entered cannot more than Qty On Hand Free.")}
                return  {'value': {'onhand_allocated_qty': qty_free}, 'warning': warning}
        else:
            return {'value': {'onhand_allocated_qty': 0.000}}

fifo_onhand_reallocated()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
