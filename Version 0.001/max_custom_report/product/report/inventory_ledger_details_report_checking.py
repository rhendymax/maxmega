# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
# Copyright (c) 2006-2010 OpenERP S.A
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from report import report_sxw
import locale
locale.setlocale(locale.LC_ALL, '')

class inventory_ledger_details_report(report_sxw.rml_parse):
    _name = 'inventory.ledger.details.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.product_from = data['form']['product_from'] and data['form']['product_from'][0] or False
        self.product_to = data['form']['product_to'] and data['form']['product_to'][0] or False
        self.location_from = data['form']['location_from'] and data['form']['location_from'][0] or False
        self.location_to = data['form']['location_to'] and data['form']['location_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(inventory_ledger_details_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(inventory_ledger_details_report, self).__init__(cr, uid, name, context=context)
        self.total_cost = 0.00
        self.total_qty = 0.00
#      
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'total_cost' : self._total_cost,
            'total_qty' : self._total_qty,
            'product_from': self._get_product_from,
            'product_to': self._get_product_to,
            'location_from': self._get_location_from,
            'location_to': self._get_location_to,
            })
      

    def _get_product_from(self):
           return self.product_from and self.pool.get('product.product').browse(self.cr, self.uid, self.product_from).name or False
    
    def _get_product_to(self):
        return self.product_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_to).name or False
    
    def _get_location_from(self):
        return self.location_from and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_from).name or False
    
    def _get_location_to(self):
        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_to).name or False
#        
    def _get_lines(self):
        results = []
        val_product = []
        val_location = []
        res_temp1 = []
        res_temp2 = []
        res_temp3 = []
        date_group = {}
        product_group = {}
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        product_from = self.product_from
        product_to = self.product_to
        location_from = self.location_from
        location_to = self.location_to
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(code_from, code_to))

        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        stock_move_obj = self.pool.get('stock.move')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        obj_currency_rate = self.pool.get('res.currency.rate')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))
        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))

#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
#            val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_from).name))
#        if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
#            val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_to).name))
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(vals, code_to))

#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part)
        product_ids = product_product_obj.search(self.cr, self.uid, val_product,order='name')
        location_ids = stock_location_obj.search(self.cr, self.uid, val_location)
#        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)
        for product_id in product_ids:
            pp = product_product_obj.browse(self.cr, self.uid, product_id)
            res_fifo = cost_price_fifo_obj.stock_move_get_with_date(self.cr, self.uid, pp.id, date_searc=date_from, context=None)
            balance_all = 0
            cost_all = 0
            if res_fifo:
                for res_f1 in res_fifo:
                    product_qty = res_f1['product_qty']
                    total_cost_price = res_f1['total_cost_price']
                    balance_all = product_qty + balance_all
                    cost_all = total_cost_price + cost_all
#            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(balance_all, cost_all))

            res = {
                'inv_key' : pp.name or '',
                'date' : False,
                'condition' : '',
                'mode' : '',
                'key' : '',
                'name': 'Opening Balance(Qty/Cost)',
                'qty' : '',
                'cost': '',
                'balance_qty': balance_all or 0.00,
                'total_cost' : cost_all or 0.00,
            }
            results.append(res)
            res = {}
            stock_move_ids = stock_move_obj.search(self.cr, self.uid, [('product_id','=',product_id),('state','=','done')])
            res_temp1 = []
            res_temp2 = []
            res_temp3 = []
            if stock_move_ids:
