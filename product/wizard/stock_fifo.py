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

import decimal_precision as dp
from osv import fields, osv
from tools.translate import _
import netsvc
import math
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from operator import itemgetter

class cost_price_fifo(osv.osv_memory):
    _name = "cost.price.fifo"
    _description = "Cost Price FIFO View"

    def internal_get2(self, cr, uid, sm_id, qty_sisa, qty_sold, context=None):
        result1 = []
        res_temp = []
        qty = qty_sisa
        sold_qty = qty_sold
        internal_move_control__obj = self.pool.get('internal.move.control')
        fifo_control_obj = self.pool.get('fifo.control')
        internal_move_control_ids = internal_move_control__obj.browse(cr, uid, internal_move_control__obj.search(cr, uid, [('internal_move_id','=',sm_id)]), context=context)
        if internal_move_control_ids:
            raise osv.except_osv(_('Debug !'), _(str(internal_move_control_ids)))
            for int in internal_move_control_ids:
                    qty_internal = int.quantity
                    if sold_qty > qty_internal:
                        sold_qty = sold_qty - qty_internal
                    else:
                        qty_internal = qty_internal - sold_qty
                        sold_qty = 0
                        if qty_internal > 0:
                            if qty > 0:
                                if qty_internal > qty:
                                    qty_internal = qty
                                    qty = 0.00
                                else:
                                    qty = qty - qty_internal
                                if int.other_move_id.picking_id:
                                    if int.other_move_id.picking_id.type == 'internal':
                                        fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',int.other_move_id.id)]), context=context)
                                        qty_out = 0.00
                                        if fifo_control_ids:
                                            for val in fifo_control_ids:
                                                if val.out_move_id.id != sm_id:
                                                    qty_out = qty_out + val.quantity
                                        res_temp = self.internal_get(cr, uid, int.other_move_id.id, qty_internal, qty_out)
                                        for res_t in res_temp:
                                            result1.append({
                                                             'move_id': res_t['move_id'],
                                                             'product_qty' : res_t['product_qty'],
                                                             'document_date' : res_t['document_date'],
                                                             })
                                    else:
                                        
                                        result1.append({
                                                        'move_id': int.other_move_id.id,
                                                        'product_qty' : qty_internal,
                                                        'document_date': int.other_move_id.picking_id.do_date,
                                                        })
                                else:
                                    if int.other_move_id.stock_inventory_ids:
                                        for si in int.other_move_id.stock_inventory_ids:
                                            result1.append({
                                                             'move_id': int.other_move_id.id,
                                                             'product_qty' : qty_internal,
                                                             'document_date': si.date_done,
                                                             })
        return result1

    def internal_get(self, cr, uid, sm_id, context=None):
        result1 = []
        res_temp = []
        res_check = []
        internal_move_control_obj = self.pool.get('internal.move.control')
        fifo_control_obj = self.pool.get('fifo.control')
        
        internal_move_control_ids = internal_move_control_obj.browse(cr, uid, internal_move_control_obj.search(cr, uid, [('internal_move_id','=',sm_id)]), context=context)

        if internal_move_control_ids:
            for int in internal_move_control_ids:
                qty_internal = int.quantity
#                if sm_id == 14385:
#                    print int.id
#                    print qty_internal
                if qty_internal > 0:
                    if int.other_move_id.picking_id:
                        if int.other_move_id.picking_id.type == 'internal':
                            res_temp = self.internal_get(cr, uid, int.other_move_id.id,)
#                            if sm_id == 14385:
#                                print int.other_move_id.id
#                                print res_temp
                            for res_t in res_temp:
                                out_fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('out_move_id','=',sm_id),('in_move_id','=',int.other_move_id.id), ('int_in_move_id','=',res_t['move_id'])]), context=None)
                                if not out_fifo_control_ids:
                                    continue
                                check_val = 'sm_id: ' + str(sm_id) + ',in_move_id: ' + str(int.other_move_id.id) + ', int_in_move_id: ' + str(res_t['move_id'])
                                if check_val in res_check:
                                    continue
                                if qty_internal > 0:
                                    res_check.append(check_val)
    #                                if sm_id == 14385:
    #                                    print sm_id
    #                                    print qty_internal
#                                    if sm_id == 14385:
#                                        print int.id
#                                        print qty_internal
                                    result1.append({
                                                     'move_id': res_t['move_id'],
                                                     'product_qty' : qty_internal,
                                                     'document_date' : res_t['document_date'],
                                                     })
                                    qty_internal = qty_internal - res_t['product_qty']
                        else:
#                            print int.other_move_id.id
                            result1.append({
                                            'move_id': int.other_move_id.id,
                                            'product_qty' : qty_internal,
                                            'document_date': int.other_move_id.picking_id.do_date,
                                            })
                    else:
                        if int.other_move_id.stock_inventory_ids:
                            for si in int.other_move_id.stock_inventory_ids:
                                result1.append({
                                                 'move_id': int.other_move_id.id,
                                                 'product_qty' : qty_internal,
                                                 'document_date': si.date_done,
                                                 })
#        if sm_id == 14385:
#            raise osv.except_osv(_('Debug !'), _(str(result1)))

        return result1

    def stock_move_get(self, cr, uid, product_id, location_id=False, context=None):
        stock_move_obj = self.pool.get('stock.move')
        result1 = []
        res_temp = []
        date_done = {}
        int_res = []
        int_res2 = []
        int_date_done = {}
        number = 0
        int_number = 0
        product_product_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        currency_obj = self.pool.get('res.currency')
        fifo_control_obj = self.pool.get('fifo.control')
        move_allocated_control_obj = self.pool.get('move.allocated.control')
        obj_currency_rate = self.pool.get('res.currency.rate')
        product = product_product_obj.browse(cr, uid, product_id, context=context)
        if location_id:
            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('location_dest_id','=',location_id),('state','=','done')])
        else:
            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('state','=','done')])

        if stock_move_ids:
#            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(product_id, stock_move_ids))
            for sm in stock_move_obj.browse(cr, uid, stock_move_ids, context=context):
#                if sm.id == 946:
#                    continue
#                    raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(sm.full_out, sm.id))
                #6023
                #print str(sm.id) + 'xxxx' + str(qty_move)
                if sm.full_out == 'Full Out':
                    continue
                if sm.location_dest_usage != 'internal':
                    continue
                qty_allocated = 0.00

                move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id)]), context=context)
                if move_allocated_control_ids:
                    for all_c in move_allocated_control_ids:
                        
#                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
                        qty_allocated += (all_c.quantity - all_c.rec_quantity)

                if sm.picking_id:
                    qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                   print str(sm.id) + '----' + str(qty_move)
                    fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
                    qty_out = 0.00
                    if fifo_control_ids:
                        for val in fifo_control_ids:
                            qty_out += val.quantity
                    #print str(qty_move) + 'xxxxx' + str(qty_out)
                    
                    qty_move = qty_move - qty_out
                    
                    unit_cost_price = 0.00

#if incoming
                    if sm.picking_id.type == "in":
                        ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id
