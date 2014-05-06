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

class allocated_po(osv.osv_memory):
    _name = 'allocated.po'
    _description = 'Allocated Purchase Order'

    def default_get(self, cr, uid, fields, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        sale_allocated_obj = self.pool.get('sale.allocated')
        product_uom_obj = self.pool.get('product.uom')
        stock_move_obj = self.pool.get('stock.move')
        result1 = []
        if context is None:
            context = {}
        res = super(allocated_po, self).default_get(cr, uid, fields, context=context)

        for lines in sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            spq = lines.product_id.spq

            pol_ids = []
            purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',lines.product_id.id),('location_dest_id','=',lines.location_id.id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])
            if purchase_order_line_ids:
                for val in purchase_order_line_ids:
                    pol = purchase_order_line_obj.browse(cr, uid, val, context=context)
                    qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, pol.product_id.uom_id.id)
                    sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
                    qty_allocated = 0.00
                    qty_received = 0.00
                    incoming_qty = 0.00
                    if sale_allocated_ids:
                        for val2 in sale_allocated_ids:
                            qty_allocated = qty_allocated + val2.quantity
                            qty_received = qty_received + val2.received_qty

                    if qtyp > 0:
                        stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
                        if stock_move_ids:
                            for stock_move_id in stock_move_ids:
                                stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                                incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, pol.product_id.uom_id.id)
                        if qtyp - (incoming_qty - qty_received) - qty_allocated > 0:
                            pol_ids.append(val)

            pol_ids = sorted(set(pol_ids))
            po_ids = []

            for o2 in pol_ids:
                pol2 = purchase_order_line_obj.browse(cr, uid, o2, context=context)
                po_ids.append(pol2.order_id.id)

            po_ids = sorted(set(po_ids))

            if po_ids:
                purchase_order_id = po_ids[0]
                polxx_ids = purchase_order_line_obj.search(cr, uid, [('order_id','=',purchase_order_id),('product_id','=',lines.product_id.id)])
                purchase_order_line_id = polxx_ids[0]
            else:
                raise osv.except_osv(_('No Un-Allocated !'), _('no Un-Allocated found in Purchase Order!'))

            sale_allocated_id = sale_allocated_obj.search(cr, uid, [('sale_line_id','=',lines.id),('purchase_line_id','=',purchase_order_line_id)])
            if sale_allocated_id:
                sale_allocated = sale_allocated_obj.browse(cr, uid, sale_allocated_id[0], context=context)
                qty_sale_order = sale_allocated.quantity
                qty_sale_order_received = sale_allocated.received_qty
            else:
                qty_sale_order = 0.00
                qty_sale_order_received = 0.00

            qty_purchase_order = 0.00
            pol3 = purchase_order_line_obj.browse(cr, uid, purchase_order_line_id, context=context)
            qtyp3 = product_uom_obj._compute_qty(cr, uid, pol3.product_uom.id, pol3.product_qty, pol3.product_id.uom_id.id)
            sale_allocated_ids3 = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',purchase_order_line_id),('receive','=',False)]), context=context)
            qty_allocated3 = 0.00
            qty_received3 = 0.00
            incoming_qty3 = 0.00
            if sale_allocated_ids3:
                for val3 in sale_allocated_ids3:
                    qty_allocated3 = qty_allocated3 + val3.quantity
                    qty_received3 = qty_received3 + val3.received_qty

            if qtyp3 > 0:
                stock_move_ids3 = stock_move_obj.search(cr, uid, [('purchase_line_id','=',purchase_order_line_id),('state','=','done')])
                if stock_move_ids3:
                    for stock_move_id3 in stock_move_ids3:
                        stock_move3 = stock_move_obj.browse(cr, uid, stock_move_id3, context=context)
                        incoming_qty3 = incoming_qty3 + product_uom_obj._compute_qty(cr, uid, stock_move3.product_uom.id, stock_move3.product_qty, stock_move3.product_id.uom_id.id)
                qty_purchase_order = qtyp3 - (incoming_qty3 - qty_received3) - qty_allocated3

            qty_sale_order2 = 0.00
            qtyp4 = product_uom_obj._compute_qty(cr, uid, lines.product_uom.id, lines.product_uom_qty, lines.product_id.uom_id.id)
            qty_onhand_allocated4 = lines.qty_onhand_allocated
            sale_allocated_ids4 = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('sale_line_id','=',lines.id)]), context=context)
            qty_allocated42 = 0.00
            if sale_allocated_ids4:
                for val4 in sale_allocated_ids4:
                     qty_allocated42 = qty_allocated42 + val4.quantity
            qty_sale_order2 = (qtyp4 - (qty_onhand_allocated4 + qty_allocated42)) + qty_sale_order

            qty_can_allocated = 0.00
            if qty_sale_order + qty_purchase_order < qty_sale_order2:
                qty_can_allocated = qty_sale_order + qty_purchase_order
            else:
                qty_can_allocated = qty_sale_order2
            if 'spq' in fields:
                res.update({'spq': spq or 0.00})
            if 'qty_sale_order' in fields:
                res.update({'qty_sale_order': qty_sale_order or 0.00})
            if 'qty_sale_order_received' in fields:
                res.update({'qty_sale_order_received': qty_sale_order_received or 0.00})
            if 'qty_purchase_order' in fields:
                res.update({'qty_purchase_order': qty_purchase_order or 0.00})
            if 'qty_sale_order2' in fields:
                res.update({'qty_sale_order2': qty_sale_order2 or 0.00})
            if 'qty_can_allocated' in fields:
                res.update({'qty_can_allocated': qty_can_allocated or 0.00})
            if 'qty_sale_orderx' in fields:
                res.update({'qty_sale_orderx': qty_sale_order or 0.00})
            if 'qty_sale_order_receivedx' in fields:
                res.update({'qty_sale_order_receivedx': qty_sale_order_received or 0.00})
            if 'qty_purchase_orderx' in fields:
                res.update({'qty_purchase_orderx': qty_purchase_order or 0.00})
            if 'qty_sale_order2x' in fields:
                res.update({'qty_sale_order2x': qty_sale_order2 or 0.00})
            if 'qty_can_allocatedx' in fields:
                res.update({'qty_can_allocatedx': qty_can_allocated or 0.00})
            if 'purchase_order_id' in fields:
                res.update({'purchase_order_id': purchase_order_id or False})
            if 'purchase_order_line_id' in fields:
                res.update({'purchase_order_line_id': purchase_order_line_id or False})
            if 'product_id' in fields:
                res.update({'product_id': lines.product_id.id or False})
            if 'sale_order_line_id' in fields:
                res.update({'sale_order_line_id': lines.id or False})
            if 'location_dest_id' in fields:
                res.update({'location_dest_id': lines.location_id.id or False})
        return res

    def onchange_purchase_order_id(self, cr, uid, ids ,purchase_order_id, purchase_order_line_id, product_id, location_dest_id, context={}):

        purchase_order_line_obj = self.pool.get("purchase.order.line")
        purchase_order_obj = self.pool.get("purchase.order")
        product_uom_obj = self.pool.get("product.uom")
        stock_move_obj = self.pool.get("stock.move")
        sale_allocated_obj = self.pool.get("sale.allocated")
        product_product_obj = self.pool.get("product.product")
        res = {}
        res['value'] = {}
        pol_ids = []
        if not purchase_order_id:
            return {}

        purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',product_id),('location_dest_id','=',location_dest_id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])
        if purchase_order_line_ids:
            for val in purchase_order_line_ids:
                pol = purchase_order_line_obj.browse(cr, uid, val, context=context)

                qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, pol.product_id.uom_id.id)
                sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
                qty_allocated = 0.00
                qty_received = 0.00
                incoming_qty = 0.00
                if sale_allocated_ids:
                    for val2 in sale_allocated_ids:
                        qty_allocated = qty_allocated + val2.quantity
                        qty_received = qty_received + val2.received_qty
        #        if pol.id == 46:
        #            raise osv.except_osv(_('Debug !'), _(str(qty_allocated) + '----' + '' + '----' + ''))

                if qtyp > 0:
                    stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
                    if stock_move_ids:
                        for stock_move_id in stock_move_ids:
                            stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                            incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, pol.product_id.uom_id.id)
                    if qtyp - (incoming_qty - qty_received) - qty_allocated > 0:
                        pol_ids.append(val)

        pol_ids = sorted(set(pol_ids))
        po_ids = []
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

        for o in pol_ids:
            pol2 = purchase_order_line_obj.browse(cr, uid, o, context=context)
            po_ids.append(pol2.order_id.id)
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

        po_ids = sorted(set(po_ids))

        res['domain'] = {'purchase_order_id': [('id','in',po_ids)]}

        if purchase_order_id not in po_ids:
            res['value'].update({'purchase_order_id': False, 'purchase_order_line_id': False})
            res['warning'] = {'title': _('Warning'), 'message': _('The selected Purchase Order is not belong to Product ' + str(product_product_obj.browse(cr, uid, product_id, context=context).name) + ' !')}
            return res

        if purchase_order_line_id:
            pol3 = purchase_order_line_obj.browse(cr, uid, purchase_order_line_id, context=context)
            if pol3.order_id.id != purchase_order_id:
                res['value'].update({'purchase_order_line_id': False})
