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

class inventory_stock_aging_report(report_sxw.rml_parse):
    _name = 'inventory.stock.aging.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.product_from = data['form']['product_from'] and data['form']['product_from'][0] or False
        self.product_to = data['form']['product_to'] and data['form']['product_to'][0] or False
        self.location_from = data['form']['location_from'] and data['form']['location_from'][0] or False
        self.location_to = data['form']['location_to'] and data['form']['location_to'][0] or False
        self.brand_from = data['form']['brand_from'] and data['form']['brand_from'][0] or False
        self.brand_to = data['form']['brand_to'] and data['form']['brand_to'][0] or False

        return super(inventory_stock_aging_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(inventory_stock_aging_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'product_from': self._get_product_from,
            'product_to': self._get_product_to,
            'location_from': self._get_location_from,
            'location_to': self._get_location_to,
            'get_brand_from': self._get_brand_from,
            'get_brand_to': self._get_brand_to,
            })
      

    def _get_product_from(self):
           return self.product_from and self.pool.get('product.product').browse(self.cr, self.uid, self.product_from).name or False
    
    def _get_product_to(self):
        return self.product_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_to).name or False
    
    def _get_location_from(self):
        return self.location_from and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_from).name or False
    
    def _get_location_to(self):
        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_to).name or False

    def _get_brand_from(self):
        return self.brand_from and self.pool.get('product.brand').browse(self.cr, self.uid, self.brand_from).name or False
    
    def _get_brand_to(self):
        return self.brand_to and self.pool.get('product.brand').browse(self.cr, self.uid, self.brand_to).name or False


    def _get_lines(self):
        results = []
        val_brand = []
        val_product = []
        val_location = []
        product_brand_obj = self.pool.get('product.brand')
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        brand_from = self.brand_from
        brand_to = self.brand_to
        location_from = self.location_from
        location_to = self.location_to
        product_from = self.product_from
        product_to = self.product_to

        if brand_from and product_brand_obj.browse(self.cr, self.uid, brand_from) and product_brand_obj.browse(self.cr, self.uid, brand_from).name:
            val_brand.append(('name', '>=', product_brand_obj.browse(self.cr, self.uid, brand_from).name))
        if brand_to and product_brand_obj.browse(self.cr, self.uid, brand_to) and product_brand_obj.browse(self.cr, self.uid, brand_to).name:
            val_brand.append(('name', '>=', product_brand_obj.browse(self.cr, self.uid, brand_to).name))
        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))
        val_location.append(('usage', '=', 'internal'))
        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))

        location_ids = stock_location_obj.search(self.cr, self.uid, val_location,order='name')
        brand_ids = product_brand_obj.search(self.cr, self.uid, val_brand,order='name')
        for brand in product_brand_obj.browse(self.cr, self.uid, brand_ids):
            val_brand_prod = list(val_product)
            val_brand_prod.append(('brand_id', '=', brand.id))
            res = {}
            vals_ids = []
            total_qty = 0
            total_cost = 0
            product_ids = product_product_obj.search(self.cr, self.uid, val_brand_prod,order='name')
            for product_id in product_product_obj.browse(self.cr, self.uid, product_ids):
                cpf_loc = cost_price_fifo_obj.stock_move_get(self.cr, self.uid, product_id.id)
                if cpf_loc:
                    stock_group = {}
                    for res_f1 in cpf_loc:
                        if res_f1['location_id'] in location_ids:
                            if res_f1['location_id'] in stock_group:
                                vals = stock_group[res_f1['location_id']].copy()
                                try:
                                    d = datetime.strptime(res_f1['document_date'], '%Y-%m-%d')
                                except:
                                    d = datetime.strptime(res_f1['document_date'], '%Y-%m-%d %H:%M:%S')
                                d = d.date()
                                delta = datetime.now().date() - d
                                daysremaining = delta.days
                                if daysremaining < 31:
                                    vals['qty1'] += res_f1['product_qty']
                                    vals['cost1'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                elif daysremaining > 30 and daysremaining < 61:
                                    vals['qty2'] += res_f1['product_qty']
                                    vals['cost2'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                elif daysremaining > 60 and daysremaining < 91:
                                    vals['qty3'] += res_f1['product_qty']
                                    vals['cost3'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                elif daysremaining > 90 and daysremaining < 121:
                                    vals['qty4'] += res_f1['product_qty']
                                    vals['cost4'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                elif daysremaining > 120 and daysremaining < 151:
                                    vals['qty5'] += res_f1['product_qty']
                                    vals['cost5'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                elif daysremaining > 150 and daysremaining < 181:
                                    vals['qty6'] += res_f1['product_qty']
                                    vals['cost6'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                else:
                                    vals['qty7'] += res_f1['product_qty']
                                    vals['cost7'] += res_f1['total_cost_price']
                                    vals['qty'] += res_f1['product_qty']
                                    vals['cost'] += res_f1['total_cost_price']
                                stock_group[res_f1['location_id']] = vals
                            else:
                                try:
                                    d = datetime.strptime(res_f1['document_date'], '%Y-%m-%d')
                                except:
                                    d = datetime.strptime(res_f1['document_date'], '%Y-%m-%d %H:%M:%S')
                                d = d.date()
                                delta = datetime.now().date() - d
                                daysremaining = delta.days
                                qty1 = cost1 = qty2 = cost2 = qty3 = cost3 = 0
                                qty4 = cost4 = qty5 = cost5 = qty6 = cost6 = 0
                                qty7 = cost7 = qty = cost = 0
                                if daysremaining < 31:
                                    qty1 += res_f1['product_qty']
                                    cost1 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                elif daysremaining > 30 and daysremaining < 61:
                                    qty2 += res_f1['product_qty']
                                    cost2 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                elif daysremaining > 60 and daysremaining < 91:
                                    qty3 += res_f1['product_qty']
                                    cost3 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                elif daysremaining > 90 and daysremaining < 121:
                                    qty4 += res_f1['product_qty']
                                    cost4 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                elif daysremaining > 120 and daysremaining < 151:
                                    qty5 += res_f1['product_qty']
                                    cost5 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                elif daysremaining > 150 and daysremaining < 181:
                                    qty6 += res_f1['product_qty']
                                    cost6 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                else:
                                    qty7 += res_f1['product_qty']
                                    cost7 += res_f1['total_cost_price']
                                    qty += res_f1['product_qty']
                                    cost += res_f1['total_cost_price']
                                location_ids_vals = {
                                    'location_name': stock_location_obj.browse(self.cr, self.uid, res_f1['location_id']).name,
                                    'qty' : qty,
                                    'cost' : cost,
                                    'qty1' : qty1,
                                    'qty2' : qty2,
                                    'qty3' : qty3,
                                    'qty4' : qty4,
                                    'qty5' : qty5,
                                    'qty6' : qty6,
                                    'qty7' : qty7,
                                    'cost1' : cost1,
                                    'cost2' : cost2,
                                    'cost3' : cost3,
                                    'cost4' : cost4,
                                    'cost5' : cost5,
                                    'cost6' : cost6,
                                    'cost7' : cost7,
                                    }
                                stock_group[res_f1['location_id']] = location_ids_vals

                    for st in stock_group:
                        total_qty += stock_group[st]['qty']
                        total_cost += stock_group[st]['cost']
                        vals_ids.append({
                            'inv_key' : product_id.name,
                            'loc_name' : stock_group[st]['location_name'],
                            'qty' : stock_group[st]['qty'],
                            'qty1' : stock_group[st]['qty1'],
                            'qty2' : stock_group[st]['qty2'],
                            'qty3' : stock_group[st]['qty3'],
                            'qty4' : stock_group[st]['qty4'],
                            'qty5' : stock_group[st]['qty5'],
                            'qty6' : stock_group[st]['qty6'],
                            'qty7' : stock_group[st]['qty7'],
                            'cost' : stock_group[st]['cost'],
                            'cost1' : stock_group[st]['cost1'],
                            'cost2' : stock_group[st]['cost2'],
                            'cost3' : stock_group[st]['cost3'],
                            'cost4' : stock_group[st]['cost4'],
                            'cost5' : stock_group[st]['cost5'],
                            'cost6' : stock_group[st]['cost6'],
                            'cost7' : stock_group[st]['cost7'],
                            })
            if not vals_ids:
                continue
            res['pro_lines'] = vals_ids
            res['brand_name'] = brand.name or ''
            res['total_qty'] = total_qty
            res['total_cost'] = total_cost
            results.append(res)
        return results

report_sxw.report_sxw('report.inventory.stock.aging.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_stock_aging_report.rml', parser=inventory_stock_aging_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
