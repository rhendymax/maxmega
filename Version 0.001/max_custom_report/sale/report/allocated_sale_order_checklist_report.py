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

class allocated_sale_order_checklist_report(report_sxw.rml_parse):
    _name = 'allocated.sale.order.checklist.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.product_id_from = data['form']['product_id_from'] and data['form']['product_id_from'][0] or False
        self.product_id_to = data['form']['product_id_to'] and data['form']['product_id_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(allocated_sale_order_checklist_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(allocated_sale_order_checklist_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_product_id_from': self._get_product_from,
            'get_product_id_to': self._get_product_to,
            })

    def _get_product_from(self):
        return self.product_id_from and self.pool.get('product.product').browse(self.cr, self.uid,self.product_id_from).name or False
    
    def _get_product_to(self):
        return self.product_id_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_id_to).name or False

    def _get_lines(self):
        results = []
        val_prod = []
        line_ids = []
        prod_id = False
        prod_ids = []
        prod_ids_name = {}
        prod_ids_lines = {}
        product_product_obj = self.pool.get('product.product')
        product_id_from = self.product_id_from
        product_id_from_name = product_id_from and product_product_obj.browse(self.cr, self.uid, product_id_from) and product_product_obj.browse(self.cr, self.uid, product_id_from).name or False
        product_id_to = self.product_id_to
        product_id_to_name = product_id_to and product_product_obj.browse(self.cr, self.uid, product_id_to) and product_product_obj.browse(self.cr, self.uid, product_id_to).name or False
        criteria = ""
        if product_id_from_name:
            criteria += " AND pt.name >= '" + str(product_id_from_name) + "'"
        if product_id_to_name:
            criteria += " AND pt.name <= '" + str(product_id_to_name) + "'"


        self.cr.execute("select  sol.product_id, \
        pb.name as brand_name, \
        pt.name as product_name, \
        so.name as so_name, \
        rp.ref as customer_ref, \
        rp.name as customer_name, \
        pc.name as cpn, \
        sl.name as location_name, \
        COALESCE(sol.qty_onhand_allocated, 0) + (select COALESCE(sum(received_qty),0) \
        from sale_allocated where sale_line_id = sol.id) \
        - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
        where sm2.sale_line_id = sol.id and sm2.state = 'done') as qty, \
        pu.name as uom \
        from sale_order_line sol \
        left join product_uom pu on sol.product_uom = pu.id \
        left join stock_location sl on sol.location_id = sl.id \
        left join product_customer pc on sol.product_customer_id = pc.id \
        left join product_template pt on sol.product_id = pt.id \
        left join product_product pp on pt.id = pp.id \
        left join product_brand pb on pp.brand_id = pb.id \
        left join sale_order so on sol.order_id = so.id \
        left join res_partner rp on so.partner_id = rp.id \
        where sol.state not in ('draft','done','cancel') \
        and COALESCE(sol.qty_onhand_allocated, 0) \
        + (select COALESCE(sum(received_qty),0) from sale_allocated where sale_line_id = sol.id) \
        - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
        where sm2.sale_line_id = sol.id and sm2.state = 'done') > 0 " + str(criteria) + " \
        order by pb.name, pt.name, pp.id")
        res_general = self.cr.dictfetchall()
        
        for r in res_general:
            if r['product_id'] not in prod_ids:
                prod_ids.append(r['product_id'])
                prod_ids_name[r['product_id']] = '[' + str (r['brand_name']) + '] ' + str(r['product_name'])
                if prod_id:
                    prod_ids_lines[prod_id] = line_ids
                    line_ids = []
                prod_id = r['product_id']

            line_ids.append({
                             'so_name' : r['so_name'],
                             'customer_name' : '[' + str(r['customer_ref']) + '] ' + str(r['customer_name']),
                             'cpn' : r['cpn'],
                             'location' : r['location_name'],
                             'qty' : r['qty'],
                             'uom' : r['uom']
                             })

        if prod_id:
            prod_ids_lines[prod_id] = line_ids
            line_ids = []

        if prod_ids:

            for product_id in prod_ids:
                res = {}
                res['name'] = prod_ids_name[product_id]
                res['lines'] = prod_ids_lines[product_id]
                results.append(res)