#                res['warning'] = {'title': _('Warning'), 'message': _('The selected Purchase Order Line is not belong to Purchase Order ' + str(purchase_order_obj.browse(cr, uid, purchase_order_id, context=context).name) + ' !')}
            return res
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

#        res['domain'] = {'product_id': [('id','in',product_ids)]}
        return res

    def onchange_purchase_order_line_id(self, cr, uid, ids , purchase_order_line_id, sale_order_line_id, context={}):

        purchase_order_line_obj = self.pool.get("purchase.order.line")
        sale_order_line_obj = self.pool.get("sale.order.line")
        purchase_order_obj = self.pool.get("purchase.order")
        product_uom_obj = self.pool.get("product.uom")
        stock_move_obj = self.pool.get("stock.move")
        sale_allocated_obj = self.pool.get("sale.allocated")
        product_product_obj = self.pool.get("product.product")
        valxx = {
            'spq' : 0.00,
            'qty_sale_order': 0.00,
            'qty_sale_order_received': 0.00,
            'qty_purchase_order': 0.00,
            'qty_sale_order2': 0.00,
            'qty_can_allocated': 0.00,
            'qty_sale_orderx': 0.00,
            'qty_sale_order_receivedx': 0.00,
            'qty_purchase_orderx': 0.00,
            'qty_sale_order2x': 0.00,
            'qty_can_allocatedx': 0.00,
            'qty_allocated': 0.00,
        }
        if not purchase_order_line_id:
            return {'value': valxx}

        sale_allocated_id = sale_allocated_obj.search(cr, uid, [('sale_line_id','=',sale_order_line_id),('purchase_line_id','=',purchase_order_line_id)])
        if sale_allocated_id:
            sale_allocated = sale_allocated_obj.browse(cr, uid, sale_allocated_id[0], context=context)
            qty_sale_order = sale_allocated.quantity
            qty_sale_order_received = sale_allocated.received_qty
        else:
            qty_sale_order = 0.00
            qty_sale_order_received = 0.00

        qty_purchase_order = 0.00
        pol3 = purchase_order_line_obj.browse(cr, uid, purchase_order_line_id, context=context)
        qtyp3 = product_uom_obj._compute_qty(cr, uid, pol3.product_uom.id, pol3.product_qty, pol3.product_id.uom_id.id)
        sale_allocated_ids3 = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',purchase_order_line_id),('receive','=',False)]), context=context)
        spq = pol3.product_id.spq
        qty_allocated3 = 0.00
        qty_received3 = 0.00
        incoming_qty3 = 0.00
        if sale_allocated_ids3:
            for val3 in sale_allocated_ids3:
                qty_allocated3 = qty_allocated3 + val3.quantity
                qty_received3 = qty_received3 + val3.received_qty

        if qtyp3 > 0:
            stock_move_ids3 = stock_move_obj.search(cr, uid, [('purchase_line_id','=',purchase_order_line_id),('state','=','done')])
            if stock_move_ids3:
                for stock_move_id3 in stock_move_ids3:
                    stock_move3 = stock_move_obj.browse(cr, uid, stock_move_id3, context=context)
                    incoming_qty3 = incoming_qty3 + product_uom_obj._compute_qty(cr, uid, stock_move3.product_uom.id, stock_move3.product_qty, stock_move3.product_id.uom_id.id)
            qty_purchase_order = qtyp3 - (incoming_qty3 - qty_received3) - qty_allocated3

        qty_sale_order2 = 0.00
        o = sale_order_line_obj.browse(cr, uid, sale_order_line_id, context=context)
        qtyp4 = product_uom_obj._compute_qty(cr, uid, o.product_uom.id, o.product_uom_qty, o.product_id.uom_id.id)
        qty_onhand_allocated4 = o.qty_onhand_allocated
        sale_allocated_ids4 = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('sale_line_id','=',o.id)]), context=context)
        qty_allocated42 = 0.00
        if sale_allocated_ids4:
            for val in sale_allocated_ids4:
                 qty_allocated42 = qty_allocated42 + val.quantity
        qty_sale_order2 = (qtyp4 - (qty_onhand_allocated4 + qty_allocated42)) + qty_sale_order

        qty_can_allocated = 0.00
        if qty_sale_order + qty_purchase_order < qty_sale_order2:
            qty_can_allocated = qty_sale_order + qty_purchase_order
        else:
            qty_can_allocated = qty_sale_order2