#                print stock_move_ids
#                raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %('xx', stock_move_ids))
                for sm in stock_move_obj.browse(self.cr, self.uid, stock_move_ids, context=None):
                    if sm.picking_id:
                        document_date =  sm.picking_id and sm.picking_id.date_done or False
                    else:
                        for si in sm.stock_inventory_ids:
                            document_date =  si.date_done or False
                    if document_date \
                        and document_date >= date_from and document_date <= date_to:
                        key = ''
                        name = ''
                        unit_cost_price = 0.00
                        total_unit_cost_price = 0.00
                        qty = uom_obj._compute_qty(self.cr, self.uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                        if sm.picking_id:
                            key = sm.picking_id and sm.picking_id.partner_id and sm.picking_id.partner_id.ref or False
                            name = sm.picking_id and sm.picking_id.partner_id and sm.picking_id.partner_id.name or False
                            if sm.picking_id.type != "internal":
                                condition = "Inc"
                                mode = "IN"
                                rate_id = False
                                p_curr_id = sm.picking_id.pricelist_id.currency_id.id
                                ptype_src = self.pool.get('res.company').browse(self.cr, self.uid, sm.picking_id.company_id.id, context=None).currency_id.id
                                if p_curr_id != ptype_src:
                                    tgl = sm.picking_id.date_done
                                    tgl = datetime.strptime(tgl, '%Y-%m-%d %H:%M:%S').date()
                                    rate_ids = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', p_curr_id),
                                                                                  ('name','<=', tgl)
                                                                                  ])
                                    if rate_ids:
                                        rate_id = rate_ids[0]
                                    else:
                                        raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                    home_rate_ids = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', ptype_src),
                                                                                  ('name','<=', tgl)
                                                                                  ])
                                    if home_rate_ids:
                                        home_rate_id = home_rate_ids[0]
                                    else:
                                        raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
    
                                if rate_id:
                                    unit_cost_price = sm.price_unit * obj_currency_rate.browse(self.cr, self.uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id, context=None).rate)
                                    total_unit_cost_price = (qty * sm.price_unit) * obj_currency_rate.browse(self.cr, self.uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id, context=None).rate)
                                else:
                                    unit_cost_price = currency_obj.compute(self.cr, self.uid, p_curr_id, ptype_src, sm.price_unit, round=False)
                                    total_unit_cost_price = currency_obj.compute(self.cr, self.uid, p_curr_id, ptype_src, (qty * sm.price_unit), round=False)
                                unit_cost_price = uom_obj._compute_price(self.cr, self.uid, sm.product_id.uom_id.id, unit_cost_price, sm.product_uom.id)
                                unit_cost_price = product_product_obj.round_p(self.cr, self.uid, unit_cost_price, 'Purchase Price',)
                                total_unit_cost_price = uom_obj._compute_price(self.cr, self.uid, sm.product_id.uom_id.id, total_unit_cost_price, sm.product_uom.id)
                                total_unit_cost_price = product_product_obj.round_p(self.cr, self.uid, total_unit_cost_price, 'Purchase Price',)

                                if sm.picking_id.type == 'out':
                                    condition = "DO"
                                    mode = "OUT"
                            else:
                                condition = "Internal"
                                mode = "INT"
                        else:
                            key = ''
                            name = ''
                            condition = "PI"
                            unit_cost_price = sm.price_unit
                            total_unit_cost_price = unit_cost_price * qty
                            if sm.location_dest_usage == 'internal':
                                mode = "IN"
                            else:
                                mode = "OUT"
                        res_temp1.append({
                                        'inv_key' : pp.name or '',
                                        'date' : document_date,
                                        'condition' : condition or '',
                                        'mode' : mode or '',
                                        'key' : key or '',
                                        'name': name or '',
                                        'qty' : qty or 0.00,
                                        'total_unit_cost_price' : total_unit_cost_price or 0.00,
                                        'cost': unit_cost_price or 0.00,
                                        'sm_id' : sm.id,
                                         }
                                        )
                        #sort by date
                        date_group[sm.id] = document_date

                if res_temp1:
                    for key, value in sorted(date_group.iteritems(), key=lambda (k,v): (v,k)):

                        for temp in res_temp1:
                            if temp['sm_id'] == key:
                                product_group[temp['sm_id']] = temp['inv_key']
                                res_temp2.append({
                                                'inv_key' : temp['inv_key'],
                                                'date' : temp['date'],
                                                'condition' : temp['condition'],
                                                'mode' : temp['mode'],
                                                'key' : temp['key'],
                                                'name': temp['name'],
                                                'qty' : temp['qty'],
                                                'total_unit_cost_price' : temp['total_unit_cost_price'],
                                                'cost': temp['cost'],
                                                'sm_id' : temp['sm_id'],
                                                })
                if res_temp2:
                    for key, value in sorted(product_group.iteritems(), key=lambda (k,v): (v,k)):
    #                for key, value in sorted(fiscal_position_group.iteritems(), key=lambda (k,v): (v,k)):
                        for temp in res_temp2:
                            if temp['sm_id'] == key:
                                res_temp3.append({
                                                'inv_key' : temp['inv_key'],
                                                'date' : temp['date'],
                                                'condition' : temp['condition'],
                                                'mode' : temp['mode'],
                                                'key' : temp['key'],
                                                'name': temp['name'],
                                                'qty' : temp['qty'],
                                                'total_unit_cost_price' : temp['total_unit_cost_price'],
                                                'cost': temp['cost'],
                                                'sm_id' : temp['sm_id'],
                                                })
    
    
                if res_temp3:
                    for temp in res_temp3:
                        if temp['mode'] == 'OUT':
                            balance_all = balance_all - temp['qty']
                            fifo_control_ids = fifo_control_obj.browse(self.cr, self.uid, fifo_control_obj.search(self.cr, self.uid, [('out_move_id','=',temp['sm_id'])]), context=None)
                            total_unit_cost_price_1 = 0.00
                            if fifo_control_ids:
                                for val in fifo_control_ids:
                                    qty_xx = uom_obj._compute_qty(self.cr, self.uid, val.in_move_id.product_uom.id, val.quantity, val.in_move_id.product_id.uom_id.id)

                                    if val.in_move_id.picking_id:

                                        if val.in_move_id.picking_id.type == 'internal':
                                            qty_int = qty_xx
                                            internal_move_control_ids = cost_price_fifo_obj.internal_get(self.cr, self.uid, val.in_move_id.id)
                                            if internal_move_control_ids:
                                                for int in internal_move_control_ids:
                                                    if qty_int > 0:
                                                        int_sm = stock_move_obj.browse(self.cr, self.uid, int['move_id'], context=None)
                                                        qty_int = qty_int - int['product_qty']
                                                        if int_sm.picking_id:
                                                            total_unit_cost_price_int = 0.00
                                                            rate_id_int = False
                                                            p_curr_id_int = int_sm.picking_id.pricelist_id.currency_id.id
                                                            ptype_src_int = self.pool.get('res.company').browse(self.cr, self.uid, int_sm.picking_id.company_id.id, context=None).currency_id.id
                                                            if p_curr_id_int != ptype_src_int:
                                                                
                                                                tgl_int = int_sm.picking_id.date_done
                                                                tgl_int = datetime.strptime(tgl_int, '%Y-%m-%d %H:%M:%S').date()
                                                                rate_ids_int = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', p_curr_id_int),
                                                                                                              ('name','<=', tgl_int)
                                                                                                              ])
                                                                if rate_ids_int:
                                                                    rate_id_int = rate_ids_int[0]
                                                                else:
                                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                                                home_rate_ids_int = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', ptype_src_int),
                                                                                                              ('name','<=', tgl_int)
                                                                                                              ])
                                                                if home_rate_ids_int:
                                                                    home_rate_id_int = home_rate_ids_int[0]
                                                                else:
                                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
                                
                                                            if rate_id_int:
                                                                unit_cost_price_int = int_sm.price_unit * obj_currency_rate.browse(self.cr, self.uid, home_rate_id_int, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id_int, context=None).rate)
                                                                total_unit_cost_price_int = (int['product_qty'] * int_sm.price_unit) * obj_currency_rate.browse(self.cr, self.uid, home_rate_id_int, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id_int, context=None).rate)
                                                            else:
                                                                unit_cost_price_int = currency_obj.compute(self.cr, self.uid, p_curr_id_int, ptype_src_int, int_sm.price_unit, round=False)
                                                                total_unit_cost_price__int = currency_obj.compute(self.cr, self.uid, p_curr_id_int, ptype_src_int, (int['product_qty'] * int_sm.price_unit), round=False)
                                                            unit_cost_price_int = uom_obj._compute_price(self.cr, self.uid, int_sm.product_id.uom_id.id, unit_cost_price_int, int_sm.product_uom.id)
                                                            unit_cost_price_int = product_product_obj.round_p(self.cr, self.uid, unit_cost_price_int, 'Purchase Price',)
                                                            total_unit_cost_price_int = uom_obj._compute_price(self.cr, self.uid, int_sm.product_id.uom_id.id, total_unit_cost_price_int, int_sm.product_uom.id)
                                                            total_unit_cost_price_int = product_product_obj.round_p(self.cr, self.uid, total_unit_cost_price__int, 'Purchase Price',)
                                                            total_unit_cost_price_1 = total_unit_cost_price_1 + total_unit_cost_price_int
                                                        else:
                                                            total_unit_cost_price_1 = total_unit_cost_price_1 + (int['product_qty'] * int_sm.price_unit)
                                                    #raise osv.except_osv(_('Message Error!'), _(str(internal_move_control_ids) + str(val.int_in_move_id.picking_id.type)))
                                        else:
                                            rate_id_xx = False
                                            p_curr_id_xx = val.in_move_id.picking_id.pricelist_id.currency_id.id
                                            ptype_src_xx = self.pool.get('res.company').browse(self.cr, self.uid, val.in_move_id.picking_id.company_id.id, context=None).currency_id.id
                                            if p_curr_id_xx != ptype_src_xx:
            
                                                tgl_xx = val.in_move_id.picking_id.date_done
                                                tgl_xx = datetime.strptime(tgl_xx, '%Y-%m-%d %H:%M:%S').date()
                                                rate_ids_xx = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', p_curr_id_xx),
                                                                                              ('name','<=', tgl_xx)
                                                                                              ])
                                                if rate_ids_xx:
                                                    rate_id_xx = rate_ids_xx[0]
                                                else:
                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                                home_rate_ids_xx = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', ptype_src_xx),
                                                                                              ('name','<=', tgl_xx)
                                                                                              ])
                                                if home_rate_ids_xx:
                                                    home_rate_id_xx = home_rate_ids_xx[0]
                                                else:
                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
                
                                            if rate_id_xx:
                                                unit_cost_price_xx = val.in_move_id.price_unit * obj_currency_rate.browse(self.cr, self.uid, home_rate_id_xx, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id_xx, context=None).rate)
                                                total_unit_cost_price_xx = (qty_xx * val.in_move_id.price_unit) * obj_currency_rate.browse(self.cr, self.uid, home_rate_id_xx, context=None).rate/ (obj_currency_rate.browse(self.cr, self.uid, rate_id_xx, context=None).rate)
                                            else:
                                                unit_cost_price_xx = currency_obj.compute(self.cr, self.uid, p_curr_id_xx, ptype_src_xx, val.in_move_id.price_unit, round=False)
                                                total_unit_cost_price_xx = currency_obj.compute(self.cr, self.uid, p_curr_id_xx, ptype_src_xx, (qty_xx * val.in_move_id.price_unit), round=False)
                                            unit_cost_price_xx = uom_obj._compute_price(self.cr, self.uid, val.in_move_id.product_id.uom_id.id, unit_cost_price_xx, val.in_move_id.product_uom.id)
                                            unit_cost_price_xx = product_product_obj.round_p(self.cr, self.uid, unit_cost_price_xx, 'Purchase Price',)
                                            total_unit_cost_price_xx = uom_obj._compute_price(self.cr, self.uid, val.in_move_id.product_id.uom_id.id, total_unit_cost_price_xx, val.in_move_id.product_uom.id)
                                            total_unit_cost_price_xx = product_product_obj.round_p(self.cr, self.uid, total_unit_cost_price_xx, 'Purchase Price',)
    
                                            total_unit_cost_price_1 = total_unit_cost_price_xx + total_unit_cost_price_1
                                    else:
                                        total_unit_cost_price_1 = (val.in_move_id.price_unit * qty_xx) + total_unit_cost_price_1