#
#            if product_id = False:
#                product_id = r['product_id']
#                res['name'] = '[' + str (r['brand_name']) + '] ' + str(r['product_name'])
#            else:
#                if 
#                res['lines'] = line_ids
#
#
#
#        product_id_from = self.product_id_from
#        product_id_to = self.product_id_to
#        
#        sale_order_line_obj = self.pool.get('sale.order.line')
#        product_uom_obj = self.pool.get('product.uom')
#        stock_move_obj = self.pool.get('stock.move')
#
#        if product_id_from and product_product_obj.browse(self.cr, self.uid, product_id_from) and product_product_obj.browse(self.cr, self.uid, product_id_from).name:
#            val_prod.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_id_from).name))
#        if product_id_to and product_product_obj.browse(self.cr, self.uid, product_id_to) and product_product_obj.browse(self.cr, self.uid, product_id_to).name:
#            val_prod.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_id_to).name))
#
#
#        prod_ids = product_product_obj.search(self.cr, self.uid, val_prod, order='ref ASC')
#        if prod_ids:
#            product_ids = product_product_obj.browse(self.cr, self.uid, prod_ids)
#            for product in product_ids:
#                sale_order_line_ids = sale_order_line_obj.browse(self.cr, self.uid, sale_order_line_obj.search(self.cr, self.uid, [('product_id','=',product.id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')]), context=None)
#                allocated_onhand = 0.00
#                if sale_order_line_ids:
#                    res = {}
#                    line_ids = []
#                    for val in sale_order_line_ids:
#                        allocated_onhand = val.qty_onhand_count
#                        stock_move_ids = stock_move_obj.search(self.cr, self.uid, [('sale_line_id','=',val.id),('state','=','done')])
#                        do_qty = 0.00
#                        if stock_move_ids:
#                            for stock_move_id in stock_move_ids:
#                                stock_move = stock_move_obj.browse(self.cr, self.uid, stock_move_id, context=None)
#                                do_qty = do_qty + product_uom_obj._compute_qty(self.cr, self.uid, stock_move.product_uom.id, stock_move.product_qty, product.uom_id.id)
#                        if (allocated_onhand - do_qty) > 0:
#                            
##                            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(val, ''))
#                            line_ids.append({
#                                            'sale_order_name' : val.order_id.name,
#                                            'customer_ref' : '',
#                                            'cpn' : '',
#                                            'qty' : 0,
#                                            'uom' : ''
#                                            })
#                    if line_ids:
#                        res['name'] = product.name
#                        res['lines'] = line_ids
#                        results.append(res)
##        
##        
##        sale_order_line_ids = sale_order_line_obj.browse(self.cr, self.uid, sale_order_line_obj.search(cr, uid, [('product_id','=',product.id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')]), context=context)
##        allocated_onhand = 0.00
##        if sale_order_line_ids:
##            loc_vals = []
##            loc_qty = {}
##            for val in sale_order_line_ids:
##                allocated_onhand = val.qty_onhand_count
##                stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',val.id),('state','=','done')])
##                do_qty = 0.00
##                if stock_move_ids:
##                    for stock_move_id in stock_move_ids:
##                        stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
##                        do_qty = do_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, product.uom_id.id)
##                if (allocated_onhand - do_qty) > 0:
#                    
#
##        val_part = []
##        val_inv = []
##        date_from = self.date_from
##        date_to =  self.date_to + ' ' + '23:59:59'
##        code_from = self.partner_code_from
##        code_to = self.partner_code_to
##        inv_from = self.inv_from
##        inv_to = self.inv_to
##        account_invoice_obj = self.pool.get('account.invoice')
##        res_partner_obj = self.pool.get('res.partner')
##
##        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
##            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
##        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
##            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
##        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
##            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
##        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
##            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
##        val_part.append(('customer', '=', True))
##        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
##        if part_ids:
##            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
##            val_inv.append(('date_invoice', '>=', date_from))
##            val_inv.append(('date_invoice', '<=', date_to))
##            val_inv.append(('type', 'in', ['out_invoice','out_refund']))
##            val_inv.append(('state', 'in', ['open','paid']))
##            for part in partner_ids:
##                val_inv2 = list(val_inv)
##                val_inv2.append(('partner_id', '=', part.id))
##                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
##                if inv_ids:
##                    line_ids = []
##                    res = {}
##                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
##                        line_ids.append(inv_id)
##                    res['ref'] = part.ref
##                    res['name'] = part.name
##                    res['lines'] = line_ids
##                    results.append(res)
        return results

report_sxw.report_sxw('report.allocated.sale.order.checklist.report_landscape', 'sale.order',
    'addons/max_custom_report/sale/report/allocated_sale_order_checklist_report.rml', parser=allocated_sale_order_checklist_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
