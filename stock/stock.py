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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import decimal_precision as dp
import netsvc
from datetime import datetime, timedelta

class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _description = "Picking List"

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for pick in self.browse(cr, uid, ids, context=context):
            if pick.type == 'out' and pick.state in ['assigned']:
                raise osv.except_osv(_('Error'), _('You cannot remove the picking which is in %s state !')%("Ready To Process",))

        return super(stock_picking, self).unlink(cr, uid, ids, context=context)

    def create(self, cr, user, vals, context=None):
        if 'type' in vals:
            if vals['type'] == 'in':
                if 'created_vals' in vals:
                    if vals['created_vals'] == False:
                        raise osv.except_osv(_('Error!'), _('Cannot Create Incoming'))
            if vals['type'] == 'out':
                if 'created_vals' in vals:
                    if vals['created_vals'] == False:
                        raise osv.except_osv(_('Error!'), _('Cannot Create Delivery Order'))
        new_id = super(stock_picking, self).create(cr, user, vals, context)
        return new_id

    def action_approve_paymentterm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_term': True, 'term_approver': uid, 'term_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_undo_paymentterm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_term': False, 'term_approver': False, 'term_date':False})
        return True

    def action_approve_creditlimit(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_credit': True, 'credit_approver': uid, 'credit_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_undo_creditlimit(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_credit': False, 'credit_approver': False, 'credit_date':False})
        return True

    def log_picking(self, cr, uid, ids, context=None):
        """ This function will create log messages for picking.
        @param cr: the database cursor
        @param uid: the current user's ID for security checks,
        @param ids: List of Picking Ids
        @param context: A standard dictionary for contextual values
        """
        if context is None:
            context = {}
        data_obj = self.pool.get('ir.model.data')
        for pick in self.browse(cr, uid, ids, context=context):
            msg=''
            if pick.auto_picking:
                continue
            type_list = {
                'out':_("Delivery Order"),
                'in':_('Reception'),
                'internal': _('Internal picking'),
            }
            view_list = {
                'out': 'view_picking_out_form',
                'in': 'view_picking_in_form',
                'internal': 'view_picking_form',
            }
            message = type_list.get(pick.type, _('Document')) + " '" + (pick.name or '?') + "' "
            if pick.min_date:
                msg= _(' for the ')+ datetime.strptime(pick.min_date, '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y')
            state_list = {
                'confirmed': _('is scheduled %s.') % msg,
                'assigned': _('is ready to process.'),
                'cancel': _('is cancelled.'),
                'done': _('is done.'),
                'auto': _('is waiting.'),
                'draft': _('is in draft state.'),
            }
            res = data_obj.get_object_reference(cr, uid, 'stock', view_list.get(pick.type, 'view_picking_form'))
            context.update({'view_id': res and res[1] or False})
            message += state_list[pick.state]
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        picking = self.browse(cr, uid, id, context=context)
        allow_copy = False
        if default:
            if 'allow_copy' in default:
                if default['allow_copy'] == True:
                    allow_copy = True

        if allow_copy == False:
            if picking.type == 'in':
                raise osv.except_osv(_('Error!'), _('cannot duplicate incoming'))
            if picking.type == 'out':
                raise osv.except_osv(_('Error!'), _('cannot duplicate delivery order'))
        return super(stock_picking, self).copy(cr, uid, id, default, context)

    def revert_invoice(self, cr, uid, ids, context=None):
        account_invoice_obj = self.pool.get('account.invoice')
        for pick in self.browse(cr, uid, ids, context=context):
            if pick.account_invoice_ids:
                raise osv.except_osv(_('Error!'), _('cannot revert to non invoiced until delete the related invoice'))
            self.write(cr, uid, pick.id, {'invoice_state':'2binvoiced',}, context=context)

        return True

    def draft_validate2(self, cr, uid, ids, context=None):
        """ Validates picking directly from draft state.
        @return: True
        """
        wf_service = netsvc.LocalService("workflow")
        self.draft_force_assign(cr, uid, ids)
        for pick in self.browse(cr, uid, ids, context=context):
            if (pick.type == 'out'):
                obj_sequence = self.pool.get('ir.sequence')
                if not pick.pricelist_id.currency_id.do_sequence_id.id:
                    raise osv.except_osv(_('Invalid action !'), _('not do sequence defined in currency ' + str(pick.pricelist_id.currency_id.name)))
                seq_id = pick.pricelist_id.currency_id.do_sequence_id.id
                new_name = obj_sequence.next_by_id(cr, uid, seq_id, None)
                self.write(cr, uid, ids, {'temp_name': pick.name,'name':new_name,})
                if (pick.credit_type == 'Credit Limit'):
                    if pick.approved_credit != True:
                        raise osv.except_osv(_('Warning !'),_('Not enough credit limit, unable to process.'))
                if (pick.credit_type == 'Payment Terms'):
                    if pick.approved_term != True:
                        raise osv.except_osv(_('Warning !'),_('got expired term invoice, unable to process.'))

#            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
#            self.action_process2(cr, uid, [pick.id], context)
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_confirm', cr)
            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
#            move_ids = [x.id for x in pick.move_lines]
#            self.pool.get('stock.move').force_assign(cr, uid, move_ids)


        return True

    def draft_validate3(self, cr, uid, ids, context=None):
        """ Validates picking directly from draft state.
        @return: True
        """
        wf_service = netsvc.LocalService("workflow")
        self.draft_force_assign(cr, uid, ids)
        for pick in self.browse(cr, uid, ids, context=context):
#            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
#            
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_confirm', cr)
            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
            move_ids = [x.id for x in pick.move_lines]
            self.pool.get('stock.move').force_assign(cr, uid, move_ids)
            self.action_process2(cr, uid, [pick.id], context)
        return True

    def action_done2(self, cr, uid, ids, context=None):
        """ Finish the inventory
        @return: True
        """
        if context is None:
            context = {}
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        for inv in self.browse(cr, uid, ids, context=context):
            for sm in inv.move_lines:
                if (sm.location_usage == 'internal'):
                    
                    result1 = cost_price_fifo_obj.stock_move_get(cr, uid, sm.product_id.id, sm.location_id.id, context=context)
                    qty_pick = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                    ret_sm_id = False
                    for rec in sm.move_history_ids:
                        ret_sm_id = rec.id
                    if ret_sm_id:
                        for res1x in result1:
                            if res1x['move_id'] == ret_sm_id:
                                qty_fifo = 0.00
                                if qty_pick > 0:
                                    if qty_pick > res1x['qty_onhand_free']:
                                        qty_fifo = res1x['qty_onhand_free']
                                    else:
                                        qty_fifo = qty_pick
                                    qty_pick = qty_pick - qty_fifo

                                    fifo_control_obj.create(cr, uid, {
                                        'in_move_id': res1x['move_id'],
                                        'out_move_id': sm.id,
                                        'quantity': qty_fifo,
                                        },
                                        context=context)
                    for res1 in result1:
                        qty_fifo = 0.00
                        if qty_pick > 0:
                            if res1['move_id'] != ret_sm_id:
                                if qty_pick > res1['qty_onhand_free']:
                                    qty_fifo = res1['qty_onhand_free']
                                else:
                                    qty_fifo = qty_pick
                                qty_pick = qty_pick - qty_fifo
#                            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(qty_fifo, res1['move_id']))
                                fifo_control_obj.create(cr, uid, {
                                    'in_move_id': res1['move_id'],
                                    'out_move_id': sm.id,
                                    'quantity': qty_fifo,
                                    },
                                    context=context)
                            if (sm.location_dest_usage == 'internal'):
                                internal_move_control_obj.create(cr, uid, {
                                    'internal_move_id': sm.id,
                                    'other_move_id': res1['move_id'],
                                    'quantity': qty_fifo,
                                    },
                                    context=context)
            move_obj.action_done(cr, uid, [x.id for x in inv.move_lines], context=context)
            self.write(cr, uid, [inv.id], {'state':'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

        return True

    def find_date_done(self, cr, uid, move_id, context=None):
        date_done = False
        stock_move_obj = self.pool.get("stock.move")
        if move_id:
            move = stock_move_obj.browse(cr, uid, move_id, context=context)
            if move.picking_id:
                date_done = move.picking_id.do_date
            else:
                if move.stock_inventory_ids:
                    for si in move.stock_inventory_ids:
                        date_done = si.date_done
        return date_done

    def action_process2(self, cr, uid, ids, context=None):
#         raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %('a','b'))

        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, address_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """

        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        res_temp = []
        date_done = {}
        number = 0
        product_obj = self.pool.get('product.product')
        res_partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        invoice_obj = self.pool.get('account.invoice')
        sale_allocated_obj = self.pool.get("sale.allocated")
        cost_price_fifo_obj = self.pool.get("cost.price.fifo")
        fifo_control_obj = self.pool.get("fifo.control")
        internal_move_control_obj = self.pool.get("internal.move.control")
        move_allocated_control_obj = self.pool.get("move.allocated.control")
        sale_order_line_obj = self.pool.get("sale.order.line")
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):


            product_avail = {}
            for move in pick.move_lines:
#                result1 = product_location_wizard_obj.stock_location_get(cr, uid, product.id, context=context)
                result1 = []
                if move.state in ('done', 'cancel'):
                    continue
                product_qty = move.product_qty
                product_uom = move.product_uom.id
                product_price = move.price_unit
                product_currency = move.price_currency_id.id
                if (move.location_usage == 'internal'):
                    qty_pick = uom_obj._compute_qty(cr, uid, product_uom, product_qty, move.product_id.uom_id.id)
                    
                      #outgoing
                    if (pick.type == 'out'):
                        move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('so_line_id','=',move.sale_line_id.id)]), context=context)
                        if move_allocated_control_ids:
                            res_temp = []
                            date_done = {}
                            for move_a in move_allocated_control_ids:
                                number = number + 1
#                                 print self.find_date_done(cr, uid, move_a.move_id.id)
#                                 print find_date_done(move_a)
#                                 print move_a.date_done
                                res_temp.append({
                                                 'number': number,
                                                 'date_done': self.find_date_done(cr, uid, move_a.move_id.id),
                                                 'int_move_id': (move_a.int_move_id and move_a.int_move_id.id) or False,
                                                 'move_id' : move_a.move_id.id,
                                                 're_qty' : move_a.quantity - move_a.rec_quantity,
                                                 }
                                                )
                                date_done[number] = self.find_date_done(cr, uid, move_a.move_id.id)
                            if res_temp:
                                for key, value in sorted(date_done.iteritems(), key=lambda (k,v): (v,k)):
                                    for temp in res_temp:
                                        if temp['number'] == key:
                                            result1.append({
                                                            'date_done': temp['date_done'],
                                                            'move_id' : temp['move_id'],
                                                            're_qty' : temp['re_qty'],
                                                            'int_move_id' : temp['int_move_id'],
                                                            })
                            if result1:
                                for res1 in result1:
                                    if res1['re_qty'] > 0:
                                        if res1['re_qty'] > qty_pick:
                                            fifo_control_obj.create(cr, uid, {
                                                'int_in_move_id' : res1['int_move_id'],
                                                'in_move_id': res1['move_id'],
                                                'out_move_id': move.id,
                                                'quantity': qty_pick,
                                                },
                                                context=context)
                                            qty_pick = 0.00
                                        else:
                                            qty_pick = qty_pick - res1['re_qty']
                                            fifo_control_obj.create(cr, uid, {
                                                'int_in_move_id' : res1['int_move_id'],
                                                'in_move_id': res1['move_id'],
                                                'out_move_id': move.id,
                                                'quantity': res1['re_qty'],
                                                },
                                                context=context)
                              #check her
                    
                    if qty_pick > 0:
                        result_x = cost_price_fifo_obj.stock_move_get(cr, uid, move.product_id.id, move.location_id.id, context=context)
#                         print result_x
                        for res1 in result_x:
                            qty_fifo = 0.00
                            if qty_pick > res1['qty_onhand_free']:
                                qty_fifo = res1['qty_onhand_free']
                            else:
                                qty_fifo = qty_pick
                            qty_pick = qty_pick - qty_fifo
#                             raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(qty_fifo, res1['move_id']))
                            fifo_control_obj.create(cr, uid, {
                                'int_in_move_id' : res1['int_move_id'],
                                'in_move_id': res1['move_id'],
                                'out_move_id': move.id,
                                'quantity': qty_fifo,
                                },
                                context=context)
                            if (move.location_dest_usage == 'internal'):
                                internal_move_control_obj.create(cr, uid, {
                                    'internal_move_id': move.id,
                                    'other_move_id': res1['move_id'],
                                    'quantity': qty_fifo,
                                    },
                                    context=context)

#incoming
                if (pick.type == 'in'):
                    sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.grn')
                    self.write(cr, uid, ids, {'temp_name': pick.name,'name':sequence})
                    product2 = product_obj.browse(cr, uid, move.product_id.id)
                    purchase_order_line_id = move.purchase_line_id.id
#move allocated
############################
                    sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',purchase_order_line_id),('receive','=',False)]), context=context)
                    if sale_allocated_ids:
                        qty_picking = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product2.uom_id.id)
                        for val in sale_allocated_ids:
                            qty_allocated = val.quantity
                            qty_received = val.received_qty
                            if qty_allocated > qty_received:
                                qty_overall = qty_allocated - qty_received
                                if qty_picking > 0:
                                    if qty_picking > qty_overall:
                                        
                                        qty_picking = qty_picking - qty_overall
                                        move_allocated_control_obj.create(cr, uid, {
                                                                                    'move_id': move.id,
                                                                                    'so_line_id': val.sale_line_id.id,
                                                                                    'quantity': qty_overall,
                                                                                    }, context=context)
                                        sale_allocated_obj.unlink(cr, uid, val.id, context=context)
                                        sale_order_line_obj.write(cr, uid, val.sale_line_id.id, {'qty_onhand_allocated': val.sale_line_id.qty_onhand_allocated + qty_overall})
                                    else:
#                                        raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(qty_picking,qty_overall))
                                        sale_order_line_obj.write(cr, uid, val.sale_line_id.id, {'qty_onhand_allocated': val.sale_line_id.qty_onhand_allocated + qty_picking})
                                        move_allocated_control_obj.create(cr, uid, {
                                                                                    'move_id': move.id,
                                                                                    'so_line_id': val.sale_line_id.id,
                                                                                    'quantity': qty_picking,
                                                                                    }, context=context)
                                        if qty_overall - qty_picking > 0:
                                            sale_allocated_obj.write(cr, uid, val.id, {'quantity': (qty_overall - qty_picking) + qty_received})
                                        else:
                                            sale_allocated_obj.unlink(cr, uid, val.id, context=context)
                                        qty_picking = 0

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id in product_avail:
                        product_avail[product.id] += qty
                    else:
                        product_avail[product.id] = product.qty_available
                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product.qty_available <= 0:
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context=context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})
#            if (pick.type == 'out'):
#                
            self.action_move(cr, uid, [pick.id])
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
            delivered_pack_id = pick.id
            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}
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

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
#            if order.state != 'draft':
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.move_lines:
#Try Fix Bug
                val1 += line.price_subtotal
#                val1 += line.price_subtotal
                if (order.type == 'internal'):
                    taxes_id = False
                else:
                    taxes_id = line.taxes_id or False

                if taxes_id:
                    for c in self.pool.get('account.tax').compute_all(cr, uid, taxes_id, line.price_unit, line.product_qty, order.address_id.id, line.product_id.id, order.partner_id)['taxes']:
                        val += c.get('amount', 0.0)
            if not order.pricelist_id:
                res[order.id]['amount_tax']=val
    #                raise osv.except_osv(_('Debug !'),_(str(val1)))
                res[order.id]['amount_untaxed']=val1
                res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']

            else:
                
                res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
    #                raise osv.except_osv(_('Debug !'),_(str(val1)))
                res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
                res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _account_receivable(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for st in self.browse(cr, uid, ids, context=context):
            if (st.type == 'out'):
                res[st.id] = st.partner_id and st.partner_id.credit or 0.00
            else:
                res[st.id] = 0.00
        return res

    def _invoiced(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        invoice_obj = self.pool.get('account.invoice')
        for st in self.browse(cr, uid, ids, context=context):
            invoice_ids = invoice_obj.search(cr, uid, [('picking_id','=',st.id), ('state','in',('open', 'paid'))])
            if invoice_ids:
                res[st.id] = True
            else:
                res[st.id] = False
        return res



    def _get_taxes_invoice(self, cr, uid, move_line, type):
        """ Gets taxes on invoice
        @param move_line: Stock move lines
        @param type: Type of invoice
        @return: Taxes Ids for the move line
        """
        taxes = move_line.taxes_id

        if move_line.picking_id and move_line.picking_id.fiscal_position:
            return self.pool.get('account.fiscal.position').map_tax(
                cr,
                uid,
                move_line.picking_id.fiscal_position,
                taxes
            )
        else:
            return map(lambda x: x.id, taxes)

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        """ Builds the dict containing the values for the invoice line
            @param group: True or False
            @param picking: picking object
            @param: move_line: move_line object
            @param: invoice_id: ID of the related invoice
            @param: invoice_vals: dict used to created the invoice
            @return: dict that will be used to create the invoice line
        """
        if group:
            name = (picking.name or '') + '-' + move_line.name
        else:
            name = move_line.name
        origin = move_line.picking_id.name or ''
        if move_line.picking_id.origin:
            origin += ':' + move_line.picking_id.origin

        if invoice_vals['type'] in ('out_invoice', 'out_refund'):
            account_id = move_line.product_id.product_tmpl_id.\
                    property_account_income.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_income_categ.id
        else:
            account_id = move_line.product_id.product_tmpl_id.\
                    property_account_expense.id
            if not account_id:
                account_id = move_line.product_id.categ_id.\
                        property_account_expense_categ.id
        if invoice_vals['fiscal_position']:
            fp_obj = self.pool.get('account.fiscal.position')
            fiscal_position = fp_obj.browse(cr, uid, invoice_vals['fiscal_position'], context=context)
            account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)
#        print account_id
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(account_id, 'xxx'))

        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move_line.product_uos and move_line.product_uos.id or False
        if not uos_id and invoice_vals['type'] in ('out_invoice', 'out_refund'):
            uos_id = move_line.product_uom.id

        return {
            'stock_move_id': move_line.id,
            'name': name,
            'origin': origin,
            'invoice_id': invoice_id,
            'uos_id': uos_id,
            'product_id': move_line.product_id.id,
            'account_id': account_id,
            'price_unit': move_line.price_unit,
            'discount': 0.00,
            'quantity': move_line.product_qty,
            'invoice_line_tax_id': [(6, 0, self._get_taxes_invoice(cr, uid, move_line, invoice_vals['type']))],
            'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
        }

    def button1(self, cr, uid, ids, context=None):
       #if vals['type'] == 'in':
        stock_ids = self.browse(cr, uid, self.search(cr, uid, [('type','=','in')]), context=context)
        if stock_ids:
            for pp in stock_ids:
                self.write(cr, uid, pp.id, {'do_date': pp.date,
                                            })
#                raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(pp.name, pp.default_code))
        return True

    def button2(self, cr, uid, ids, context=None):
        self._write_data(cr, uid, 'res.partner.child', 'partner_id', context=context)
        self._write_data(cr, uid, 'product.customer', 'partner_id', context=context)
        self._write_data(cr, uid, 'product.supplier', 'partner_id2', context=context)
        self._write_data(cr, uid, 'purchase.order', 'partner_id2', context=context)
        self._write_data(cr, uid, 'sale.order', 'partner_id2', context=context)
        self._write_data(cr, uid, 'account.invoice', 'partner_id2', context=context)
        self._write_data(cr, uid, 'stock.picking', 'partner_id', context=context)
        self._write_data(cr, uid, 'po.value', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.bank.statement.line', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.invoice', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.invoice.line', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.move.line', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.move', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.voucher', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.voucher.line', 'partner_id', context=context)
        self._write_data(cr, uid, 'account.analytic.account', 'partner_id', context=context)
        self._write_data(cr, uid, 'res.partner.bank', 'partner_id', context=context)
        self._write_data(cr, uid, 'res.company', 'partner_id', context=context)
        self._write_data(cr, uid, 'res.partner.event', 'partner_id', context=context)
        self._write_data(cr, uid, 'res.partner', 'parent_id', context=context)
        self._write_data(cr, uid, 'res.request', 'ref_partner_id', context=context)
        self._write_data(cr, uid, 'product.supplierinfo', 'name', context=context)
        self._write_data(cr, uid, 'purchase.order', 'partner_id', context=context)
        self._write_data(cr, uid, 'purchase.order.line', 'partner_id', context=context)
        self._write_data(cr, uid, 'sale.order', 'partner_id', context=context)
        self._write_data(cr, uid, 'sale.order.line', 'order_partner_id', context=context)
        self._write_data(cr, uid, 'stock.picking', 'partner_id', context=context)
        self._write_data(cr, uid, 'stock.move', 'partner_id', context=context)

        return True

    def _write_data(self, cr, uid, obj_val, field_1, context=None):
        
        res_partner_obj = self.pool.get('res.partner')
        res_other_obj = self.pool.get(obj_val)
 ########################################3
        res_partner_ids = res_partner_obj.search(cr, uid, [('ref','in',('8P130017US', '8P130018US', '8P130019US', '8P130028US'))])
        main_partner_ids = res_partner_obj.browse(
            cr, uid, res_partner_obj.search(cr, uid, [('ref','=','8P130102US')]), 
            context=context)
        if main_partner_ids:
            for mp in main_partner_ids:
                main_partner_id = mp.id
###############################
        res_other_ids = res_other_obj.browse(
            cr, uid, 
            res_other_obj.search(cr, uid, 
            [(field_1,'in',res_partner_ids)]), 
            context=context)
        if res_other_ids:
            for roi in res_other_ids:
                res_other_obj.write(cr, uid, [roi.id], 
                {field_1: main_partner_id,
                })
#                if obj_val == 'account.move':
#                    raise osv.except_osv(_('Error!'), _(str(roi.id)))
        return True

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        """ Builds the dict containing the values for the invoice
            @param picking: picking object
            @param partner: object of the partner to invoice
            @param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
            @param journal_id: ID of the accounting journal
            @return: dict that will be used to create the invoice object
        """
        if inv_type in ('out_invoice', 'out_refund'):
            account_id = partner.property_account_receivable.id
        else:
            account_id = partner.property_account_payable.id
        comment = self._get_comment_invoice(cr, uid, picking)
        period_obj = self.pool.get('account.period')
        ctx = context.copy()
        ctx.update({'company_id': picking.company_id.id})

        period_ids = period_obj.find(cr, uid, picking.do_date, context=ctx)
        period_id = period_ids and period_ids[0] or False
#        raise account_id
        invoice_vals = {
            'ref_no': picking.ref_no,
            'invoice_date': picking.invoice_date,
            'invoice_no': picking.invoice_no,
            'header_invoice': picking.header_picking,
            'footer_invoice': picking.footer_picking,
            'period_id': period_id,
            'picking_id': picking.id or False,
            'sale_term_id': partner.sale_term_id.id or False,
            'name': picking.name,
            'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
            'type': inv_type,
            'account_id': account_id,
            'partner_id': partner.id,
            'address_invoice_id': picking.partner_invoice_id and picking.partner_invoice_id.id or False,
            'address_contact_id': picking.partner_order_id and picking.partner_order_id.id or False,
            'comment': comment,
            'payment_term': partner.property_payment_term and partner.property_payment_term.id or False,
            'fiscal_position': picking.fiscal_position and picking.fiscal_position.id or False,
            'date_invoice': picking.do_date or False,
            'company_id': picking.company_id and picking.company_id.id or False,
            'user_id': (picking.user_id and picking.user_id.id) or False,
            'fob_id': (picking.fob_id and picking.fob_id.id) or False,
            'sales_zone_id': (picking.sales_zone_id and picking.sales_zone_id.id) or False,
            'ship_method_id': (picking.ship_method_id and picking.ship_method_id.id) or False,
            'cur_date': picking.do_date or False,
        }
        cur_id = picking.pricelist_id and picking.pricelist_id.currency_id and picking.pricelist_id.currency_id.id or False
        if cur_id:
            invoice_vals['currency_id'] = cur_id
        if journal_id:
            invoice_vals['journal_id'] = journal_id
        return invoice_vals

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            partner = picking.partner_id or False
            if not partner:
                raise osv.except_osv(_('Error, no partner !'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals_group = self._prepare_invoice_group(cr, uid, picking, partner, invoice, context=context)
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals_group, context=context)
            else:
                invoice_vals = self._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
                invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                if move_line.state == 'cancel':
                    continue
                vals = self._prepare_invoice_line(cr, uid, group, picking, move_line,
                                invoice_id, invoice_vals, context=context)
                if vals:

                    invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
                    self._invoice_line_hook(cr, uid, move_line, invoice_line_id)

            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)
        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced',
            }, context=context)
        return res

    def _credit_limit(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        currency_obj = self.pool.get('res.currency')
        invoice_obj = self.pool.get('account.invoice')
        credit_limit = grace = term_days = os_inv_amount= do_amt = do_posted_amt = credit_balance = credit_due_amount = over_due_days = 0.00
        credit_type = False
        for id in ids:
#            print id
            res[id] = {}.fromkeys(field_names, 0.0)
        for st in self.browse(cr, uid, ids, context=context):
            if (st.type == 'out'):
                if st.state != 'cancel':
                    where = [tuple([st.partner_id.id])]
                    cr.execute(
                        "select COALESCE(sum(CASE WHEN COALESCE(pp.currency_id, rc.currency_id) = rc.currency_id THEN "\
                        "round(CAST(sm.price_unit as numeric), 5) * sm.product_qty ELSE "\
                        "round(CAST(sm.price_unit / (select rate from res_currency_rate where currency_id = pp.currency_id and name >=  sp.do_date order by name limit 1) as numeric), 5) * sm.product_qty END), 0) as total "\
                        "from stock_move sm "\
                        "inner join stock_picking sp on sm.picking_id = sp.id "\
                        "left join res_company rc on sp.company_id = rc.id "\
                        "left join product_pricelist pp on sp.pricelist_id = pp.id "\
                        "where sp.partner_id = %s and sp.type = 'out' and sp.state in ('assigned', 'done') and "\
                        "sp.id not in (select picking_id from account_invoice where state in ('open', 'paid') and picking_id is not null)",tuple(where))
                    results = cr.fetchone()
                    if results:
                        do_posted_amt = results[0]
#Fix 19 May 2014
#                credit_limit = 0

                credit_limit = (st.partner_id and st.partner_id.credit_limit) or 0.00
                term_days = (st.partner_id and st.partner_id.sale_term_id and st.partner_id.sale_term_id.days) or 0
                grace = (st.partner_id and st.partner_id.grace) or (st.partner_id and st.partner_id.sale_term_id and st.partner_id.sale_term_id.grace) or 0
#Fix 19 May 2014

#                os_inv_amount = 0
                os_inv_amount = st.partner_id and st.partner_id.credit or 0.00

                company_id = self.pool.get('res.company').browse(cr, uid, st.company_id.id, context=context) or False
                ptype_src = company_id and company_id.currency_id and company_id.currency_id.id or False
                org_src = st.pricelist_id and st.pricelist_id.currency_id and st.pricelist_id.currency_id.id or False
#Fix 19 May 2014
                do_amt = (ptype_src and org_src and currency_obj.compute(cr, uid, org_src, ptype_src, st.amount_total, round=False)) or 0.00
#                do_amt = 0.00

                credit_balance = (credit_limit > 0.00 and credit_limit - os_inv_amount - do_posted_amt) or 0.00

                credit_due_amount = (do_amt > credit_balance and ((credit_balance > 0 and do_amt - credit_balance) or do_amt)) or 0.00

                invoice_ids = invoice_obj.search(cr, uid, [('partner_id','=',st.partner_id.id),('state','=','open'), ('type','=','out_invoice')], order='date_invoice', limit=1)
                if invoice_ids:
                    for inv in invoice_obj.browse(cr, uid, invoice_ids):
                        sale_term_id = inv.sale_term_id or False
                        if sale_term_id:
                            d = datetime.strptime(inv.date_invoice, '%Y-%m-%d')
                            delta = datetime.now() - d
                            daysremaining = delta.days
                            gracedays = 0
                            partner_grace = st.partner_id and st.partner_id.grace or 0
                            sale_grace = sale_term_id.grace or 0
                            if partner_grace > 0:
                                gracedays = partner_grace
                            else:
                                gracedays = sale_grace
                            termdays = sale_term_id.days
                            over_due_days = daysremaining - (termdays + gracedays)
#Fix 19 May 2014
                credit_type = False
#                credit_type = (do_amt > credit_balance and credit_limit > 0 and "Credit Limit") or (st.overdue_days > 0 and "Payment Terms") or False

        for f in field_names:
            c = context.copy()
            if f == 'credit_limit':
                result = credit_limit
            if f == 'days':
                result = term_days
            if f == 'grace':
                result = grace
            if f == 'account_receivable':
                result = os_inv_amount
            if f == 'do_amt':
                result = do_amt
            if f == 'do_posted_amt':
                result = do_posted_amt
            if f == 'credit_balance':
                result = credit_balance
            if f == 'credit_due_amount':
                result = credit_due_amount
            if f == 'overdue_days':
                result = over_due_days
            for id in ids:
                res[id][f] = result
        return res

    def _credit_type(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        credit_type = ''
        for st in self.browse(cr, uid, ids, context=context):
            credit_type = (st.do_amt > st.credit_balance and st.credit_limit > 0 and "Credit Limit") or (st.overdue_days > 0 and "Payment Terms") or False
#            credit_type = 'testing'
            res[st.id] = credit_type
        return res


    _columns = {
        'user_id': fields.many2one('res.users', 'Salesman', select=True, readonly=True),
        'temp_name': fields.char('Temp No', size=64, readonly=True),
        'created_vals': fields.boolean('Create Vals', invisible=True),
        'header_picking': fields.text('Header'),
        'footer_picking': fields.text('Footer'),
        'do_date': fields.date('Do Date', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}),
        'invoice_date': fields.date('Supplier Invoice Date'),
        'invoice_no': fields.char('Supplier Invoice No', size=64),
        'ref_no': fields.char('Reference No', size=64),
        'country_org_id': fields.many2one('res.country', 'Country of Origin'),
        'country_des_id': fields.many2one('res.country', 'Country of Destination'),
        'po_ids2': fields.many2many('purchase.order', 'purchase_order_picking_rel', 'picking_id', 'order_id', 'Related Purchase', readonly=True),
        'res_consigning_id': fields.many2one('res.consigning', 'Consigning'),
        'res_note_user_id': fields.many2one('res.note.user', 'Note User'),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True,),
        'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True,),
        'partner_order_id': fields.many2one('res.partner.address', 'Ordering Contact', readonly=True,),
        'partner_shipping_id': fields.many2one('res.partner.address', 'Shipping Address', readonly=True,),
        'partner_child_id': fields.many2one('res.partner.child', 'Supplier Branch', readonly=True,),
        'ship_method_id': fields.many2one('shipping.method','Ship Method', readonly=True),
        'fob_id': fields.many2one('fob.point.key', 'FOB Point Key', select=True, readonly=True,),
        'sales_zone_id': fields.many2one('res.partner.sales.zone','Sales Zone',readonly=True),
        'sale_term_id': fields.many2one('sale.payment.term', 'Payment Term', select=True, readonly=True,),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True),
        'invoiced': fields.function(_invoiced, string='Invoiced', type='boolean'),
        'credit_limit': fields.function(_credit_limit, multi='credit_limit', type='float', string='Credit Limit'),
        'days': fields.function(_credit_limit, multi='credit_limit', type='float', string='Payment Term Days'),
        'grace': fields.function(_credit_limit, multi='credit_limit', type='float', string='Grace Days Given'),
        'account_receivable': fields.function(_credit_limit, multi='credit_limit', type='float', string='OS Inv Amount'),
        'credit_type': fields.function(_credit_type, type='char', string='Type'),
        'do_amt': fields.function(_credit_limit, multi='credit_limit', type='float', string='Total DO Amt'),
        'do_posted_amt': fields.function(_credit_limit, multi='credit_limit', type='float', digits_compute=dp.get_precision('Purchase Price'), string='Total DO Posted'),
        'credit_balance': fields.function(_credit_limit, multi='credit_limit', type='float', string='Credit Limit Bal/Exc'),
        'credit_due_amount': fields.function(_credit_limit, multi='credit_limit', type='float', string='Credit Limit Due Amt'),
        'overdue_days': fields.function(_credit_limit, multi='credit_limit', type='float', string='Max Overdue Days'),
        'amount_untaxed': fields.function(_amount_all, string='Untaxed Amount', multi="sums", help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, string='Taxes', multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, string='Total', multi="sums",help="The total amount"),
        'account_invoice_ids': fields.one2many('account.invoice', 'picking_id', 'Invoices', readonly=True),
        'move_lines': fields.one2many('stock.move', 'picking_id', 'Internal Moves', states={'done': [('readonly', True)], 'assigned': [('readonly', True)],'cancel': [('readonly', True)]}),
        'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', readonly=True),
        'approved_credit': fields.boolean('approved credit', invisible=True),
        'approved_term': fields.boolean('approved Term', invisible=True),
        'credit_approver':fields.many2one('res.users', 'Credit Limit Approved By'),
        'credit_date': fields.datetime('Credit Limit Approved Date'),
        'term_approver':fields.many2one('res.users', 'Payment Terms Approved By'),
        'term_date': fields.datetime('Payment Terms Approved Date'),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Control",
            select=True, required=True, readonly=True),

    }
stock_picking()

class stock_move(osv.osv):

    _inherit = "stock.move"
    _description = "Stock Move"

    def _get_accounting_data_for_valuation(self, cr, uid, move, context=None):
        """
        Return the accounts and journal to use to post Journal Entries for the real-time
        valuation of the move.

        :param context: context dictionary that can explicitly mention the company to consider via the 'force_company' key
        :raise: osv.except_osv() is any mandatory account or journal is not defined.
        """
        product_obj=self.pool.get('product.product')
        accounts = product_obj.get_product_accounts(cr, uid, move.product_id.id, context)

        if move.location_id.valuation_out_account_id:
            acc_src = move.location_id.valuation_out_account_id.id
        else:
            acc_src = accounts['stock_account_input']

        if move.location_dest_id.valuation_in_account_id:
            acc_dest = move.location_dest_id.valuation_in_account_id.id
        else:
            acc_dest = accounts['stock_account_output']

        if not move.picking_id:
            for si in move.stock_inventory_ids:
                si_type = si.int_type_id.type
                if si_type == 'addiction':
                    acc_src = si.int_type_id and si.int_type_id.property_stock_input and si.int_type_id.property_stock_input.id or False
                    if not acc_src:
                        raise osv.except_osv(_('Error!'),  _('There is no physical inventory input account defined for this product: "%s" (id: %d)') % \
                            (move.product_id.name, move.product_id.id,))
                else:
                    acc_dest = si.int_type_id and si.int_type_id.property_stock_output and si.int_type_id.property_stock_output.id or False
                    if not acc_dest:
                        raise osv.except_osv(_('Error!'),  _('There is no physical inventory output account defined for this product: "%s" (id: %d)') % \
                        (move.product_id.name, move.product_id.id,))

        acc_valuation = accounts.get('property_stock_valuation_account_id', False)
        journal_id = accounts['stock_journal']

        if acc_dest == acc_valuation:
            raise osv.except_osv(_('Error!'),  _('Can not create Journal Entry, Output Account defined on this product and Valuation account on category of this product are same.'))

        if acc_src == acc_valuation:
            raise osv.except_osv(_('Error!'),  _('Can not create Journal Entry, Input Account defined on this product and Valuation account on category of this product are same.'))

        if not acc_src:
            raise osv.except_osv(_('Error!'),  _('There is no stock input account defined for this product or its category: "%s" (id: %d)') % \
                                    (move.product_id.name, move.product_id.id,))
        if not acc_dest:
            raise osv.except_osv(_('Error!'),  _('There is no stock output account defined for this product or its category: "%s" (id: %d)') % \
                                    (move.product_id.name, move.product_id.id,))
        if not journal_id:
            raise osv.except_osv(_('Error!'), _('There is no journal defined on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        if not acc_valuation:
            raise osv.except_osv(_('Error!'), _('There is no inventory Valuation account defined on the product category: "%s" (id: %d)') % \
                                    (move.product_id.categ_id.name, move.product_id.categ_id.id,))
        return journal_id, acc_src, acc_dest, acc_valuation

    def onchange_internal_dest_id(self, cr, uid, ids, location_id, location_dest_id, context=None):
        res = {}
        if location_id:
            if location_dest_id:
                if location_id == location_dest_id:
                    res['warning'] = {'title': _('Warning'), 'message': _('Destination Location cannot same with Source Location')}
                    res['value'] = {'location_dest_id' : False}
        return res

    def _create_product_valuation_moves(self, cr, uid, move, context=None):
        """
        Generate the appropriate accounting moves if the product being moves is subject
        to real_time valuation tracking, and the source or destination location is
        a transit location or is outside of the company.
        """
        product_uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        
#        if move.id == 943:
#            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(move.id, '2xxxx'))
        if move.product_id.valuation == 'real_time': # FIXME: product valuation should perhaps be a property?
            if context is None:
                context = {}
            inventory_date = context.get('inventory_date',False)
            inventory_date = inventory_date and datetime.strptime(inventory_date, '%Y-%m-%d %H:%M:%S')
            src_company_ctx = dict(context,force_company=move.location_id.company_id.id)
            dest_company_ctx = dict(context,force_company=move.location_dest_id.company_id.id)
            account_moves = []
            # Outgoing moves (or cross-company output part)
            if move.location_id.company_id \
                and (move.location_id.usage == 'internal' and move.location_dest_id.usage != 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, src_company_ctx)

                fifo_control_ids = fifo_control_obj.browse(
                    cr, uid, fifo_control_obj.search(cr, uid, [('out_move_id','=',move.id)]), 
                    context=context)
                if fifo_control_ids:
                    int_res = []
                    res_temp = []
                    result1 = []
                    date_done = {}
                    int_number = 0
                    for move_a in fifo_control_ids:
                        int_number = int_number + 1
                        res_temp.append({
                                         'number': int_number,
                                         'allocated_qty': move_a.quantity,
                                         'move_id' : move_a.in_move_id.id,
                                         'int_move_id' : (move_a.int_in_move_id and move_a.int_in_move_id.id) or False,
                                         })
                        date_done[int_number] = self.pool.get('stock.move').browse(cr, uid, move_a.in_move_id.id, context=None).picking_id.do_date
    
                    for key, value in sorted(date_done.iteritems(), key=lambda (k,v): (v,k)):
                        for temp in res_temp:
                            if temp['number'] == key:
                                result1.append({
                                                'number': temp['number'],
                                                'allocated_qty' : temp['allocated_qty'],
                                                'move_id' : temp['move_id'],
                                                'int_move_id' : temp['int_move_id'],
                                                })
                    if result1:
                        
                        for res1 in result1:
                            if res1['int_move_id']:
                                mov_all = self.pool.get('stock.move').browse(cr, uid, res1['int_move_id'], context=None)
                            else:
                                mov_all = self.pool.get('stock.move').browse(cr, uid, res1['move_id'], context=None)
                            reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid,res1['allocated_qty'], mov_all, src_company_ctx)
                            account_moves += [(journal_id, self._create_account_move_line(cr, uid, res1['allocated_qty'], move, acc_valuation, acc_dest, reference_amount, reference_currency_id, context))]

            # Incoming moves (or cross-company input part)
            if move.location_dest_id.company_id \
                and (move.location_id.usage != 'internal' and move.location_dest_id.usage == 'internal'\
                     or move.location_id.company_id != move.location_dest_id.company_id):
                journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation(cr, uid, move, dest_company_ctx)
                qty_m = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)
                reference_amount, reference_currency_id = self._get_reference_accounting_values_for_valuation(cr, uid, qty_m, move, src_company_ctx)
                account_moves += [(journal_id, self._create_account_move_line(cr, uid, qty_m, move, acc_src, acc_valuation, reference_amount, reference_currency_id, context))]

            move_obj = self.pool.get('account.move')
            for j_id, move_lines in account_moves:
                if move.picking_id:
                    date_m = move.picking_id.do_date
                else:
                    date_m = inventory_date and inventory_date.strftime('%Y-%m-%d') or datetime.now().strftime('%Y-%m-%d')
                period_ids = self.pool.get('account.period').find(cr, uid, date_m, context=None)
                period_id = period_ids and period_ids[0] or False
                
                move_obj.create(cr, uid,
                    {'period_id':period_id,
                     'date':date_m,
                     'journal_id': j_id,
                     'line_id': move_lines,
                     'picking_id': move.picking_id and move.picking_id.id or False,
                     'ref': move.picking_id and move.picking_id.name})

    def _get_reference_accounting_values_for_valuation(self, cr, uid, qty_m, move, context=None):
        """
        Return the reference amount and reference currency representing the inventory valuation for this move.
        These reference values should possibly be converted before being posted in Journals to adapt to the primary
        and secondary currencies of the relevant accounts.
        """
        product_uom_obj = self.pool.get('product.uom')

        # by default the reference currency is that of the move's company
        reference_currency_id = move.company_id.currency_id.id

        default_uom = move.product_id.uom_id.id
        qty = qty_m

        # if product is set to average price and a specific value was entered in the picking wizard,
        # we use it

        reference_amount = qty * move.price_unit
        reference_currency_id = move.price_currency_id.id or reference_currency_id

        # Otherwise we default to the company's valuation price type, considering that the values of the
        # valuation field are expressed in the default currency of the move's company.

        return reference_amount, reference_currency_id

    def _create_account_move_line(self, cr, uid, qty, move, src_account_id, dest_account_id, reference_amount, reference_currency_id, context=None):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given stock move.
        """
        # prepare default values considering that the destination accounts have the reference_currency_id as their main currency
        inventory_date = context.get('inventory_date',False)
        print inventory_date
        inventory_date = inventory_date and datetime.strptime(inventory_date, '%Y-%m-%d %H:%M:%S')
#        (datetime.strptime(move.date, '%Y-%m-%d %H:%M:%S') + relativedelta(days=delay or 0)).strftime('%Y-%m-%d'),
        if move.picking_id:
            date_m = move.picking_id.do_date
        else:
            date_m = inventory_date and inventory_date.strftime('%Y-%m-%d') or datetime.now().strftime('%Y-%m-%d')
#        print date_m
#        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))

        partner_id = (move.picking_id.address_id and move.picking_id.address_id.partner_id and move.picking_id.address_id.partner_id.id) or False
        period_ids = self.pool.get('account.period').find(cr, uid, date_m, context=None)
        period_id = period_ids and period_ids[0] or False
        debit_line_vals = {
                    'period_id': period_id,
                    'name': move.name,
                    'product_id': move.product_id and move.product_id.id or False,
                    'quantity': qty,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': date_m,
                    'exrate': 1.00,
                    'partner_id': partner_id,
                    'debit': float_round(reference_amount,2),
                    'account_id': dest_account_id,
                    'stock_move_id': move.id,
        }
        credit_line_vals = {
                    'period_id': period_id,
                    'name': move.name,
                    'product_id': move.product_id and move.product_id.id or False,
                    'quantity': qty,
                    'ref': move.picking_id and move.picking_id.name or False,
                    'date': date_m,
                    'exrate': 1.00,
                    'partner_id': partner_id,
                    'credit': float_round(reference_amount,2),
                    'account_id': src_account_id,
                    'stock_move_id': move.id,
        }

        # if we are posting to accounts in a different currency, provide correct values in both currencies correctly
        # when compatible with the optional secondary currency on the account.
        # Financial Accounts only accept amounts in secondary currencies if there's no secondary currency on the account
        # or if it's the same as that of the secondary amount being posted.
        account_obj = self.pool.get('account.account')
        product_product_obj = self.pool.get('product.product')
        src_acct, dest_acct = account_obj.browse(cr, uid, [src_account_id, dest_account_id], context=context)
        src_main_currency_id = src_acct.company_id.currency_id.id
        dest_main_currency_id = dest_acct.company_id.currency_id.id
        cur_obj = self.pool.get('res.currency')
        obj_currency_rate = self.pool.get('res.currency.rate')
        if reference_currency_id != src_main_currency_id:
            # fix credit line:
            if move.picking_id:
                tgl = move.picking_id.do_date
                if not tgl:
                    tgl = time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    tgl = datetime.strptime(tgl, '%Y-%m-%d').date()

            ref_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', reference_currency_id),
                                                          ('name','<=', tgl)
                                                          ], order='name DESC', limit=1)
            if ref_rate_ids:
                ref_rate_id = ref_rate_ids[0]
            else:
                raise osv.except_osv(_('Error'), _('No rate found \n' \
                    'for the currency: %s \n' \
                    'at the date: %s') % (cur_obj.browse(cr, uid, reference_currency_id, context=context).symbol, tgl))
            src_main_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', src_main_currency_id),
                                                          ('name','<=', tgl)
                                                          ], order='name DESC', limit=1)
            if src_main_rate_ids:
                src_main_rate_id = src_main_rate_ids[0]
            else:
                raise osv.except_osv(_('Error'), _('No rate found \n' \
                    'for the currency: %s \n' \
                    'at the date: %s') % (cur_obj.browse(cr, uid, src_main_currency_id, context=context).symbol, tgl))
            if ref_rate_id:
                credit_amount = reference_amount * (obj_currency_rate.browse(cr, uid, src_main_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, ref_rate_id, context=None).rate))
                credit_line_vals['credit'] = float_round(credit_amount, 2)
            if (not src_acct.currency_id) or src_acct.currency_id.id == reference_currency_id:
                credit_line_vals.update(cur_date=tgl,exrate=obj_currency_rate.browse(cr, uid, ref_rate_id, context=None).rate, currency_id=reference_currency_id, amount_currency=reference_amount)
        if reference_currency_id != dest_main_currency_id:
            # fix debit line:


            if move.picking_id:
                d_tgl = move.picking_id.do_date
                if not d_tgl:
                    d_tgl = time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    d_tgl = datetime.strptime(d_tgl, '%Y-%m-%d').date()

            d_ref_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', reference_currency_id),
                                                          ('name','<=', d_tgl)
                                                          ], order='name DESC', limit=1)
            if d_ref_rate_ids:
                d_ref_rate_id = d_ref_rate_ids[0]
            else:
                raise osv.except_osv(_('Error'), _('No rate found \n' \
                    'for the currency: %s \n' \
                    'at the date: %s') % (cur_obj.browse(cr, uid, reference_currency_id, context=context).symbol, d_tgl))
            dest_main_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', dest_main_currency_id),
                                                          ('name','<=', d_tgl)
                                                          ], order='name DESC', limit=1)
            if dest_main_rate_ids:
                dest_main_rate_id = dest_main_rate_ids[0]
            else:
                raise osv.except_osv(_('Error'), _('No rate found \n' \
                    'for the currency: %s \n' \
                    'at the date: %s') % (cur_obj.browse(cr, uid, dest_main_currency_id, context=context).symbol, d_tgl))
            if d_ref_rate_id:
                debit_amount = reference_amount * (obj_currency_rate.browse(cr, uid, dest_main_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, d_ref_rate_id, context=None).rate))
                debit_line_vals['debit'] = float_round(debit_amount, 2)
            if (not dest_acct.currency_id) or dest_acct.currency_id.id == reference_currency_id:
                debit_line_vals.update(cur_date=d_tgl,exrate=obj_currency_rate.browse(cr, uid, d_ref_rate_id, context=None).rate,currency_id=reference_currency_id, amount_currency=reference_amount)
        if 'cur_date' not in debit_line_vals:
            debit_line_vals.update(cur_date=date_m,exrate=1.00)
        if 'cur_date' not in credit_line_vals:
            credit_line_vals.update(cur_date=date_m,exrate=1.00)