########################
                        rate_id = False
                        p_curr_id = sm.picking_id.pricelist_id.currency_id.id
                        if p_curr_id != ptype_src:
                            tgl = sm.picking_id.do_date
                            tgl = datetime.strptime(tgl, '%Y-%m-%d').date()
                            rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', p_curr_id),
                                                                          ('name','<=', tgl)
                                                                          ])
                            if rate_ids:
                                rate_id = rate_ids[0]
                            else:
                                raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                            home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', ptype_src),
                                                                          ('name','<=', tgl)
                                                                          ])
                            if home_rate_ids:
                                home_rate_id = home_rate_ids[0]
                            else:
                                raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))

                        if rate_id:
                            unit_cost_price = sm.price_unit * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                            total_unit_cost_price = (qty_move * sm.price_unit) * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                        else:
                            unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, sm.price_unit, round=False)
                            total_unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, (qty_move * sm.price_unit), round=False)
                        unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, unit_cost_price, sm.product_uom.id)
                        unit_cost_price = product_product_obj.round_p(cr, uid, unit_cost_price, 'Purchase Price',)
                        total_unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, total_unit_cost_price, sm.product_uom.id)
                        total_unit_cost_price = product_product_obj.round_p(cr, uid, total_unit_cost_price, 'Purchase Price',)
                        number = number + 1
                        res_temp.append({
                                         'int_doc_no' : '',
                                         'int_move_id' : False,
                                         'doc_ucp': sm.price_unit,
                                         'doc_total_ucp': sm.price_unit * qty_move,
                                         'doc_curr_id' : p_curr_id,
                                         'home_curr_id' : ptype_src,
                                         'number': number,
                                         'document_date': sm.picking_id.do_date,
                                         'document_no' : sm.picking_id.name,
                                         'purchase_no' : (sm.purchase_line_id and sm.purchase_line_id.order_id and sm.purchase_line_id.order_id.name) or '',
                                         'move_id' : sm.id,
                                         'location_id' : sm.location_dest_id.id,
                                         'product_qty' : qty_move,
                                         'product_uom' : sm.product_id.uom_id.id,
                                         'unit_cost_price' : unit_cost_price,
                                         'total_cost_price' : total_unit_cost_price,
                                         'qty_allocated' : qty_allocated,
                                         'qty_onhand_free' : qty_move - qty_allocated,
                                         }
                                        )
                        date_done[number] = sm.picking_id.do_date
#if internal
                    if sm.picking_id.type == 'internal':
#                        if sm.picking_id.name == '1300517MTF':
#                            print 'xxxx'
                        ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id

                        real_qty = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                        print real_qty
                        
#                        sold_qty = 3000
#                        qty_sisa = 2000
                        internal_move_control_ids = self.internal_get(cr, uid, sm.id)
#                        if sm.picking_id.name == '1300517MTF':
#                            raise osv.except_osv(_('Debug !'), _(str(internal_move_control_ids)))


                        if internal_move_control_ids:
                            int_res = []
#                            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(internal_move_control_ids, 'xxxxx'))
                            #print str(sm.id) + 'xxxx' + str(real_qty) + 'yyyy' + str(internal_move_control_ids)
                            for int in internal_move_control_ids:
                                int_sm = stock_move_obj.browse(cr, uid, int['move_id'], context=context)
                                if int_sm.picking_id:
                                    int_number = int_number + 1
                                    int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_sm.picking_id.company_id.id, context=context).currency_id.id
################
                                    rate_id = False
                                    int_p_curr_id = int_sm.picking_id.pricelist_id.currency_id.id
                                    int_res.append({
                                                     'doc_no' : int_sm.picking_id.name,
                                                     'doc_curr_id' : int_p_curr_id,
                                                     'home_curr_id' : int_ptype_src,
                                                     'number': int_number,
                                                     'document_date': int_sm.picking_id.do_date,
                                                     'move_id' : int_sm.id,
                                                     'product_qty' : int['product_qty'],
                                                     'unit_cost_price' : int_sm.price_unit,
                                                     })
                                    int_date_done[int_number] = int_sm.picking_id.do_date
                                else:
                                    if int_sm.stock_inventory_ids:
                                        for int_si in int_sm.stock_inventory_ids:
                                            int_number = int_number + 1
                                            int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_si.company_id.id, context=context).currency_id.id
                                            int_res.append({
                                                             'doc_no' : int_si.name,
                                                             'doc_curr_id' : int_ptype_src,
                                                             'home_curr_id' : int_ptype_src,
                                                             'number': int_number,
                                                             'document_date': int_si.date_done,
                                                             'move_id' : int_sm.id,
                                                             'product_qty' : int['product_qty'],
                                                             'unit_cost_price' : int_sm.price_unit,
                                                             })
                                            int_date_done[int_number] = int_si.date_done
                            int_res2 = []
                            for key, value in sorted(int_date_done.iteritems(), key=lambda (k,v): (v,k)):
                                for int_temp in int_res:
                                    if int_temp['number'] == key:
                                        int_res2.append({
                                                        'doc_no' : int_temp['doc_no'],
                                                        'doc_curr_id' : int_temp['doc_curr_id'],
                                                        'home_curr_id' : int_temp['home_curr_id'],
                                                        'number': int_temp['number'],
                                                        'document_date' : int_temp['document_date'],
                                                        'move_id' : int_temp['move_id'],
                                                        'product_qty' : int_temp['product_qty'],
                                                        'unit_cost_price' : int_temp['unit_cost_price'],
                                                        })
                            

                            if int_res2:
#                                raise osv.except_osv(_('Debug !'), _(str(int_res2)))
#                                if sm.picking_id.name == '1300597MTF':
#                                    print 'yess'
#                                    print int_res2
                                for int_temp2 in int_res2:

                                    #raise osv.except_osv(_('Debug !'), _(str(int_temp2['move_id'])))


                                    int_qty_allocated = 0
                                    int_move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id), ('int_move_id','=',int_temp2['move_id'])]), context=context)
                                    if int_move_allocated_control_ids:
                                        for int_all_c in int_move_allocated_control_ids:
                    #                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
                                            int_qty_allocated += (int_all_c.quantity - int_all_c.rec_quantity)
                                    
                                    int_qty_out = 0.00
                                    int_fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id), ('int_in_move_id','=',int_temp2['move_id'])]), context=context)
                                    
                                    if int_fifo_control_ids:
                                        for int_val in int_fifo_control_ids:
                                            int_qty_out += int_val.quantity
#                                    if int_temp2['move_id'] == 944:
#                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_allocated) + 'xxx' + str(int_qty_out)))
                                    qty_internal = int_temp2['product_qty']
                                    #print str(sm.id) + 'wwww' + str(int_temp2['move_id']) + 'xxxx' + str(qty_internal) + 'yyyy' + str(int_qty_out)
                                    int_qty_sisa = qty_internal - int_qty_out
