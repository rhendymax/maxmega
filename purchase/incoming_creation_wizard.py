# -*- coding: utf-8 -*-
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

import tools
import time
from osv import fields,osv
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp
import netsvc
import math

class incoming_creation_wizard(osv.osv):
    _name = "incoming.creation.wizard"
    _description = "Incoming Creation Wizard"

    _columns = {
        'incoming_date': fields.date('Goods Receipt Date'),
        'do_date': fields.date('GRN Date'),
        'invoice_date': fields.date('Supplier Invoice Date'),
        'invoice_no': fields.char('Supplier Invoice No', size=64),
        'ref_no': fields.char('Reference No', size=64),
        'desc': fields.text('Description'),
        'country_org_id': fields.many2one('res.country', 'Country of Origin'),
        'country_des_id': fields.many2one('res.country', 'Country of Destination'),
        'incoming_lines_ids' : fields.one2many('incoming.creation.lines', 'wizard_id', 'Incoming Lines'),
        'purchase_order_ids' :fields.many2many('purchase.order', 'incoming_creation_po_rel', 'wizard_id', 'po_id', 'Purchase Order', domain=[('state','=','approved')]),
        'order_line_ids' :fields.many2many('purchase.order.line', 'incoming_creation_po_lines_rel', 'wizard_id', 'lines_id', 'Purchase Order Lines', domain=[('state','=','confirmed')]),
    }

    def action_compute(self, cr, uid, ids, context=None):
        incoming_creation_line_obj = self.pool.get('incoming.creation.lines')
        purchase_order_obj = self.pool.get('purchase.order')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        for wizard in self.browse(cr, uid, ids):
            line_ids = ids and incoming_creation_line_obj.search(cr, uid, [('wizard_id', '=', wizard.id)]) or False
            if line_ids:
                incoming_creation_line_obj.unlink(cr, uid, line_ids)
            purchase_order_ids = []
            for order in wizard.purchase_order_ids:
                purchase_order_ids.append(order.id)
                for lines in order.order_line:
                    qty_delivery = 0.00
                    move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',lines.id),('state','!=','cancel')])
                    if move_ids:
                        for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                            qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
                    qty_sales = product_uom_obj._compute_qty(cr, uid, lines.product_uom.id, lines.product_qty, lines.product_id.uom_id.id)
    
                    qty_order = qty_sales - qty_delivery
                    qty_unit_sale = qty_sales / lines.product_qty
                    qty_order = math.floor(qty_order / qty_unit_sale)
                    if qty_order > 0:
                        incoming_lines_vals = {
                            'spq' : lines.spq,
                            'order_id' : order.id,
                            'order_line_id' : lines.id,
                            'product_id' : lines.product_id.id,
                            'product_uom_qty' : lines.product_qty,
                            'product_uom' : lines.product_uom.id,
                            'qty_delivery' : qty_delivery,
                            'product_uom2' : lines.product_id.uom_id.id,
                            'qty_order' : qty_order,
                            'uom_id' : lines.product_uom.id,
                            'location_dest_id' : lines.location_dest_id.id,
                            'wizard_id': wizard.id,
                            }
                        incoming_creation_line_obj.create(cr, uid, incoming_lines_vals, context)
            for order_lines in wizard.order_line_ids:
                if order_lines.order_id.id in purchase_order_ids:
                    continue
                qty_delivery = 0.00
                move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',order_lines.id),('state','!=','cancel')])
                if move_ids:
                    for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                        qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
                qty_sales = product_uom_obj._compute_qty(cr, uid, order_lines.product_uom.id, order_lines.product_qty, order_lines.product_id.uom_id.id)

                qty_order = qty_sales - qty_delivery
                qty_unit_sale = qty_sales / lines.product_qty
                qty_order = math.floor(qty_order / qty_unit_sale)
                if qty_order > 0:
                    incoming_lines_vals = {
                        'spq' : order_lines.spq,
                        'order_id' : order_lines.order_id.id,
                        'order_line_id' : order_lines.id,
                        'product_id' : order_lines.product_id.id,
                        'product_uom_qty' : order_lines.product_qty,
                        'product_uom' : order_lines.product_uom.id,
                        'qty_delivery' : qty_delivery,
                        'product_uom2' : order_lines.product_id.uom_id.id,
                        'qty_order' : qty_order,
                        'uom_id' : order_lines.product_uom.id,
                        'location_dest_id' : order_lines.location_dest_id.id,
                        'wizard_id': wizard.id,
                        }
                    incoming_creation_line_obj.create(cr, uid, incoming_lines_vals, context)
        return True

    def _prepare_picking(self, cr, uid, generated, po_vals, context=None):
        res_partner_obj = self.pool.get('res.partner')
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
        if po_vals.invoice_method == 'picking':
            invoice_state = '2binvoiced'
        else:
            invoice_state = 'none'

        addr = po_vals.partner_id and res_partner_obj.address_get(cr, uid, [po_vals.partner_id.id], ['delivery', 'invoice', 'contact'])
        partner_val = po_vals.partner_id or False

        picking_vals = {
                        'name': sequence,
                        'invoice_state': invoice_state,
                        'type': 'in',
                        'state': 'draft',
                        'date': generated.incoming_date or time.strftime('%Y-%m-%d'),
                        'do_date': generated.do_date or time.strftime('%Y-%m-%d'),
                        'company_id': (po_vals.company_id and po_vals.company_id.id) or False,
                        'pricelist_id': (po_vals.pricelist_id and po_vals.pricelist_id.id) or False,
                        'partner_order_id' : addr and addr['contact'] or False,
                        'partner_invoice_id' : addr and addr['invoice'] or False,
                        'partner_shipping_id' : (po_vals.partner_shipping_id and po_vals.partner_shipping_id.id) or False,
                        'partner_id': (po_vals.partner_id and po_vals.partner_id.id) or False,
                        'partner_child_id': (po_vals.partner_child_id and po_vals.partner_child_id.id) or False,
                        'ship_method_id' : (partner_val and partner_val.ship_method_id and partner_val.ship_method_id.id) or False,
                        'fob_id' : (partner_val and partner_val.fob_id and partner_val.fob_id.id) or False,
                        'sale_term_id' : (partner_val and partner_val.sale_term_id and partner_val.sale_term_id.id) or False,
                        'fiscal_position' : (po_vals.fiscal_position and po_vals.fiscal_position.id) or False,
                        'invoice_date' : generated.invoice_date,
                        'invoice_no' : generated.invoice_no,
                        'ref_no' : generated.ref_no,
                        'country_org_id' : generated.country_org_id.id,
                        'country_des_id' : generated.country_des_id.id,
                        'note' : generated.desc,
                        }
        return picking_vals

    def _prepare_stock_move(self, cr, uid, moves, picking_id, context=None):
        res_partner_obj = self.pool.get('res.partner')
        account_tax_obj = self.pool.get('account.tax')
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        taxes = account_tax_obj.browse(cr, uid, map(lambda x: x.id, moves.order_line_id.taxes_id))
        fpos = moves.order_id.fiscal_position or False
        taxes_ids = fiscal_position_obj.map_tax(cr, uid, fpos, taxes)

        move_vals = {
             'name': moves.order_id.name + ': ' + (moves.order_line_id.name or ''),
             'picking_id': picking_id,
             'product_id': moves.order_line_id.product_id.id,
             'product_qty': moves.qty_order,
             'product_uom': moves.order_line_id.product_uom.id,
             'product_uos': moves.order_line_id.product_uom.id,
             'date': moves.order_line_id.estimated_time_departure or time.strftime('%Y-%m-%d'),
             'date_expected': moves.order_line_id.estimated_time_arrive or time.strftime('%Y-%m-%d'),
             'location_id': moves.order_id.partner_id.property_stock_supplier.id,
             'location_dest_id': moves.location_dest_id.id,
             'purchase_line_id': moves.order_line_id.id,
             'company_id': (moves.order_id.company_id and moves.order_id.company_id.id) or False,
             'price_unit': moves.order_line_id.price_unit,
             'price_currency_id': moves.order_id.pricelist_id.currency_id.id,
             'state': 'assigned',
             'taxes_id': [(6,0,taxes_ids)],
             'address_id': (moves.order_id.partner_shipping_id and moves.order_id.partner_shipping_id.id) or False,
             'move_dest_id': moves.order_line_id.move_dest_id.id,
             }
        return move_vals

    def generated_do(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        assert len(ids) == 1
        picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        newinv = []
        picking_group = {}

        generated = self.browse(cr, uid, ids[0], context=context)
        move_ids = generated.incoming_lines_ids
        if move_ids:
            for moves in move_ids:
                if moves.qty_order < 1:
                    continue
                po_vals = moves.order_id
                if (str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False)) in picking_group:
                    picking_id = picking_group[(str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False))]
                else:
                    picking_vals = self._prepare_picking(cr, uid, generated, po_vals, context=context)
                    picking_id = picking_obj.create(cr, uid, picking_vals, context=context)
                    newinv.append(picking_id)
                    cr.execute('insert into purchase_order_picking_rel (order_id,picking_id) values (%s,%s)', (moves.order_id.id, picking_id))

                    picking_group[(str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False))] = picking_id
                if moves.order_line_id.state == 'cancel':
                    continue

                vals = self._prepare_stock_move(cr, uid, moves, picking_id, context=context)
                if vals:
                    stock_move_id = stock_move_obj.create(cr, uid, vals, context=context)

            for sp in newinv:
                wf_service.trg_validate(uid, 'stock.picking', sp,
                    'button_confirm', cr)
                wf_service.trg_write(uid, 'stock.picking', sp, cr)
        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree4')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', ["+','.join(map(str,newinv))+"])]"
        result['context'] = "{'search_default_available':0}"
        return result

