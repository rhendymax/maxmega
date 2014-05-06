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
        product_ids = product_product_obj.search(self.cr, self.uid, val_product,order='name')
        
        for product_id in product_product_obj.browse(self.cr, self.uid, product_ids):
            res_fifo = cost_price_fifo_obj.stock_move_get_with_date(self.cr, self.uid, product_id.id, date_searc=date_from, context=None)
            res = {}
            vals_ids = []
            res_temp1 = []
            res_temp2 = []
            res_temp3 = []
            date_group = {}
            balance_all = 0
            cost_all = 0
            if res_fifo:
                for res_f1 in res_fifo:
                    balance_all += res_f1['product_qty']
                    cost_all += res_f1['total_cost_price']
            stock_move_ids = stock_move_obj.search(self.cr, self.uid, [('product_id','=',product_id.id),('state','=','done')])
            if balance_all == 0 and not stock_move_ids:
                continue
            res = {
                'prod_name' : product_id.name or '',
                'balance_qty': balance_all or 0.00,
                'total_cost' : cost_all or 0.00,
            }

            for sm in stock_move_obj.browse(self.cr, self.uid, stock_move_ids, context=None):
                if sm.picking_id:
                    document_date = sm.picking_id.do_date or sm.picking_id.date_done or False
                    voucher_no = sm.picking_id.name
                else:
                    for si in sm.stock_inventory_ids:
                        voucher_no = si.name
                        document_date =  si.date_done or False
                if document_date and document_date >= date_from and document_date <= date_to:
                    key = ''
                    unit_cost_price = 0.00
                    total_unit_cost_price = 0.00
                    qty = uom_obj._compute_qty(self.cr, self.uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                    if sm.picking_id:
                        key = sm.picking_id and sm.picking_id.partner_id and sm.picking_id.partner_id.ref or False
                        if sm.picking_id.type != "internal":
                            mod = "PO"
                            type = "GR"
                            rate_id = False
                            p_curr_id = sm.picking_id.pricelist_id.currency_id.id
                            ptype_src = self.pool.get('res.company').browse(self.cr, self.uid, sm.picking_id.company_id.id, context=None).currency_id.id
                            if p_curr_id != ptype_src:
                                tgl = sm.picking_id.do_date or (sm.picking_id.date_done and datetime.strptime(sm.picking_id.date_done, '%Y-%m-%d %H:%M:%S').date()) or False
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
                                mod = "SO"
                                type = "DO"
                        else:
                            mod = "IC"
                            type = "TF"
                    else:
                        key = ''
                        mod = "IC"
                        unit_cost_price = sm.price_unit
                        total_unit_cost_price = unit_cost_price * qty
                        if sm.location_dest_usage == 'internal':
                            type = "PI-IN"
                        else:
                            type = "PI-OUT"
                    res_temp1.append({
                                    'inv_key' : product_id.name or '',
                                    'voucher_no' : voucher_no,
                                    'date' : document_date,
                                    'mod' : mod or '',
                                    'type' : type or '',
                                    'key' : key or '',
                                    'qty' : qty or 0.00,
                                    'total_unit_cost_price' : total_unit_cost_price or 0.00,
                                    'cost': unit_cost_price or 0.00,
                                    'sm_id' : sm.id,
                                    'source_location': sm.location_id.name or '',
                                    'dest_location': sm.location_dest_id.name or '',
                                     }
                                    )
                    date_group[sm.id] = document_date

            if res_temp1:
                for key, value in sorted(date_group.iteritems(), key=lambda (k,v): (v,k)):
                    for temp in res_temp1:
                        if temp['sm_id'] == key:
                            res_temp2.append({
                                            'voucher_no' : temp['voucher_no'],
                                            'inv_key' : temp['inv_key'],
                                            'date' : temp['date'],
                                            'mod' : temp['mod'],
                                            'type' : temp['type'],
                                            'key' : temp['key'],
                                            'qty' : temp['qty'],
                                            'total_unit_cost_price' : temp['total_unit_cost_price'],
                                            'cost': temp['cost'],
                                            'sm_id' : temp['sm_id'],
                                            'source_location': temp['source_location'],
                                            'dest_location': temp['dest_location'],
                                            })
            if res_temp2:
                for temp in res_temp2:
                    cost_output = 0
                    qty_output = temp['qty']
                    if temp['mod'] == 'SO' or (temp['mod'] == 'IC' and temp['type'] == 'PI-OUT'):
                        balance_all = balance_all - temp['qty']
                        fifo_control_ids = fifo_control_obj.browse(self.cr, self.uid, fifo_control_obj.search(self.cr, self.uid, [('out_move_id','=',temp['sm_id'])]), context=None)
                        total_unit_cost_price_1 = 0.00
                        if fifo_control_ids:
                            for val in fifo_control_ids:
                                qty_xx = uom_obj._compute_qty(self.cr, self.uid, val.in_move_id.product_uom.id, val.quantity, val.in_move_id.product_id.uom_id.id)
                                if val.in_move_id.picking_id:
                                    sm_id = val.int_in_move_id or val.in_move_id
                                    if sm_id.picking_id:
                                        rate_id_xx = False
                                        p_curr_id_xx = sm_id.picking_id.pricelist_id.currency_id.id
                                        ptype_src_xx = self.pool.get('res.company').browse(self.cr, self.uid, sm_id.picking_id.company_id.id, context=None).currency_id.id
                                        if p_curr_id_xx != ptype_src_xx:
                                            tgl_xx = sm_id.picking_id.do_date
                                            tgl_xx = datetime.strptime(tgl_xx, '%Y-%m-%d').date()
                                            rate_ids_xx = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', p_curr_id_xx),
                                                                                          ('name','<=', tgl_xx)
                                                                                          ])
                                            if rate_ids_xx:
                                                rate_id_xx = rate_ids_xx[0]
                                                rate = obj_currency_rate.browse(self.cr, self.uid, rate_id_xx, context=None).rate
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                            home_rate_ids_xx = obj_currency_rate.search(self.cr, self.uid, [('currency_id','=', ptype_src_xx),
                                                                                          ('name','<=', tgl_xx)
                                                                                          ])
                                            if home_rate_ids_xx:
                                                home_rate_id_xx = home_rate_ids_xx[0]
                                                home_rate = obj_currency_rate.browse(self.cr, self.uid, home_rate_id_xx, context=None).rate
                                            else:
                                                raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
            
                                        if rate_id_xx:
                                            unit_cost_price_xx = sm_id.price_unit * home_rate / rate
                                            total_unit_cost_price_xx = (qty_xx * sm_id.price_unit) * home_rate/ rate
                                        else:
                                            unit_cost_price_xx = currency_obj.compute(self.cr, self.uid, p_curr_id_xx, ptype_src_xx, sm_id.price_unit, round=False)
                                            total_unit_cost_price_xx = currency_obj.compute(self.cr, self.uid, p_curr_id_xx, ptype_src_xx, (qty_xx * sm_id.price_unit), round=False)
                                        unit_cost_price_xx = uom_obj._compute_price(self.cr, self.uid, sm_id.product_id.uom_id.id, unit_cost_price_xx, sm_id.product_uom.id)
                                        unit_cost_price_xx = product_product_obj.round_p(self.cr, self.uid, unit_cost_price_xx, 'Purchase Price',)
                                        total_unit_cost_price_xx = uom_obj._compute_price(self.cr, self.uid, sm_id.product_id.uom_id.id, total_unit_cost_price_xx, sm_id.product_uom.id)
                                        total_unit_cost_price_xx = product_product_obj.round_p(self.cr, self.uid, total_unit_cost_price_xx, 'Purchase Price',)
                                        total_unit_cost_price_1 += total_unit_cost_price_xx
                                    else:
                                        total_unit_cost_price_1 += (sm_id.price_unit * qty_xx)
                                else:
                                    total_unit_cost_price_1 += (val.in_move_id.price_unit * qty_xx)
                        cost_output = -1 * total_unit_cost_price_1
                        qty_output = -1 * temp['qty']
                        cost_all = cost_all - total_unit_cost_price_1
                    elif temp['mod'] == 'PO' or (temp['mod'] == 'IC' and temp['type'] == 'PI-IN'):
                        balance_all += temp['qty']
                        cost_all += temp['total_unit_cost_price']
                        cost_output = temp['total_unit_cost_price']
                    vals_ids.append({
                        'voucher_no' : temp['voucher_no'],
                        'date' : temp['date'],
                        'mod' : temp['mod'],
                        'type' : temp['type'],
                        'key' : temp['key'],
                        'qty' : qty_output,
                        'cost': cost_output,
                        'balance_qty': balance_all or 0.00,
                        'total_cost' : cost_all or 0.00,
                        'source_location': temp['source_location'],
                        'dest_location': temp['dest_location'],
                    })
            res['closing_balance_qty'] = balance_all or 0.00
            res['closing_total_cost'] = cost_all or 0.00
            res['pro_lines'] = vals_ids
            results.append(res)
        return results

    def _total_cost(self):
        return self.total_cost
    
    def _total_qty(self):
        return self.total_qty

report_sxw.report_sxw('report.inventory.ledger.details.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_ledger_details_report.rml', parser=inventory_ledger_details_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