#                                    if int_temp2['move_id'] == 944:
#                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_sisa) + 'xxx'))

                                    if int_qty_sisa > 0:
                                        number = number + 1
                                        x_ptype_src = int_temp2['home_curr_id']
                ########################
                                        x_rate_id = False
                                        x_p_curr_id = int_temp2['doc_curr_id']
                                        if x_p_curr_id != x_ptype_src:
                                            x_tgl = int_temp2['document_date']
                                            x_tgl = datetime.strptime(x_tgl, '%Y-%m-%d %H:%M:%S').date()
                                            x_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_p_curr_id),
                                                                                          ('name','<=', x_tgl)
                                                                                          ])
                                            if x_rate_ids:
                                                x_rate_id = x_rate_ids[0]
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                            x_home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_ptype_src),
                                                                                          ('name','<=', x_tgl)
                                                                                          ])
                                            if x_home_rate_ids:
                                                x_home_rate_id = x_home_rate_ids[0]
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
                
                                        if x_rate_id:
                                            x_unit_cost_price = int_temp2['unit_cost_price'] * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                                            x_total_unit_cost_price = (int_qty_sisa * int_temp2['unit_cost_price']) * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                                        else:
                                            x_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, int_temp2['unit_cost_price'], round=False)
                                            x_total_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, (int_qty_sisa * int_temp2['unit_cost_price']), round=False)
                                        x_unit_cost_price = product_product_obj.round_p(cr, uid, x_unit_cost_price, 'Purchase Price',)
                                        x_total_unit_cost_price = product_product_obj.round_p(cr, uid, x_total_unit_cost_price, 'Purchase Price',)
                                        allo_input = 0
#                                        print str(sm.id) + 'xxxxx' + str(qty_internal) + 'yyyyy' + str(int_qty_out) + 'zzzz' + str(int_qty_allocated)
                                    
                                        if int_qty_allocated > 0:
                                            if int_qty_sisa > int_qty_allocated:
                                                allo_input = int_qty_allocated
                                                int_qty_allocated = 0
                                            else:
                                                allo_input = int_qty_sisa
                                                int_qty_allocated = int_qty_allocated - int_qty_sisa
                                        res_temp.append({
                                                         'int_doc_no' : int_temp2['doc_no'],
                                                        'int_move_id' : int_temp2['move_id'],
                                                        'doc_ucp': int_temp2['unit_cost_price'],
                                                        'doc_total_ucp': int_temp2['unit_cost_price'] * int_qty_sisa,
                                                        'doc_curr_id' : int_temp2['doc_curr_id'],
                                                        'home_curr_id' : int_temp2['home_curr_id'],
                                                        'number': number,
                                                        'document_date': sm.picking_id.date_done,
                                                        'document_no' : sm.picking_id.name,
                                                        'purchase_no' : '',
                                                        'move_id' : sm.id,
                                                        'location_id' : sm.location_dest_id.id,
                                                        'product_qty' : int_qty_sisa,
                                                        'product_uom' : sm.product_id.uom_id.id,
                                                        'unit_cost_price' : x_unit_cost_price,
                                                        'total_cost_price' : x_total_unit_cost_price,
                                                        'qty_allocated' : allo_input,
                                                        'qty_onhand_free' : int_qty_sisa - allo_input,
                                                        })
                                        date_done[number] = sm.picking_id.date_done
                else:
                    
                    if sm.stock_inventory_ids:
                        for si in sm.stock_inventory_ids:
                            number = number + 1
                            qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                            
                            fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=None)
                            #print 'pi'
                            #print qty_move
                            #print sm.id
                            qty_out = 0.00
                            #print fifo_control_ids
                            if fifo_control_ids:
                                for val in fifo_control_ids:
                                    #print val.quantity
                                    qty_out += val.quantity
#                            print str(sm.id) + '----' + str(qty_move) + --- + str(qty_out)
                            qty_move = qty_move - qty_out


                            #print qty_out
                            unit_cost_price = sm.price_unit
                            ptype_src = self.pool.get('res.company').browse(cr, uid, si.company_id.id, context=context).currency_id.id
                            res_temp.append({
                                             'int_doc_no' : '',
                                             'int_move_id' : False,
                                             'doc_ucp': unit_cost_price,
                                             'doc_total_ucp': unit_cost_price * qty_move,
                                             'doc_curr_id' : ptype_src,
                                             'home_curr_id' : ptype_src,
                                             'number': number,
                                             'document_date': si.date_done,
                                             'document_no' : si.name,
                                             'purchase_no' : '',
                                             'move_id' : sm.id,
                                             'location_id' : sm.location_dest_id.id,
                                             'product_qty' : qty_move,
                                             'product_uom' : sm.product_id.uom_id.id,
                                             'unit_cost_price' : unit_cost_price,
                                             'total_cost_price' : unit_cost_price * qty_move,
                                             'qty_allocated' : qty_allocated,
                                             'qty_onhand_free' : qty_move - qty_allocated,
                                             }
                                            )
                            date_done[number] = si.date_done

#        raise osv.except_osv(_('Warning !'), _(str(res_temp)))

        for key, value in sorted(date_done.iteritems(), key=lambda (k,v): (v,k)):
            for temp in res_temp:
                if temp['number'] == key:
                    result1.append({
                                    'int_move_id' : temp['int_move_id'],
                                    'int_doc_no' : temp['int_doc_no'],
                                    'doc_ucp' : temp['doc_ucp'],
                                    'doc_total_ucp': temp['doc_total_ucp'],
                                    'doc_curr_id' : temp['doc_curr_id'],
                                    'home_curr_id': temp['home_curr_id'],
                                    'document_date': temp['document_date'],
                                    'document_no' : temp['document_no'],
                                    'purchase_no' : temp['purchase_no'],
                                    'move_id' : temp['move_id'],
                                    'location_id' : temp['location_id'],
                                    'product_qty' : temp['product_qty'],
                                    'product_uom' : temp['product_uom'],
                                    'unit_cost_price' : temp['unit_cost_price'],
                                    'total_cost_price' : temp['total_cost_price'],
                                    'qty_allocated' : temp['qty_allocated'],
                                    'qty_onhand_free' : temp['qty_onhand_free'],
                                    })

#        print result1
        return result1


    def stock_move_get_with_date(self, cr, uid, product_id, location_id=False, date_searc=False, context=None):
        stock_move_obj = self.pool.get('stock.move')
        result1 = []
        res_temp = []
        date_done = {}
        int_res = []
        int_res2 = []
        int_date_done = {}
        number = 0
        int_number = 0
        product_product_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        currency_obj = self.pool.get('res.currency')
        fifo_control_obj = self.pool.get('fifo.control')
        move_allocated_control_obj = self.pool.get('move.allocated.control')
        obj_currency_rate = self.pool.get('res.currency.rate')
        product = product_product_obj.browse(cr, uid, product_id, context=context)
        if location_id:
            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('location_dest_id','=',location_id),('state','=','done')])
        else:
            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('state','=','done')])

        if stock_move_ids:
            for sm in stock_move_obj.browse(cr, uid, stock_move_ids, context=context):
                if sm.location_dest_usage != 'internal':
                    continue
               
                dat_done = False
                if sm.picking_id:
                    dat_done = sm.picking_id.do_date or sm.picking_id.date_done
                else:
                    for si in sm.stock_inventory_ids:
                        dat_done = si.date_done or False

                if dat_done and date_searc:
                    if dat_done >= date_searc:
                        continue


                qty_allocated = 0.00
                move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id)]), context=context)
                if move_allocated_control_ids:
                    for all_c in move_allocated_control_ids:
                        