incoming_creation_wizard()

class incoming_creation_lines(osv.osv_memory):
    _name = 'incoming.creation.lines'
    _description = 'Incoming Lines'

    _columns = {
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'wizard_id': fields.many2one('incoming.creation.wizard', 'Generated Incoming(s)', ondelete='cascade',),
        'order_id' : fields.many2one('purchase.order', 'Order', ondelete='cascade',),
        'order_line_id' : fields.many2one('purchase.order.line', 'Order Line', ondelete='cascade', required=True,),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True,),
        'product_uom_qty': fields.float('Qty (Purchase Order)', readonly=True,),
        'product_uom': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_delivery': fields.float('has generate Qty', readonly=True),
        'product_uom2': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_order': fields.float('Qty (Incoming Shipment)',),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', readonly=True, help="Location where the system will stock the finished products."),
    }

    def onchange_qty_order(self, cr, uid, ids, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_order, uom_id, spq, order_id, context=None):
        res= {}
        product_uom_obj = self.pool.get('product.uom')
        product_product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        spq_approve = False
        if order_id:
            spq_approve = self.pool.get('purchase.order').browse(cr, uid, order_id, context=context).spq_approve
        product_uom = product_uom_obj.browse(cr, uid, product_uom2, context=context)
        res['value'] = {'qty_order': qty_order or 0.0, 'uom_id' : uom_id or False}
        res['domain'] = {'uom_id': [('category_id','=',product_product.uom_id.category_id.id)]}
        if not uom_id:
            return res
        qty_sale = product_uom_obj._compute_qty(cr, uid, product_uom_id, product_uom_qty, product_product.uom_id.id)
        qty_delivery = product_uom_obj._compute_qty(cr, uid, product_uom2, qty_delivery, product_product.uom_id.id)
        qty_order = product_uom_obj._compute_qty(cr, uid, uom_id, qty_order, product_product.uom_id.id)
        if qty_order > 0:
            if spq_approve == False and qty_order%spq != 0:
                qty_order = 0
                if 'warning' in res:
                    if 'message' in res['warning']:
                        message = res['warning']['message']
                        message = message + '\n & \n the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                        res['warning'].update({
                                         'message': message,
                                         })
                    else:
                        message = 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                        res['warning'].update({
                                        'title': _('Configuration Error !'),
                                        'message': message,
                                        })
                else:
                    warning = {
                               'title': _('Configuration Error !'),
                               'message' : 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                               }
                    res['warning'] = warning
            else:
                if qty_order > qty_sale - qty_delivery:
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                                   }
                        res['warning'] = warning
                    qty_order = 0.00
        else:
            qty_order = 0.00
        res['value'].update({'qty_order': qty_order})
        return res

incoming_creation_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
