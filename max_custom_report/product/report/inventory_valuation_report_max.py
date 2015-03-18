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

class inventory_valuation_report_max(report_sxw.rml_parse):
    _name = 'inventory.valuation.report.max'

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
        return super(inventory_valuation_report_max, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(inventory_valuation_report_max, self).__init__(cr, uid, name, context=context)
        self.total_cost = 0.00
        self.total_qty = 0.00

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
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'

        product_from = self.product_from
        product_to = self.product_to
        location_from = self.location_from
        location_to = self.location_to

        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))
        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))
        val_location.append(('usage', '=', 'internal'))
        product_ids = product_product_obj.search(self.cr, self.uid, val_product,order='name')
        location_ids = stock_location_obj.search(self.cr, self.uid, val_location,order='name')
        for location_id in location_ids:
            sl = stock_location_obj.browse(self.cr, self.uid, location_id)
            sl_checking = stock_location_obj.search(self.cr, self.uid, [('location_id','=',sl.id)])
            if sl_checking:
                continue
            res = {}

            vals_ids = []
            total_cost = 0
            total_qty = 0
            for product_id in product_product_obj.browse(self.cr, self.uid, product_ids):
                cpf_loc = cost_price_fifo_obj.stock_move_get(self.cr, self.uid, product_id.id, location_id=location_id)
                if cpf_loc:
                    vals_ids2 = []
                    total_prod_cost = 0.00
                    total_prod_qty = 0.00
                    for res_f1 in cpf_loc:
                        document_date =  res_f1['document_date'] or  False
                        if document_date \
                            and document_date >= date_from and document_date <= date_to:
                            vals_ids2.append({
                                'int_no' : res_f1['int_doc_no'] or '',
                                'doc_no' : res_f1['document_no'] or '',
                                'date' : res_f1['document_date'] or False,
                                'location' : sl.name or '',
                                'qty_on_hand' : res_f1['product_qty'] or 0.00,
                                'unit_cost' : res_f1['unit_cost_price'] or 0.00,
                                'total_cost' : res_f1['total_cost_price'] or 0.00,
                                })
                            total_prod_cost += (res_f1['total_cost_price'] or 0.00)
                            total_prod_qty += (res_f1['product_qty'] or 0.00)
                            total_qty += (res_f1['product_qty'] or 0.00)
                            total_cost += (res_f1['total_cost_price'] or 0.00)
                            self.total_cost += (res_f1['total_cost_price'] or 0.00)
                            self.total_qty += (res_f1['product_qty'] or 0.00)
                    vals_ids.append({
                    'prod_name' : product_id.name,
                    'lines' : vals_ids2,
                    'loc_cost' : total_prod_cost,
                    'loc_qty' : total_prod_qty,
                    })
            if not vals_ids:
                continue
            res['total_cost'] = total_cost
            res['total_qty'] = total_qty
            res['pro_lines'] = vals_ids
            res['loc_name'] = sl.name or ''
            results.append(res)
        return results 

    def _total_cost(self):
        return self.total_cost

    def _total_qty(self):
        return self.total_qty

report_sxw.report_sxw('report.inventory.valuation.report.max_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_valuation_report_max.rml', parser=inventory_valuation_report_max, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