#                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
                        qty_allocated += (all_c.quantity - all_c.rec_quantity)

                if sm.picking_id:
                    qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                   print str(sm.id) + '----' + str(qty_move)
                    fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
                    qty_out = 0.00
                    if fifo_control_ids:
                        for val in fifo_control_ids:

                            sm2 = val.out_move_id and stock_move_obj.browse(cr, uid, val.out_move_id, context=context) or False
                            dat_done2 = False
                            if sm2:
                                if sm2.picking_id:
                                    dat_done2 = sm2.picking_id.do_date or sm2.picking_id.date_done
                                else:
                                    for si2 in sm2.stock_inventory_ids:
                                        dat_done2 =  si2.date_done or False
                                if dat_done2 and date_searc:
                                    if dat_done2 < date_searc:
                                        qty_out = qty_out + val.quantity
    
    
#                            qty_out += val.quantity
                    #print str(qty_move) + 'xxxxx' + str(qty_out)
                    
                    qty_move = qty_move - qty_out
                    
                    unit_cost_price = 0.00

#if incoming
                    if sm.picking_id.type == "in":
                        ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id
########################
                        rate_id = False
                        p_curr_id = sm.picking_id.pricelist_id.currency_id.id
                        if p_curr_id != ptype_src:
                            tgl = sm.picking_id.do_date
                            tgl = datetime.strptime(tgl, '%Y-%m-%d').date()
                            rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', p_curr_id),
                                                                          ('name','<=', tgl)
                                                                          ])
                            if rate_ids:
                                rate_id = rate_ids[0]
                            else:
                                raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                            home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', ptype_src),
                                                                          ('name','<=', tgl)
                                                                          ])
                            if home_rate_ids:
                                home_rate_id = home_rate_ids[0]
                            else:
                                raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))

                        if rate_id:
                            unit_cost_price = sm.price_unit * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                            total_unit_cost_price = (qty_move * sm.price_unit) * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                        else:
                            unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, sm.price_unit, round=False)
                            total_unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, (qty_move * sm.price_unit), round=False)
                        unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, unit_cost_price, sm.product_uom.id)
                        unit_cost_price = product_product_obj.round_p(cr, uid, unit_cost_price, 'Purchase Price',)
                        total_unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, total_unit_cost_price, sm.product_uom.id)
                        total_unit_cost_price = product_product_obj.round_p(cr, uid, total_unit_cost_price, 'Purchase Price',)
                        number = number + 1
#                        print str(sm.id) + 'xxxxx' + str(qty_move)
                        res_temp.append({
                                         'int_doc_no' : '',
                                         'int_move_id' : False,
                                         'doc_ucp': sm.price_unit,
                                         'doc_total_ucp': sm.price_unit * qty_move,
                                         'doc_curr_id' : p_curr_id,
                                         'home_curr_id' : ptype_src,
                                         'number': number,
                                         'document_date': sm.picking_id.do_date,
                                         'document_no' : sm.picking_id.name,
                                         'move_id' : sm.id,
                                         'location_id' : sm.location_dest_id.id,
                                         'product_qty' : qty_move,
                                         'product_uom' : sm.product_id.uom_id.id,
                                         'unit_cost_price' : unit_cost_price,
                                         'total_cost_price' : total_unit_cost_price,
                                         'qty_allocated' : qty_allocated,
                                         'qty_onhand_free' : qty_move - qty_allocated,
                                         }
                                        )
                        date_done[number] = sm.picking_id.do_date
#if internal
                    if sm.picking_id.type == 'internal':
#                        if sm.picking_id.name == '1300517MTF':
#                            print 'xxxx'
                        ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id

                        real_qty = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                        print real_qty
                        
#                        sold_qty = 3000
#                        qty_sisa = 2000
                        internal_move_control_ids = self.internal_get(cr, uid, sm.id)
#                        if sm.picking_id.name == '1300517MTF':
#                            raise osv.except_osv(_('Debug !'), _(str(internal_move_control_ids)))


                        if internal_move_control_ids:
                            int_res = []
#                            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(internal_move_control_ids, 'xxxxx'))
                            #print str(sm.id) + 'xxxx' + str(real_qty) + 'yyyy' + str(internal_move_control_ids)
                            for int in internal_move_control_ids:
                                int_sm = stock_move_obj.browse(cr, uid, int['move_id'], context=context)
                                if int_sm.picking_id:
                                    int_number = int_number + 1
                                    int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_sm.picking_id.company_id.id, context=context).currency_id.id
################
                                    rate_id = False
                                    int_p_curr_id = int_sm.picking_id.pricelist_id.currency_id.id
                                    int_res.append({
                                                     'doc_no' : int_sm.picking_id.name,
                                                     'doc_curr_id' : int_p_curr_id,
                                                     'home_curr_id' : int_ptype_src,
                                                     'number': int_number,
                                                     'document_date': int_sm.picking_id.do_date,
                                                     'move_id' : int_sm.id,
                                                     'product_qty' : int['product_qty'],
                                                     'unit_cost_price' : int_sm.price_unit,
                                                     })
                                    int_date_done[int_number] = int_sm.picking_id.do_date
                                else:
                                    if int_sm.stock_inventory_ids:
                                        for int_si in int_sm.stock_inventory_ids:
                                            int_number = int_number + 1
                                            int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_si.company_id.id, context=context).currency_id.id
                                            int_res.append({
                                                             'doc_no' : int_si.name,
                                                             'doc_curr_id' : int_ptype_src,
                                                             'home_curr_id' : int_ptype_src,
                                                             'number': int_number,
                                                             'document_date': int_si.date_done,
                                                             'move_id' : int_sm.id,
                                                             'product_qty' : int['product_qty'],
                                                             'unit_cost_price' : int_sm.price_unit,
                                                             })
                                            int_date_done[int_number] = int_si.date_done
                            int_res2 = []
                            for key, value in sorted(int_date_done.iteritems(), key=lambda (k,v): (v,k)):
                                for int_temp in int_res:
                                    if int_temp['number'] == key:
                                        int_res2.append({
                                                        'doc_no' : int_temp['doc_no'],
                                                        'doc_curr_id' : int_temp['doc_curr_id'],
                                                        'home_curr_id' : int_temp['home_curr_id'],
                                                        'number': int_temp['number'],
                                                        'document_date' : int_temp['document_date'],
                                                        'move_id' : int_temp['move_id'],
                                                        'product_qty' : int_temp['product_qty'],
                                                        'unit_cost_price' : int_temp['unit_cost_price'],
                                                        })
                            

                            if int_res2:
#                                raise osv.except_osv(_('Debug !'), _(str(int_res2)))
#                                if sm.picking_id.name == '1300597MTF':
#                                    print 'yess'
#                                    print int_res2
                                for int_temp2 in int_res2:

                                    #raise osv.except_osv(_('Debug !'), _(str(int_temp2['move_id'])))


                                    int_qty_allocated = 0
                                    int_move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id), ('int_move_id','=',int_temp2['move_id'])]), context=context)
                                    if int_move_allocated_control_ids:
                                        for int_all_c in int_move_allocated_control_ids:
                    #                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
                                            int_qty_allocated += (int_all_c.quantity - int_all_c.rec_quantity)
                                    
                                    int_qty_out = 0.00
                                    int_fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id), ('int_in_move_id','=',int_temp2['move_id'])]), context=context)
                                    
                                    if int_fifo_control_ids:
                                        for int_val in int_fifo_control_ids:
                                            int_qty_out += int_val.quantity
#                                    if int_temp2['move_id'] == 944:
#                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_allocated) + 'xxx' + str(int_qty_out)))
                                    qty_internal = int_temp2['product_qty']
                                    #print str(sm.id) + 'wwww' + str(int_temp2['move_id']) + 'xxxx' + str(qty_internal) + 'yyyy' + str(int_qty_out)
                                    int_qty_sisa = qty_internal - int_qty_out
#                                    if int_temp2['move_id'] == 944:
#                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_sisa) + 'xxx'))

                                    if int_qty_sisa > 0:
                                        number = number + 1
                                        x_ptype_src = int_temp2['home_curr_id']
                ########################
                                        x_rate_id = False
                                        x_p_curr_id = int_temp2['doc_curr_id']
                                        if x_p_curr_id != x_ptype_src:
                                            x_tgl = int_temp2['document_date']
                                            x_tgl = datetime.strptime(x_tgl, '%Y-%m-%d %H:%M:%S').date()
                                            x_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_p_curr_id),
                                                                                          ('name','<=', x_tgl)
                                                                                          ])
                                            if x_rate_ids:
                                                x_rate_id = x_rate_ids[0]
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                            x_home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_ptype_src),
                                                                                          ('name','<=', x_tgl)
                                                                                          ])
                                            if x_home_rate_ids:
                                                x_home_rate_id = x_home_rate_ids[0]
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
                
                                        if x_rate_id:
                                            x_unit_cost_price = int_temp2['unit_cost_price'] * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                                            x_total_unit_cost_price = (int_qty_sisa * int_temp2['unit_cost_price']) * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                                        else:
                                            x_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, int_temp2['unit_cost_price'], round=False)
                                            x_total_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, (int_qty_sisa * int_temp2['unit_cost_price']), round=False)
                                        x_unit_cost_price = product_product_obj.round_p(cr, uid, x_unit_cost_price, 'Purchase Price',)
                                        x_total_unit_cost_price = product_product_obj.round_p(cr, uid, x_total_unit_cost_price, 'Purchase Price',)
                                        allo_input = 0
#                                        print str(sm.id) + 'xxxxx' + str(qty_internal) + 'yyyyy' + str(int_qty_out) + 'zzzz' + str(int_qty_allocated)
                                    
                                        if int_qty_allocated > 0:
                                            if int_qty_sisa > int_qty_allocated:
                                                allo_input = int_qty_allocated
                                                int_qty_allocated = 0
                                            else:
                                                allo_input = int_qty_sisa
                                                int_qty_allocated = int_qty_allocated - int_qty_sisa
                                        res_temp.append({
                                                         'int_doc_no' : int_temp2['doc_no'],
                                                        'int_move_id' : int_temp2['move_id'],
                                                        'doc_ucp': int_temp2['unit_cost_price'],
                                                        'doc_total_ucp': int_temp2['unit_cost_price'] * int_qty_sisa,
                                                        'doc_curr_id' : int_temp2['doc_curr_id'],
                                                        'home_curr_id' : int_temp2['home_curr_id'],
                                                        'number': number,
                                                        'document_date': sm.picking_id.date_done,
                                                        'document_no' : sm.picking_id.name,
                                                        'move_id' : sm.id,
                                                        'location_id' : sm.location_dest_id.id,
                                                        'product_qty' : int_qty_sisa,
                                                        'product_uom' : sm.product_id.uom_id.id,
                                                        'unit_cost_price' : x_unit_cost_price,
                                                        'total_cost_price' : x_total_unit_cost_price,
                                                        'qty_allocated' : allo_input,
                                                        'qty_onhand_free' : int_qty_sisa - allo_input,
                                                        })
                                        date_done[number] = sm.picking_id.date_done
                else:
                    
                    if sm.stock_inventory_ids:
                        for si in sm.stock_inventory_ids:
                            number = number + 1
                            qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                            
                            fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=None)
                            #print 'pi'
                            #print qty_move
                            #print sm.id
                            qty_out = 0.00
                            #print fifo_control_ids
                            if fifo_control_ids:
                                for val in fifo_control_ids:
                                    sm2 = val.out_move_id and stock_move_obj.browse(cr, uid, val.out_move_id, context=context) or False
                                    dat_done2 = False
                                    if sm2:
                                        if sm2.picking_id:
                                            dat_done2 = sm2.picking_id.do_date or sm2.picking_id.date_done
                                        else:
                                            for si2 in sm2.stock_inventory_ids:
                                                dat_done2 =  si2.date_done or False
                                        if dat_done2 and date_searc:
                                            if dat_done2 < date_searc:
                                                qty_out = qty_out + val.quantity
#                                for val in fifo_control_ids:
#                                    #print val.quantity
#                                    qty_out += val.quantity
#                            print str(sm.id) + '----' + str(qty_move) + --- + str(qty_out)
                            qty_move = qty_move - qty_out

                            unit_cost_price = sm.price_unit
                            ptype_src = self.pool.get('res.company').browse(cr, uid, si.company_id.id, context=context).currency_id.id
                            res_temp.append({
                                             'int_doc_no' : '',
                                             'int_move_id' : False,
                                             'doc_ucp': unit_cost_price,
                                             'doc_total_ucp': unit_cost_price * qty_move,
                                             'doc_curr_id' : ptype_src,
                                             'home_curr_id' : ptype_src,
                                             'number': number,
                                             'document_date': si.date_done,
                                             'document_no' : si.name,
                                             'move_id' : sm.id,
                                             'location_id' : sm.location_dest_id.id,
                                             'product_qty' : qty_move,
                                             'product_uom' : sm.product_id.uom_id.id,
                                             'unit_cost_price' : unit_cost_price,
                                             'total_cost_price' : unit_cost_price * qty_move,
                                             'qty_allocated' : qty_allocated,
                                             'qty_onhand_free' : qty_move - qty_allocated,
                                             }
                                            )
                            date_done[number] = si.date_done