#        print [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
#        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))
#        
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

    def onchange_internal_quantity(self, cr, uid, ids, product_id, product_qty, qty_onhand_free,
                          product_uom, product_uos):
        product_vals = super(stock_move, self).onchange_quantity(cr, uid, ids,
                            product_id, product_qty, product_uom, product_uos)
        product_product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        if product_id:
            product_product = product_product_obj.browse(cr, uid, product_id, context=None)
            real_qty = product_uom_obj._compute_qty(cr, uid, product_uom, product_qty, product_product.uom_id.id)
            if real_qty > 1:
                if real_qty > qty_onhand_free:
                    product_vals['warning'] = {'title': _('Warning'), 'message': _('product qty cannot more than qty onhand free')}
                    product_vals['value'].update({'product_qty': 0.00,
                                                  'product_uom': product_product.uom_id.id,
                                                  })
            else:
                product_vals['value'].update({'product_qty': 0.00,
                                              'product_uom': product_product.uom_id.id,
                                              })
        return product_vals

    def onchange_internal_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False,  address_id=False, product_uom=False):


        product_location_wizard_obj = self.pool.get('product.location.wizard')
        product_product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        product_vals = super(stock_move, self).onchange_product_id(cr, uid, ids,
                            prod_id, loc_id, loc_dest_id, address_id)
        warning_msgs = ''
        
        if prod_id:
            product_product = product_product_obj.browse(cr, uid, prod_id, context=None)
            result1 = product_location_wizard_obj.stock_location_get(cr, uid, [prod_id], context=None)
            loc_id_updated = False
            qty_on_hand = 0.00
            qty_on_hand_free = 0.00
            qty_on_hand_allocated = 0.00
    #        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))
    #        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))
            location_ids = []
            loc_id2 = False
            for loc in product_product.location_ids:
                if loc.default_key:
                    loc_id2=loc.stock_location_id.id
                location_ids.append(loc.stock_location_id.id)
            if not loc_id:
                loc_id = loc_id2
            if loc_id:
                if result1:
                    for rs in result1:
                        if rs['location_id'] == loc_id:
                            loc_id_updated = loc_id
                            qty_on_hand = rs['qty_available']
                            qty_on_hand_free = rs['qty_free']
                            qty_on_hand_allocated = rs['qty_allocated']