#                                    raise osv.except_osv(_('Message Error!'), _(str(temp['inv_key']) + 'xxx' + str(val.in_move_id)))

                            cost_all = cost_all - total_unit_cost_price_1
                        elif temp['mode'] == 'IN':
                            balance_all = temp['qty'] + balance_all
                            cost_all = temp['total_unit_cost_price'] + cost_all
                        res = {
                            'inv_key' : '',
                            'date' : temp['date'],
                            'condition' : temp['condition'],
                            'mode' : temp['mode'],
                            'key' : temp['key'],
                            'name': temp['name'],
                            'qty' : temp['qty'],
                            'cost': temp['cost'],
                            'balance_qty': balance_all or 0.00,
                            'total_cost' : cost_all or 0.00,
                        }
                        results.append(res)
                        res = {}
        return results 

    def _total_cost(self):
        return self.total_cost
    
    def _total_qty(self):
        return self.total_qty
#        for pur in purcs:
#            date_po =  pur.order_id and pur.order_id.date_order or False
#            state = pur.order_id and pur.order_id.state or ''
#            partner_id = pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.id or False
#            po_id = pur.order_id and pur.order_id.id or False
#            if date_po and state == 'approved' \
#                and date_po >= date_from and date_po <= date_to \
#                and pur.oustanding_qty > 0 and partner_id in part_ids \
#                and po_id in po_ids:
#                partner_name = ''
#
#                if pur.order_id:
#                    partner_name = pur.order_id.partner_id and pur.order_id.partner_id.name or ''
#                if partner_name: partner_name = partner_name.replace('&','&amp;')
#                    
#                res = {
#                    's_name' : pur.order_id and partner_name or '',
#                    's_ref' : pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.ref or '',
#                    'order_name' : pur.order_id and pur.order_id.name or '',
#                    'part_name' : pur.product_id and pur.product_id.name or '',
#                    'etd' : pur.estimated_time_departure or False,
#                    'order_qty' : pur.product_qty or '',
#                    'unit_price': pur.price_unit,
#                    'oustanding': pur.oustanding_qty or '',
#                }
#                results.append(res)
#                res = {}

report_sxw.report_sxw('report.inventory.ledger.details.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_ledger_details_report.rml', parser=inventory_ledger_details_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