#        raise osv.except_osv(_('Warning !'), _(str(res_temp)))

        for key, value in sorted(date_done.iteritems(), key=lambda (k,v): (v,k)):
            for temp in res_temp:
                if temp['number'] == key:
                    result1.append({
                                    'int_move_id' : temp['int_move_id'],
                                    'int_doc_no' : temp['int_doc_no'],
                                    'doc_ucp' : temp['doc_ucp'],
                                    'doc_total_ucp': temp['doc_total_ucp'],
                                    'doc_curr_id' : temp['doc_curr_id'],
                                    'home_curr_id': temp['home_curr_id'],
                                    'document_date': temp['document_date'],
                                    'document_no' : temp['document_no'],
                                    'move_id' : temp['move_id'],
                                    'location_id' : temp['location_id'],
                                    'product_qty' : temp['product_qty'],
                                    'product_uom' : temp['product_uom'],
                                    'unit_cost_price' : temp['unit_cost_price'],
                                    'total_cost_price' : temp['total_cost_price'],
                                    'qty_allocated' : temp['qty_allocated'],
                                    'qty_onhand_free' : temp['qty_onhand_free'],
                                    })
        return result1


#    def stock_move_get_with_date(self, cr, uid, product_id, location_id=False, date_searc=False, context=None):
#        stock_move_obj = self.pool.get('stock.move')
#        result1 = []
#        res_temp = []
#        date_done = {}
#        int_res = []
#        int_res2 = []
#        int_date_done = {}
#        number = 0
#        int_number = 0
#        product_product_obj = self.pool.get('product.product')
#        uom_obj = self.pool.get('product.uom')
#        currency_obj = self.pool.get('res.currency')
#        fifo_control_obj = self.pool.get('fifo.control')
#        move_allocated_control_obj = self.pool.get('move.allocated.control')
#        obj_currency_rate = self.pool.get('res.currency.rate')
#        product = product_product_obj.browse(cr, uid, product_id, context=context)
#        if location_id:
#            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('location_dest_id','=',location_id),('state','=','done')])
#        else:
#            stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product_id),('state','=','done')])
#
#        if stock_move_ids:
##            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(product_id, stock_move_ids))
#            for sm in stock_move_obj.browse(cr, uid, stock_move_ids, context=context):
##                if sm.id == 946:
##                    continue
##                    raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(sm.full_out, sm.id))
##                if sm.full_out == 'Full Out':
##                    continue
#                if sm.location_dest_usage != 'internal':
#                    continue
#                dat_done = False
#                if sm.picking_id:
#                    dat_done = sm.picking_id.do_date
#                else:
#                    for si in sm.stock_inventory_ids:
#                        dat_done =  si.date_done or False
##                raise osv.except_osv(_('Invalid action stock fifo !'), _(' \'%s\' \'%s\'!') %(dat_done, date_searc))
##
#                if dat_done and date_searc:
#                    if dat_done >= date_searc:
#                        continue
##                    raise osv.except_osv(_('Invalid action stock fifo xx !'), _(' \'%s\' \'%s\'!') %(dat_done, date_searc))
#
##                fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
##                if fifo_control_ids:
##                    qty_in = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
##                    qty_out = 0.00
##                    for val in fifo_control_ids:
##                        sm2 = val.out_move_id and stock_move_obj.browse(cr, uid, val.out_move_id, context=context) or False
##                        dat_done2 = False
##                        if sm2:
##                            if sm2.picking_id:
##                                dat_done2 = sm2.picking_id.do_date
##                            else:
##                                for si2 in sm2.stock_inventory_ids:
##                                    dat_done2 =  si2.date_done or False
##                            if dat_done2 and date_searc:
##                                if dat_done2 < date_searc:
##                                    qty_out = qty_out + val.quantity
###                    raise osv.except_osv(_('Invalid action stock fifo !'), _(' \'%s\' \'%s\'!') %(qty_out, qty_in))
##
##                    if qty_out == qty_in:
##                        continue
#
#
#                    qty_allocated = 0.00
#    
#                    move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id)]), context=context)
#                    if move_allocated_control_ids:
#                        for all_c in move_allocated_control_ids:
#                            
#    #                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
#                            qty_allocated = qty_allocated + (all_c.quantity - all_c.rec_quantity)
#    
#                    if sm.picking_id:
#                        qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                        fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
#                        qty_out = 0.00
#                        if fifo_control_ids:
#                            for val in fifo_control_ids:
#                                sm2 = val.out_move_id and stock_move_obj.browse(cr, uid, val.out_move_id, context=context) or False
#                                dat_done2 = False
#                                if sm2:
#                                    if sm2.picking_id:
#                                        dat_done2 = sm2.picking_id.do_date
#                                    else:
#                                        for si2 in sm2.stock_inventory_ids:
#                                            dat_done2 =  si2.date_done or False
#                                    if dat_done2 and date_searc:
#                                        if dat_done2 < date_searc:
#                                            qty_out = qty_out + val.quantity
#    
#    
#    #                            qty_out = qty_out + val.quantity
#    #                    raise osv.except_osv(_('Invalid action stock fifo !'), _(' \'%s\' \'%s\'!') %(qty_out, qty_move))
#    #
#                        qty_move = qty_move - qty_out
#                        unit_cost_price = 0.00
#    
#    #if incoming
#                        if sm.picking_id.type == "in":
#                            ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id
#    ########################
#                            rate_id = False
#                            p_curr_id = sm.picking_id.pricelist_id.currency_id.id
#                            if p_curr_id != ptype_src:
#                                tgl = sm.picking_id.do_date
#                                tgl = datetime.strptime(tgl, '%Y-%m-%d').date()
#                                rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', p_curr_id),
#                                                                              ('name','<=', tgl)
#                                                                              ])
#                                if rate_ids:
#                                    rate_id = rate_ids[0]
#                                else:
#                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
#                                home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', ptype_src),
#                                                                              ('name','<=', tgl)
#                                                                              ])
#                                if home_rate_ids:
#                                    home_rate_id = home_rate_ids[0]
#                                else:
#                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
#    
#                            if rate_id:
#                                unit_cost_price = sm.price_unit * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
#                                total_unit_cost_price = (qty_move * sm.price_unit) * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
#                            else:
#                                unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, sm.price_unit, round=False)
#                                total_unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, (qty_move * sm.price_unit), round=False)
#                            unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, unit_cost_price, sm.product_uom.id)
#                            unit_cost_price = product_product_obj.round_p(cr, uid, unit_cost_price, 'Purchase Price',)
#                            total_unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, total_unit_cost_price, sm.product_uom.id)
#                            total_unit_cost_price = product_product_obj.round_p(cr, uid, total_unit_cost_price, 'Purchase Price',)
#                            number = number + 1
#                            res_temp.append({
#                                             'int_doc_no' : '',
#                                             'int_move_id' : False,
#                                             'doc_ucp': sm.price_unit,
#                                             'doc_total_ucp': sm.price_unit * qty_move,
#                                             'doc_curr_id' : p_curr_id,
#                                             'home_curr_id' : ptype_src,
#                                             'number': number,
#                                             'document_date': sm.picking_id.do_date,
#                                             'document_no' : sm.picking_id.name,
#                                             'move_id' : sm.id,
#                                             'location_id' : sm.location_dest_id.id,
#                                             'product_qty' : qty_move,
#                                             'product_uom' : sm.product_id.uom_id.id,
#                                             'unit_cost_price' : unit_cost_price,
#                                             'total_cost_price' : total_unit_cost_price,
#                                             'qty_allocated' : qty_allocated,
#                                             'qty_onhand_free' : qty_move - qty_allocated,
#                                             }
#                                            )
#                            date_done[number] = sm.picking_id.do_date
#                            
#                        if sm.picking_id.type == 'internal':
#    
#                            ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=context).currency_id.id
#    
#                            real_qty = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                            
#    
#    
#    #                        sold_qty = 3000
#    #                        qty_sisa = 2000
#                            internal_move_control_ids = self.internal_get(cr, uid, sm.id,)
#    #                        raise osv.except_osv(_('Debug !'), _(str(internal_move_control_ids)))
#                            if internal_move_control_ids:
#                                int_res = []
#    #                            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(internal_move_control_ids, 'xxxxx'))
#    
#                                for int in internal_move_control_ids:
#                                    int_sm = stock_move_obj.browse(cr, uid, int['move_id'], context=context)
#                                    if int_sm.picking_id:
#                                        int_number = int_number + 1
#                                        int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_sm.picking_id.company_id.id, context=context).currency_id.id
#    ################
#                                        rate_id = False
#                                        int_p_curr_id = int_sm.picking_id.pricelist_id.currency_id.id
#                                        int_res.append({
#                                                         'doc_no' : int_sm.picking_id.name,
#                                                         'doc_curr_id' : int_p_curr_id,
#                                                         'home_curr_id' : int_ptype_src,
#                                                         'number': int_number,
#                                                         'document_date': int_sm.picking_id.do_date,
#                                                         'move_id' : int_sm.id,
#                                                         'product_qty' : int['product_qty'],
#                                                         'unit_cost_price' : int_sm.price_unit,
#                                                         })
#                                        int_date_done[int_number] = int_sm.picking_id.do_date
#                                    else:
#                                        if int_sm.stock_inventory_ids:
#                                            for int_si in int_sm.stock_inventory_ids:
#                                                int_number = int_number + 1
#                                                int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_si.company_id.id, context=context).currency_id.id
#                                                int_res.append({
#                                                                 'doc_no' : int_si.name,
#                                                                 'doc_curr_id' : int_ptype_src,
#                                                                 'home_curr_id' : int_ptype_src,
#                                                                 'number': int_number,
#                                                                 'document_date': int_si.date_done,
#                                                                 'move_id' : int_sm.id,
#                                                                 'product_qty' : int['product_qty'],
#                                                                 'unit_cost_price' : int_sm.price_unit,
#                                                                 })
#                                                int_date_done[int_number] = int_si.date_done
#                                int_res2 = []
#                                for key, value in sorted(int_date_done.iteritems(), key=lambda (k,v): (v,k)):
#                                    for int_temp in int_res:
#                                        if int_temp['number'] == key:
#                                            int_res2.append({
#                                                            'doc_no' : int_temp['doc_no'],
#                                                            'doc_curr_id' : int_temp['doc_curr_id'],
#                                                            'home_curr_id' : int_temp['home_curr_id'],
#                                                            'number': int_temp['number'],
#                                                            'document_date' : int_temp['document_date'],
#                                                            'move_id' : int_temp['move_id'],
#                                                            'product_qty' : int_temp['product_qty'],
#                                                            'unit_cost_price' : int_temp['unit_cost_price'],
#                                                            })
#                                if int_res2:
#    #                                raise osv.except_osv(_('Debug !'), _(str(int_res2)))
#    
#                                    for int_temp2 in int_res2:
#                                        #raise osv.except_osv(_('Debug !'), _(str(int_temp2['move_id'])))
#    
#    
#                                        int_qty_allocated = 0
#                                        int_move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',sm.id), ('int_move_id','=',int_temp2['move_id'])]), context=context)
#                                        if int_move_allocated_control_ids:
#                                            for int_all_c in int_move_allocated_control_ids:
#                                                
#                        #                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
#                                                int_qty_allocated = int_qty_allocated + (int_all_c.quantity - int_all_c.rec_quantity)
#    
#                                        int_qty_out = 0.00
#                                        int_fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id), ('int_in_move_id','=',int_temp2['move_id'])]), context=context)
#                                        
#                                        if int_fifo_control_ids:
#                                            for int_val in int_fifo_control_ids:
#                                                int_qty_out = int_qty_out + int_val.quantity
#    #                                    if int_temp2['move_id'] == 944:
#    #                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_allocated) + 'xxx' + str(int_qty_out)))
#    
#                                        qty_internal = int_temp2['product_qty']
#                                        int_qty_sisa = qty_internal - int_qty_out
#    #                                    if int_temp2['move_id'] == 944:
#    #                                        raise osv.except_osv(_('Debug !'), _(str(int_qty_sisa) + 'xxx'))
#    
#                                        if int_qty_sisa > 0:
#                                            number = number + 1
#                                            x_ptype_src = int_temp2['home_curr_id']
#                    ########################
#                                            x_rate_id = False
#                                            x_p_curr_id = int_temp2['doc_curr_id']
#                                            if x_p_curr_id != x_ptype_src:
#                                                x_tgl = int_temp2['document_date']
#                                                x_tgl = datetime.strptime(x_tgl, '%Y-%m-%d %H:%M:%S').date()
#                                                x_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_p_curr_id),
#                                                                                              ('name','<=', x_tgl)
#                                                                                              ])
#                                                if x_rate_ids:
#                                                    x_rate_id = x_rate_ids[0]
#                                                else:
#                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
#                                                x_home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_ptype_src),
#                                                                                              ('name','<=', x_tgl)
#                                                                                              ])
#                                                if x_home_rate_ids:
#                                                    x_home_rate_id = x_home_rate_ids[0]
#                                                else:
#                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
#                    
#                                            if x_rate_id:
#                                                x_unit_cost_price = int_temp2['unit_cost_price'] * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
#                                                x_total_unit_cost_price = (int_qty_sisa * int_temp2['unit_cost_price']) * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
#                                            else:
#                                                x_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, int_temp2['unit_cost_price'], round=False)
#                                                x_total_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, (int_qty_sisa * int_temp2['unit_cost_price']), round=False)
#                                            x_unit_cost_price = product_product_obj.round_p(cr, uid, x_unit_cost_price, 'Purchase Price',)
#                                            x_total_unit_cost_price = product_product_obj.round_p(cr, uid, x_total_unit_cost_price, 'Purchase Price',)
#                                            allo_input = 0
#                                            if int_qty_allocated > 0:
#                                                if int_qty_sisa > int_qty_allocated:
#                                                    allo_input = int_qty_allocated
#                                                    int_qty_allocated = 0
#                                                else:
#                                                    allo_input = int_qty_sisa
#                                                    int_qty_allocated = int_qty_allocated - int_qty_sisa
#                                            res_temp.append({
#                                                             'int_doc_no' : int_temp2['doc_no'],
#                                                            'int_move_id' : int_temp2['move_id'],
#                                                            'doc_ucp': int_temp2['unit_cost_price'],
#                                                            'doc_total_ucp': int_temp2['unit_cost_price'] * int_qty_sisa,
#                                                            'doc_curr_id' : int_temp2['doc_curr_id'],
#                                                            'home_curr_id' : int_temp2['home_curr_id'],
#                                                            'number': number,
#                                                            'document_date': sm.picking_id.do_date,
#                                                            'document_no' : sm.picking_id.name,
#                                                            'move_id' : sm.id,
#                                                            'location_id' : sm.location_dest_id.id,
#                                                            'product_qty' : int_qty_sisa,
#                                                            'product_uom' : sm.product_id.uom_id.id,
#                                                            'unit_cost_price' : x_unit_cost_price,
#                                                            'total_cost_price' : x_total_unit_cost_price,
#                                                            'qty_allocated' : allo_input,
#                                                            'qty_onhand_free' : int_qty_sisa - allo_input,
#                                                            })
#                                            date_done[number] = sm.picking_id.do_date
#                    else:
#                        if sm.stock_inventory_ids:
#                            for si in sm.stock_inventory_ids:
#                                number = number + 1
#                                qty_move = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                                fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id)]), context=context)
#                                qty_out = 0.00
#                                if fifo_control_ids:
#                                    for val in fifo_control_ids:
#                                        sm2 = val.out_move_id and stock_move_obj.browse(cr, uid, val.out_move_id, context=context) or False
#                                        dat_done2 = False
#                                        if sm2:
#                                            if sm2.picking_id:
#                                                dat_done2 = sm2.picking_id.do_date
#                                            else:
#                                                for si2 in sm2.stock_inventory_ids:
#                                                    dat_done2 =  si2.date_done or False
#                                            if dat_done2 and date_searc:
#                                                if dat_done2 < date_searc:
#                                                    qty_out = qty_out + val.quantity
#    
#    #                                for val in fifo_control_ids:
#    #                                    qty_out = val.quantity
#    #                            raise osv.except_osv(_('Invalid action stock fifo !'), _(' \'%s\' \'%s\'!') %(qty_out, qty_move))
#    #
#                                qty_move = qty_move - qty_out
#                                unit_cost_price = sm.price_unit
#                                ptype_src = self.pool.get('res.company').browse(cr, uid, si.company_id.id, context=context).currency_id.id
#                                res_temp.append({
#                                                 'int_doc_no' : '',
#                                                 'int_move_id' : False,
#                                                 'doc_ucp': unit_cost_price,
#                                                 'doc_total_ucp': unit_cost_price * qty_move,
#                                                 'doc_curr_id' : ptype_src,
#                                                 'home_curr_id' : ptype_src,
#                                                 'number': number,
#                                                 'document_date': si.date_done,
#                                                 'document_no' : si.name,
#                                                 'move_id' : sm.id,
#                                                 'location_id' : sm.location_dest_id.id,
#                                                 'product_qty' : qty_move,
#                                                 'product_uom' : sm.product_id.uom_id.id,
#                                                 'unit_cost_price' : unit_cost_price,
#                                                 'total_cost_price' : unit_cost_price * qty_move,
#                                                 'qty_allocated' : qty_allocated,
#                                                 'qty_onhand_free' : qty_move - qty_allocated,
#                                                 }
#                                                )
#                                date_done[number] = si.date_done
#
##        raise osv.except_osv(_('Warning !'), _(str(res_temp)))
#
#        for key, value in sorted(date_done.iteritems(), key=lambda (k,v): (v,k)):
#            for temp in res_temp:
#                if temp['number'] == key:
#                    result1.append({
#                                    'int_move_id' : temp['int_move_id'],
#                                    'int_doc_no' : temp['int_doc_no'],
#                                    'doc_ucp' : temp['doc_ucp'],
#                                    'doc_total_ucp': temp['doc_total_ucp'],
#                                    'doc_curr_id' : temp['doc_curr_id'],
#                                    'home_curr_id': temp['home_curr_id'],
#                                    'document_date': temp['document_date'],
#                                    'document_no' : temp['document_no'],
#                                    'move_id' : temp['move_id'],
#                                    'location_id' : temp['location_id'],
#                                    'product_qty' : temp['product_qty'],
#                                    'product_uom' : temp['product_uom'],
#                                    'unit_cost_price' : temp['unit_cost_price'],
#                                    'total_cost_price' : temp['total_cost_price'],
#                                    'qty_allocated' : temp['qty_allocated'],
#                                    'qty_onhand_free' : temp['qty_onhand_free'],
#                                    })
#
#        return result1

    def default_get(self, cr, uid, fields, context=None):
        product_product_obj = self.pool.get('product.product')
        result1 = []
        if context is None:
            context = {}
        res = super(cost_price_fifo, self).default_get(cr, uid, fields, context=context)
        for product in product_product_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            result1 = self.stock_move_get(cr, uid, product.id, context=context)
        if 'lines_ids' in fields:
            res.update({'lines_ids': result1})
        return res

    _columns = {
        'lines_ids' : fields.one2many('price.fifo.lines', 'wizard_id', 'Fifo Lines', readonly=True),
    }