#                    warning_msgs += _("The Source Location selected is not belong to this product")  + "\n\n"
    #            raise osv.except_osv(_('Warning !'),_(str(loc_id_updated)))
    #                if loc_id_updated = 
     #           result['location_id'] = loc_id

#            raise osv.except_osv(_('Warning !'),_(str(location_ids) + str(loc_id_updated)))
#                            raise osv.except_osv(_('Warning !'),_('found ids' + str(loc_id_updated)))
#            raise osv.except_osv(_('Warning !'),_(str(loc_id_updated)))

#            raise osv.except_osv(_('Warning !'),_(str(loc_id_updated)))
            product_vals['domain'] = ({'location_id': [('id','in',location_ids)],
                                       'location_dest_id': [('id','in',location_ids)],
                                       'product_uom': [('category_id','=',product_product.uom_id.category_id.id)],
                                       })
            if not product_uom:
                product_uom = product_product.uom_id.id
            if product_product.uom_id.category_id.id != product_uom_obj.browse(cr, uid, product_uom, context=None).category_id.id:
                warning_msgs += _("Selected UOM does not belong to the same category as the product UOM")  + "\n\n"
                product_uom = product_product.uom_id.id
            if warning_msgs != '':
                product_vals['warning'] = {'title': _('Warning'), 'message': _(warning_msgs)}
            product_vals['value'].update({'location_id': loc_id,
                                          'location_dest_id' : False,
                                          'qty_onhand_r': qty_on_hand,
                                          'qty_onhand_free_r': qty_on_hand_free,
                                          'qty_onhand_allocated_r': qty_on_hand_allocated,
                                          'product_uom': product_uom,
                                          })