#        raise osv.except_osv(_('Debug !'), _(str(qty_sale_order) + '----' + str(qty_sale_order_received) + '----' + str(qty_purchase_order) + '----' + str(qty_sale_order2) + '----' + str(qty_can_allocated)))

        val = {
            'spq': spq,
            'qty_sale_order': qty_sale_order,
            'qty_sale_order_received': qty_sale_order_received,
            'qty_purchase_order': qty_purchase_order,
            'qty_sale_order2': qty_sale_order2,
            'qty_can_allocated': qty_can_allocated,
            'qty_sale_orderx': qty_sale_order,
            'qty_sale_order_receivedx': qty_sale_order_received,
            'qty_purchase_orderx': qty_purchase_order,
            'qty_sale_order2x': qty_sale_order2,
            'qty_can_allocatedx': qty_can_allocated,
        }
        return {'value': val}

    def onchange_qty_allocated(self, cr, uid, ids , qty_allocated, qty_can_allocated, spq):
        if qty_allocated > 0:
            if qty_allocated%spq != 0:
                qty_allocated= spq * ((qty_allocated-(qty_allocated%spq))/spq)
        else:
            qty_allocated = 0
        if qty_allocated > qty_can_allocated:
            warning = {'title': _('Warning'), 'message': _("the Qty for Allocated cannot more than Qty can allocated to this Purchase Order.")}
            return {'value':{'qty_allocated': qty_can_allocated}, 'warning':warning}
        return {'value':{'qty_allocated': qty_allocated}}

    
    def do_reallocated(self, cr, uid, ids, context=None):
        sale_allocated_obj = self.pool.get('sale.allocated')
        sale_order_line_obj = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.qty_allocated > 0:
                if obj.qty_sale_order > 0:
                    sale_allocated_id = sale_allocated_obj.search(cr, uid, [('sale_line_id', '=', obj.sale_order_line_id.id), ('purchase_line_id', '=', obj.purchase_order_line_id.id)])
                    if obj.qty_allocated < obj.qty_sale_order_received:
                        sol = sale_order_line_obj.browse(cr, uid, obj.sale_order_line_id.id, context=context)
                        qty_onhand_allocated = sol.qty_onhand_allocated
                        sale_order_line_obj.write(cr, uid, sol.id,
                            {'qty_onhand_allocated': qty_onhand_allocated + (obj.qty_sale_order_received - obj.qty_allocated)}, context=context)
                        sale_allocated_obj.write(cr, uid, sale_allocated_id[0], {'quantity': obj.qty_allocated, 'received_qty': obj.qty_allocated}, context=context)
                    else:
                        sale_allocated_obj.write(cr, uid, sale_allocated_id[0], {'quantity': obj.qty_allocated}, context=context)
                else:
                    sale_allovated_vals = {
                        'sale_line_id': obj.sale_order_line_id.id,
                        'purchase_line_id': obj.purchase_order_line_id.id,
                        'product_id': obj.product_id.id,
                        'quantity': obj.qty_allocated,
                        'product_uom' : obj.product_id.uom_id.id,
                        'received_qty': 0.00,}
                    sale_allocated_obj.create(cr, uid, sale_allovated_vals,context=context)
        return {'type': 'ir.actions.act_window_close'}

    def write(self, cr, uid, ids, vals, context=None):
        if 'qty_sale_orderx' in vals:
            vals.update({'qty_sale_order': vals['qty_sale_orderx']})
        if 'qty_sale_order_receivedx' in vals:
            vals.update({'qty_sale_order_received': vals['qty_sale_order_receivedx']})
        if 'qty_purchase_orderx' in vals:
            vals.update({'qty_purchase_order': vals['qty_purchase_orderx']})
        if 'qty_sale_order2x' in vals:
            vals.update({'qty_sale_order2': vals['qty_sale_order2x']})
        if 'qty_can_allocatedx' in vals:
            vals.update({'qty_can_allocated': vals['qty_can_allocatedx']})
        return super(allocated_po, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'purchase_order_id': fields.many2one('purchase.order', 'Purchase Order', ondelete='cascade', required=True),
        'purchase_order_line_id': fields.many2one('purchase.order.line', 'Purchase Order Line', ondelete='cascade', required=True),
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade'),
        'qty_sale_order': fields.float('Qty Sale Order which has allocated to this Purchase Order', readonly=True),
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'qty_sale_order_received': fields.float('Qty Sale Order which has allocated to this Purchase Order(Received)', readonly=True),
        'qty_purchase_order': fields.float('Qty Purchase Order which can allocated', readonly=True),
        'qty_sale_order2': fields.float('Qty Sales Order need to allocated', readonly=True),
        'qty_can_allocated': fields.float('Qty can allocated to this Purchase Order', readonly=True),
        'qty_sale_orderx': fields.float('Qty Sale Order which has allocated to this Purchase Order'),
        'qty_sale_order_receivedx': fields.float('Qty Sale Order which has allocated to this Purchase Order(Received)'),
        'qty_purchase_orderx': fields.float('Qty Purchase Order which can allocated'),
        'qty_sale_order2x': fields.float('Qty Sales Order need to allocated'),
        'qty_can_allocatedx': fields.float('Qty can allocated to this Purchase Order'),
        'qty_allocated': fields.float("Qty Allocated"),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', readonly=True, help="Location where the system will stock the finished products."),
    }

allocated_po()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