cost_price_fifo()

class price_fifo_lines(osv.osv_memory):
    _name = 'price.fifo.lines'
    _description = 'Fifo Lines'

    _columns = {
        'int_move_id': fields.many2one('stock.move', 'int move id', invisible=True),
        'int_doc_no': fields.char('Int Doc No', size=64, readonly=True),
        'move_id': fields.many2one('stock.move', 'move id', invisible=True),
        'document_no': fields.char('Doc No', size=64, readonly=True),
        'document_date': fields.datetime('Date Done', readonly=True),
        'purchase_no': fields.char('PO No', size=64, readonly=True),
        'wizard_id': fields.many2one('cost.price.fifo', 'wizard id', ondelete='cascade'),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True),
        'product_qty': fields.float('QOH', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure'),
        'doc_curr_id': fields.many2one('res.currency', 'Doc Curr'),
        'home_curr_id': fields.many2one('res.currency', 'Home Curr'),
        'doc_ucp': fields.float('Doc U-CP', digits_compute= dp.get_precision('Account'), readonly=True),
        'doc_total_ucp': fields.float('doc T-CP', digits_compute= dp.get_precision('Account'), readonly=True),
        'unit_cost_price': fields.float('Home U-CP', digits_compute= dp.get_precision('Account'), readonly=True),
        'total_cost_price': fields.float('Home T-CP', digits_compute= dp.get_precision('Account'), readonly=True),
        'qty_allocated': fields.float('Q-Allo', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'qty_onhand_free': fields.float('QOH Free', digits_compute=dp.get_precision('Product UoM'), readonly=True),
    }

price_fifo_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