#            raise osv.except_osv(_('Test !'),_(str(product_vals)))
            if product_vals['value']['product_qty']:
                 product_vals['value']['product_qty'] = False
#            raise osv.except_osv(_('Warning !'),_(str(product_vals)))
        return product_vals

    def on_change_qty(self, cr, uid, ids, prod_id, loc_id):
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        product_product_obj = self.pool.get('product.product')
        warning_msgs = ''
        product_vals = {}
        if not prod_id:
            return {'value': {'qty_onhand_r': 0.0,
                              'qty_onhand_free_r' : 0.0,
                              'qty_onhand_allocated_r' : 0.0}}
        if not loc_id:
            return {'value': {'qty_onhand_r': 0.0,
                              'qty_onhand_free_r' : 0.0,
                              'qty_onhand_allocated_r' : 0.0}}
        product_product = product_product_obj.browse(cr, uid, prod_id, context=None)
        result1 = product_location_wizard_obj.stock_location_get(cr, uid, [prod_id], context=None)
        loc_id_updated = False
        qty_on_hand = 0.00
        qty_on_hand_free = 0.00
        qty_on_hand_allocated = 0.00
#        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))
#        raise osv.except_osv(_('Warning !'),_('no sale payment term founds in partner'))
        location_ids = []
        if loc_id:
            if result1:
