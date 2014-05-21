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

class inventory_free_balance_report(report_sxw.rml_parse):
    _name = 'inventory.free.balance.report'

    def set_context(self, objects, data, ids, report_type=None):
#        new_ids = ids
#        res = {}
#        self.product_from = data['form']['product_from'] and data['form']['product_from'][0] or False
#        self.product_to = data['form']['product_to'] and data['form']['product_to'][0] or False
#        self.location_from = data['form']['location_from'] and data['form']['location_from'][0] or False
#        self.location_to = data['form']['location_to'] and data['form']['location_to'][0] or False

        new_ids = ids
        res = {}
        product_product_obj = self.pool.get('product.product')
        stock_location_obj = self.pool.get('stock.location')
        qry_pp = ''
        val_pp = []
        qry_sl = ''
        val_sl = []
        pp_ids = False
        sl_ids = False
        
        pp_default_from = data['form']['product_default_from'] and data['form']['product_default_from'][0] or False
        pp_default_to = data['form']['product_default_to'] and data['form']['product_default_to'][0] or False
        pp_input_from = data['form']['product_input_from'] or False
        pp_input_to = data['form']['product_input_to'] or False

        if data['form']['product_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')

        elif data['form']['product_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(self.cr, self.uid, pp_default_from) and product_product_obj.browse(self.cr, self.uid, pp_default_from).name:
                data_found = True
                val_pp.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(self.cr, self.uid, pp_default_to) and product_product_obj.browse(self.cr, self.uid, pp_default_to).name:
                data_found = True
                val_pp.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, pp_default_to).name))
            if data_found:
                pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')
        elif data['form']['product_selection'] == 'input':
            data_found = False
            if pp_input_from:
                self.cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '>=', qry['name']))
            if pp_input_to:
                self.cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '<=', qry['name']))
            if data_found:
                pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')
        elif data['form']['product_selection'] == 'selection':
            if data['form']['product_ids']:
                pp_ids = data['form']['product_ids']
        self.pp_ids = pp_ids
        #Stock Location
        sl_default_from = data['form']['sl_default_from'] and data['form']['sl_default_from'][0] or False
        sl_default_to = data['form']['sl_default_to'] and data['form']['sl_default_to'][0] or False
        sl_input_from = data['form']['sl_input_from'] or False
        sl_input_to = data['form']['sl_input_to'] or False

        if data['form']['sl_selection'] == 'all_vall':
            sl_ids = stock_location_obj.search(self.cr, self.uid, val_sl, order='name ASC')

        elif data['form']['sl_selection'] == 'def':
            data_found = False
            if sl_default_from and stock_location_obj.browse(self.cr, self.uid, sl_default_from) and stock_location_obj.browse(self.cr, self.uid, sl_default_from).name:
                data_found = True
                val_sl.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, sl_default_from).name))
            if sl_default_to and stock_location_obj.browse(self.cr, self.uid, sl_default_to) and stock_location_obj.browse(self.cr, self.uid, sl_default_to).name:
                data_found = True
                val_sl.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, sl_default_to).name))
            if data_found:
                sl_ids = stock_location_obj.search(self.cr, self.uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'input':
            data_found = False
            if sl_input_from:
                self.cr.execute("select name " \
                                "from stock_location "\
                                "where name ilike '" + str(sl_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sl.append(('name', '>=', qry['name']))
            if sl_input_to:
                self.cr.execute("select name " \
                                "from stock_location "\
                                "where name ilike '" + str(sl_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sl.append(('name', '<=', qry['name']))
            if data_found:
                sl_ids = stock_location.search(self.cr, self.uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'selection':
            if data['form']['sl_ids']:
                sl_ids = data['form']['sl_ids']
#        location_ids = []
#        if sl_ids:
#            
#            for location in sl_ids:
#                sl_checking = stock_location.search(self.cr, self.uid, [('location_id','=',location)])
#                if sl_checking:
#                    continue
#                location_ids.append(location)
        self.sl_ids = sl_ids
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(inventory_free_balance_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(inventory_free_balance_report, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
#            'product_from': self._get_product_from,
#            'product_to': self._get_product_to,
#            'location_from': self._get_location_from,
#            'location_to': self._get_location_to,
            })

#    def _get_product_from(self):
#           return self.product_from and self.pool.get('product.product').browse(self.cr, self.uid, self.product_from).name or False
#
#    def _get_product_to(self):
#        return self.product_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_to).name or False
#
#    def _get_location_from(self):
#        return self.location_from and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_from).name or False
#
#    def _get_location_to(self):
#        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_to).name or False

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid

        stock_location_obj = self.pool.get('stock.location')
        product_product_obj = self.pool.get('product.product')
        plw_obj = self.pool.get('product.location.wizard')
        results         = []

        pp_ids = self.pp_ids or False
        sl_ids = self.sl_ids or False

        if sl_ids:
            for location in stock_location_obj.browse(self.cr, self.uid, sl_ids):
                sl_checking = stock_location_obj.search(self.cr, self.uid, [('location_id','=',location.id)])
                if sl_checking:
                    continue
                res = {}
                vals_ids = []
                total_cost = 0
                total_qty = 0
                if pp_ids:
                    for product_id in product_product_obj.browse(self.cr, self.uid, pp_ids):
                        ctx = {'location_id': location.id}
                        cpf_loc = plw_obj.stock_location_get(self.cr, self.uid, product_id.id, context=ctx)
                        if cpf_loc:
                            total_prod_cost = 0.00
                            total_prod_qty = 0.00
                            qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
                            for res_f1 in cpf_loc:
                                qty_onhand += res_f1['qty_available'] or 0.00
                                qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
                                qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
                                total_so_qty += res_f1['qty_booked'] or 0.00
                                qty_on_hand_free += res_f1['qty_free'] or 0.00
                                qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
                                qty_free_balance += res_f1['qty_free_balance'] or 0.00

                            vals_ids.append({
                            'prod_name' : product_id.name,
                            'qty_onhand' : qty_onhand,
                            'qty_grn_allocated' : qty_grn_allocated,
                            'qty_grn_unallocated' : qty_grn_unallocated,
                            'total_so_qty' : total_so_qty,
                            'qty_on_hand_free' : qty_on_hand_free,
                            'qty_on_hand_allocated' : qty_on_hand_allocated,
                            'qty_free_balance' : qty_free_balance,
                            })
                    if not vals_ids:
                        continue
                    res['pro_lines'] = vals_ids
                    res['loc_name'] = location.name or ''
                    results.append(res)


        results = results and sorted(results, key=lambda val_res: val_res['loc_name']) or []
        return results


#    def _get_lines(self):
#        results = []
#        val_product = []
#        val_location = []
#        product_product_obj = self.pool.get('product.product')
#        plw_obj = self.pool.get('product.location.wizard')
#        stock_location_obj = self.pool.get('stock.location')
#        product_from = self.product_from
#        product_to = self.product_to
#        location_from = self.location_from
#        location_to = self.location_to
#
#        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
#            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
#        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
#            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))
#        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
#            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
#        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
#            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))
#        val_location.append(('usage', '=', 'internal'))
#        product_ids = product_product_obj.search(self.cr, self.uid, val_product,order='name')
#        location_ids = stock_location_obj.search(self.cr, self.uid, val_location,order='name')
#        for location_id in location_ids:
#            sl = stock_location_obj.browse(self.cr, self.uid, location_id)
#            sl_checking = stock_location_obj.search(self.cr, self.uid, [('location_id','=',sl.id)])
#            if sl_checking:
#                continue
#            res = {}
#            vals_ids = []
#            total_cost = 0
#            total_qty = 0
#            for product_id in product_product_obj.browse(self.cr, self.uid, product_ids):
#                ctx = {'location_id': sl.id}
#                cpf_loc = plw_obj.stock_location_get(self.cr, self.uid, product_id.id, context=ctx)
#                if cpf_loc:
#                    vals_ids2 = []
#                    total_prod_cost = 0.00
#                    total_prod_qty = 0.00
#                    for res_f1 in cpf_loc:
#                        vals_ids2.append({
#                            'qty_onhand' : res_f1['qty_available'] or 0.00,
#                            'qty_grn_allocated' : res_f1['qty_incoming_booked'] or 0.00,
#                            'qty_grn_unallocated' : res_f1['qty_incoming_non_booked'] or 0.00,
#                            'total_so_qty' : res_f1['qty_booked'] or 0.00,
#                            'qty_on_hand_free' : res_f1['qty_free'] or 0.00,
#                            'qty_on_hand_allocated' : res_f1['qty_allocated'] or 0.00,
#                            'qty_free_balance' : res_f1['qty_free_balance'] or 0.00,
#                            })
#                    vals_ids.append({
#                    'prod_name' : product_id.name,
#                    'lines' : vals_ids2,
#                    })
#            if not vals_ids:
#                continue
#            res['pro_lines'] = vals_ids
#            res['loc_name'] = sl.name or ''
#            results.append(res)
#        return results

report_sxw.report_sxw('report.inventory.free.balance.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_free_balance_report.rml', parser=inventory_free_balance_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