#                if loc_id in result1['location_id']:
#                    loc_id_updated = loc_id

                for rs in result1:
                    if rs['location_id'] == loc_id:
                        loc_id_updated = loc_id
                        qty_on_hand = rs['qty_available']
                        qty_on_hand_free = rs['qty_free']
                        qty_on_hand_allocated = rs['qty_allocated']
        product_vals['value'] = {'qty_onhand_r': qty_on_hand,
                                      'qty_onhand_free_r': qty_on_hand_free,
                                      'qty_onhand_allocated_r': qty_on_hand_allocated,
                                      }
        return product_vals



    def action_delete(self, cr, uid, ids, context=None):
        for mv in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [mv.id], {'state':'draft',}, context=context)

        return self.unlink(cr, uid, ids, context=context)

    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            cur = line.picking_id.pricelist_id.currency_id
            if (line.picking_id.type == 'internal'):
                res[line.id] = 0.00
            if (line.picking_id.type == 'in'):
                taxes_id = line.taxes_id or False
                taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty)
                res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])

            if (line.picking_id.type == 'out'):
                discount = 0.00
                tax_id = line.taxes_id or False
                price = line.price_unit * (1 - (discount or 0.0) / 100.0)
                taxes = tax_obj.compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty)
                res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    def _full_out(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        fifo_control_obj = self.pool.get('fifo.control')
        uom_obj = self.pool.get('product.uom')
        for sm in self.browse(cr, uid, ids, context=context):
            if sm.location_dest_usage == 'internal':
                fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
                if fifo_control_ids:
                    qty_in = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                    qty_out = 0.00
                    for val in fifo_control_ids:
                        qty_out = qty_out + val.quantity
                    if qty_out < qty_in:
                        res[sm.id] = "Half Out"
                    else:
                        res[sm.id] = "Full Out"
                else:
                    res[sm.id] = "non Full Out"
            else:
                res[sm.id] = ""
        return res

    _columns = {
        'write_off': fields.boolean('Write Off', help="Tick The Write Off When want to write off all the qty"),
        'product_customer_id' : fields.related('sale_line_id', 'product_customer_id', type='many2one', relation="product.customer",
                                        string="Customer Part No.",
                                        store=False, readonly=True),
        'sale_id' : fields.related('sale_line_id', 'order_id', type='many2one', relation="sale.order",
                                        string="SO No",
                                        store=False, readonly=True),
        'client_order_ref': fields.related('sale_id', 'client_order_ref', string="Customer PO", type='char', relation='sale.order', store=False, readonly=True),
        'taxes_id': fields.many2many('account.tax', 'picking_taxe', 'picking_id', 'tax_id', 'Taxes'),
        'stock_inventory_ids': fields.many2many('stock.inventory', 'stock_inventory_move_rel', 'move_id', 'inventory_id', 'Created Inventories'),
        'location_usage': fields.related('location_id','usage', type='char', readonly=True, size=64, relation='stock.location', string='Location Usage'),
        'location_dest_usage': fields.related('location_dest_id','usage', type='char', readonly=True, size=64, relation='stock.location', string='Location Usage'),
        'qty_onhand_r': fields.float('Quantity On Hand', digits_compute=dp.get_precision('Product UoM')),
        'qty_onhand_free_r': fields.float('Quantity On Hand Free', digits_compute=dp.get_precision('Product UoM')),
        'qty_onhand_allocated_r': fields.float('Quantity On Hand Allocated', digits_compute=dp.get_precision('Product UoM')),
        'full_out': fields.function(_full_out, string='Type', type='char'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Purchase Price')),
    }

stock_move()


class stock_inventory(osv.osv):

    _inherit = "stock.inventory"
    _description = "Inventory"

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        raise osv.except_osv(_('Error!'), _('cannot duplicate Physical Inventory'))
        return super(stock_inventory, self).copy(cr, uid, id, default, context)

    def action_approve_zero(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_zero': True, 'zero_approver': uid, 'zero_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def action_undo_zero(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'approved_zero': False, 'zero_approver': False, 'zero_date':False})
        return True

    _columns = {
        'name': fields.char('Inventory Reference', size=64, readonly=True),
        'int_type_id': fields.many2one('int.type', 'Sequence Type', required=True, states={'done': [('readonly', True)]}),
        'reason': fields.char('Reason', size=64),
        'move_ids': fields.many2many('stock.move', 'stock_inventory_move_rel', 'inventory_id', 'move_id', 'Created Moves', states={'done': [('readonly', True)]}),
        'opening_bal': fields.boolean('Opening Balance', help="Tick The Opening Balance when want do the Opening Balance Transaction", states={'done': [('readonly', True)]}),
        'approved_zero': fields.boolean('approved zero', invisible=True),
        'zero_approver':fields.many2one('res.users', 'Zero Allowed Approved By'),
        'zero_date': fields.datetime('Zero Allowed Approved Date'),
    }

    def create(self, cr, user, vals, context=None):
        if 'int_type_id' in vals:
            obj_int_type = self.pool.get('int.type')
            obj_sequence = self.pool.get('ir.sequence')
            int_type = obj_int_type.browse(cr, user, vals['int_type_id'], context=None)
            seq_id = (int_type.sequence_id and int_type.sequence_id.id) or False
            if not seq_id:
                raise osv.except_osv(_('Invalid action !'), _('no default sequence found in "' + str(int_type.name) + '" Physical Inventories Type.'))

            new_name = obj_sequence.next_by_id(cr, user, seq_id, None)
            vals.update({'name' : new_name,
                     })
        new_id = super(stock_inventory, self).create(cr, user, vals, context)
        return new_id

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirm the inventory and writes its finished date
        @return: True
        """
        if context is None:
            context = {}
        # to perform the correct inventory corrections we need analyze stock location by
        # location, never recursively, so we use a special context
        product_context = dict(context, compute_child=False)
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        
        location_obj = self.pool.get('stock.location')
        for inv in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for line in inv.inventory_line_id:
                pid = line.product_id.id
                product_context.update(uom=line.product_uom.id, date=inv.date, prodlot_id=line.prod_lot_id.id)
                amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]
                
                type = inv.int_type_id.type

                lot_id = line.prod_lot_id.id
                if line.product_qty > 0:
                    location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                    value = {
                        'name': 'INV:' + str(line.inventory_id.id) + ':' + line.inventory_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'date': inv.date,
                    }
                    if type == 'addiction':
#                         raise osv.except_osv(_('Error !'), _(str(line.price_unit)))

                        if line.price_unit <= 0 and inv.approved_zero == False:
                            raise osv.except_osv(_('Error !'), _('cannot process, found zero price unit for the product, can bypass it with permission.'))

                        value.update( {
                            'product_qty': line.product_qty,
                            'price_unit' : line.price_unit,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                            
                        })
                    else:

                        result1 = product_location_wizard_obj.stock_location_get(cr, uid, [line.product_id.id], context=None)
                        qty_available = 0.00
                        qty_allocated = 0.00
                        if result1:
                            for res_f1 in result1:
                                if res_f1['location_id'] == line.location_id.id:
                                    qty_available = res_f1['qty_available']
                                    qty_allocated = res_f1['qty_allocated']

                        if line.product_qty > (qty_available - qty_allocated):
                            raise osv.except_osv(_('Error !'), _('cannot process, the product qty entered is more than qty onhand free for the product.('+ str(line.product_id.name) + ')'))

                        value.update( {
                            'product_qty': line.product_qty,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
                        })
                    move_ids.append(self._inventory_line_hook(cr, uid, line, value))
            if not move_ids:
                raise osv.except_osv(_('Error !'), _('cannot process, no product to process.'))

            self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
            self.pool.get('stock.move').action_confirm(cr, uid, move_ids, context=context)
            self.action_done2(cr, uid, [inv.id], context)
        return True

    def action_done2(self, cr, uid, ids, context=None):
        """ Finish the inventory
        @return: True
        """
        if context is None:
            context = {}
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')

        for inv in self.browse(cr, uid, ids, context=context):
            for sm in inv.move_ids:
                if (sm.location_usage == 'internal'):
                    result1 = cost_price_fifo_obj.stock_move_get(cr, uid, sm.product_id.id, sm.location_id.id, context=context)
#                     print result1
#                     raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %('a','b'))

                    qty_pick = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                    for res1 in result1:
                        qty_fifo = 0.00
                        if qty_pick > 0:
                            if qty_pick > res1['qty_onhand_free']:
                                qty_fifo = res1['qty_onhand_free']
                            else:
                                qty_fifo = qty_pick
                            qty_pick = qty_pick - qty_fifo

                            fifo_control_obj.create(cr, uid, {
                                'int_in_move_id' : res1['int_move_id'],
                                'in_move_id': res1['move_id'],
                                'out_move_id': sm.id,
                                'quantity': qty_fifo,
                                },
                                context=context)
                            if (sm.location_dest_usage == 'internal'):
                                internal_move_control_obj.create(cr, uid, {
                                    'internal_move_id': sm.id,
                                    'other_move_id': res1['move_id'],
                                    'quantity': qty_fifo,
                                    },
                                    context=context)
                context['inventory_date'] = inv.date
            move_obj.action_done(cr, uid, [x.id for x in inv.move_ids], context=context)
            self.write(cr, uid, [inv.id], {'state':'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return True

    def action_trig_create_acc_move(self, cr, uid, ids, context=None):
        """ Finish the inventory
        @return: True
        """
        if context is None:
            context = {}
        stock_inventory_obj = self.pool.get('stock.inventory')
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')

#        picking_ids = picking_obj.search(cr, uid, [('type', 'in', ('in', 'out')),('state', '=', 'done')])
#        for picking in picking_obj.browse(cr, uid, picking_ids):
#            for stock_move in picking.move_lines:
#                move_obj._create_product_valuation_moves(cr, uid, stock_move, context=context)
        stock_inventory_ids = stock_inventory_obj.search(cr, uid, [])
        for si in stock_inventory_obj.browse(cr, uid, stock_inventory_ids):
            context['inventory_date'] = si.date
            for move in si.move_ids:
                move_obj._create_product_valuation_moves(cr, uid, move, context=context)
#        for inv in self.browse(cr, uid, ids, context=context):
#            
#            #move_obj.action_done(cr, uid, [x.id for x in inv.move_ids], context=context)
#            
#            for move in inv.move_ids:
#                move_obj._create_product_valuation_moves(cr, uid, move, context=context)
        return True

stock_inventory()

class stock_inventory_line(osv.osv):

    _inherit = "stock.inventory.line"
    _description = "Inventory Line"

    _columns = {
        'note': fields.text('Note'),
        'write_off': fields.boolean('Write Off', help="Tick The Write Off When want to write off all the qty"),
        'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Account'), help="Input Unit Price Only When do the adding qty"),
        'qty_available' : fields.float('Quantity on Hand'),
        'qty_allocated': fields.float('Quantity On Hand Allocated'),
    }

    def on_change_product_id2(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        """ Changes UoM and name if product_id changes.
        @param location_id: Location id
        @param product: Changed product_id
        @param uom: UoM product
        @return:  Dictionary of changed values
        """
        if not product:
            return {'value': {'product_qty': 0.0, 'product_uom': False, 'write_off': False}}
        obj_product = self.pool.get('product.product').browse(cr, uid, product)
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        uom_id = obj_product.uom_id.id
        warning = False
        location_ids = []
        for loc in obj_product.location_ids:
            location_ids.append(loc.stock_location_id.id)
            if (loc.default_key == True):
                default_location_id = loc.stock_location_id.id
        if location_id:
            if location_id not in location_ids:
                warning = {'title': _('Warning'), 'message': _('The Selected Location is not belong to this product.')}
                location_id = default_location_id or False
        else:
            location_id = default_location_id
        result1 = product_location_wizard_obj.stock_location_get(cr, uid, [product], context=None)
        qty_available = 0.00
        qty_allocated = 0.00
        if result1:
            for res_f1 in result1:
                if res_f1['location_id'] == location_id:
                    qty_available = res_f1['qty_available']
                    qty_allocated = res_f1['qty_allocated']
        domain = {'location_id': [('id','in',location_ids)]}
        result = { 'write_off': False,
                  'product_uom': obj_product.uom_id.id,
                    'location_id' : location_id}
#        raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(obj_product.uom_id.name, result))

        if warning:
            res = {'value': result, 'domain': domain, 'warning': warning}
        else:
            res = {'value': result, 'domain': domain}
        return res

    def on_change_qty(self, cr, uid, ids, location_id, product, product_qty, wrt_off):
        """ Changes UoM and name if product_id changes.
        @param location_id: Location id
        @param product: Changed product_id
        @param uom: UoM product
        @return:  Dictionary of changed values
        """
        if not product:
            return {'value': {'product_qty': 0.0,
                              'qty_available' : 0.0,
                              'qty_allocated' : 0.0,
                              'product_uom': False}}
        if not location_id:
            return {'value': {'product_qty': 0.0,
                              'qty_available' : 0.0,
                              'qty_allocated' : 0.0,
                              'product_uom': False}}
        result = {}
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        warning = False
        result1 = product_location_wizard_obj.stock_location_get(cr, uid, [product], context=None)
        qty_available = 0.00
        qty_allocated = 0.00
        if result1:
            for res_f1 in result1:
                if res_f1['location_id'] == location_id:
                    qty_available = res_f1['qty_available']
                    qty_allocated = res_f1['qty_allocated']
                    result.update({
                           'qty_available' : qty_available,
                           'qty_allocated' : qty_allocated})
        if wrt_off:
            product_qty = qty_allocated
            result.update({
                           'product_qty' : product_qty,
                           'price_unit': 0.00})
        else:
#        raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(result, product_qty))
            if product_qty < qty_allocated:
                warning = {'title': _('Warning'), 'message': _('The Qty Entered cannot below from qty allocated (' + str(qty_allocated) + ').')}
                product_qty = qty_available
                result.update({
                        'product_qty' : product_qty,
                        'qty_available' : qty_available,
                        'qty_allocated' : qty_allocated})
    #        raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(result, 'xx'))
    #        result = {
    #                    'product_qty' : product_qty,
    #                    'qty_available' : qty_available,
    #                    'qty_allocated' : qty_allocated}
        if warning:
            res = {'value': result, 'warning': warning}
        else:
            res = {'value': result}
        return res

    def on_change_uom(self, cr, uid, ids, product):
        if not product:
            return {'value': {'product_uom': False}}
        obj_product = self.pool.get('product.product').browse(cr, uid, product)
        uom_id = obj_product.uom_id.id

        result = { 'product_uom': uom_id}
#        raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(obj_product.uom_id.name, result))

        res = {'value': result}
        return res

stock_inventory_line()


class stock_location(osv.osv):
    _inherit = "stock.location"
    _columns = {
        'address_id': fields.many2one('res.partner.address', 'Location Address',help="Address of  customer or supplier.", required=True),
    }
stock_location()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
