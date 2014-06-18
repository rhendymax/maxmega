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
        product_product_obj = self.pool.get('product.product')
        qry_pp = ''
        val_pp = []
        pp_ids = False

        pp_default_from = data['form']['pp_default_from'] and data['form']['pp_default_from'][0] or False
        pp_default_to = data['form']['pp_default_to'] and data['form']['pp_default_to'][0] or False
        pp_input_from = data['form']['pp_input_from'] or False
        pp_input_to = data['form']['pp_input_to'] or False

        if data['form']['pp_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')

        if data['form']['pp_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(self.cr, self.uid, pp_default_from) and product_product_obj.browse(self.cr, self.uid, pp_default_from).name:
                data_found = True
                val_pp.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(self.cr, self.uid, pp_default_to) and product_product_obj.browse(self.cr, self.uid, pp_default_to).name:
                data_found = True
                val_pp.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, pp_default_to).name))
            if data_found:
                pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')
        elif data['form']['pp_selection'] == 'input':
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
        elif data['form']['pp_selection'] == 'selection':
            if data['form']['pp_ids']:
                pp_ids = data['form']['pp_ids']
        self.pp_ids = pp_ids
    #        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(allocated_sale_order_checklist_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(allocated_sale_order_checklist_report, self).__init__(cr, uid, name, context=context)
        self.grand_total = 0
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'grand_total' : self._grand_total,
            })

    def _grand_total(self):
        return self.grand_total
    
    def _get_lines(self):
        results = []
        cr              = self.cr
        uid             = self.uid
        pp_obj = self.pool.get('product.product')
        pp_ids = self.pp_ids or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND pp.id = " + str(pp_ids[0]) + " ") or "AND pp.id IN " + str(tuple(pp_ids)) + " ")) or "AND pp.id IN (0) "
        line_ids = []
        
        cr.execute("select  DISTINCT sol.product_id \
                from sale_order_line sol \
                left join product_template pt on sol.product_id = pt.id \
                left join product_product pp on pt.id = pp.id \
                left join product_brand pb on pp.brand_id = pb.id \
                where sol.state not in ('draft','done','cancel') \
                and COALESCE(sol.qty_onhand_allocated, 0) \
                + (select COALESCE(sum(received_qty),0) from sale_allocated where sale_line_id = sol.id) \
                - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
                where sm2.sale_line_id = sol.id and sm2.state = 'done') > 0 " \
                + pp_qry )
#                " order by pb.name, pt.name")
        product_ids_vals = []
        qry = cr.dictfetchall()
        if qry:
            for r in qry:
                product_ids_vals.append(r['product_id'])

        product_ids_vals_qry = (len(product_ids_vals) > 0 and ((len(product_ids_vals) == 1 and "where pp.id = " +  str(product_ids_vals[0]) + " ") or "where pp.id IN " +  str(tuple(product_ids_vals)) + " ")) or "where pp.id IN (0) "

        cr.execute(
                "SELECT pp.id, pt.name, pb.name as brand_name " \
                "FROM product_product pp inner join product_template pt on pp.id = pt.id " \
                "left join product_brand pb on pp.brand_id = pb.id " \
                + product_ids_vals_qry \
                + " order by pt.name")
        qry1 = cr.dictfetchall()
        if qry1:
            for s in qry1:
                cr.execute("select sol.product_id, \
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
                    where sm2.sale_line_id = sol.id and sm2.state = 'done') > 0 " \
                    "and sol.product_id = " + str(s['id']) + " "\
                    " order by pb.name, pt.name")

                qry3 = cr.dictfetchall()
                val = []
                if qry3:
                    for t in qry3:
                        val.append({
                                 'so_name' : t['so_name'],
                                 'customer_name' : '[' + str(t['customer_ref']) + '] ' + str(t['customer_name']),
                                 'cpn' : t['cpn'],
                                 'location' : t['location_name'],
                                 'qty' : t['qty'],
                                 'uom' : t['uom']
                                    })
                        self.grand_total += t['qty'] or 0
                results.append({
                    'name' : '[' + s['brand_name'] + ']' + s['name'],
                    'vals' : val,
                    })

        results = results and sorted(results, key=lambda val_res: val_res['name']) or []
        results = results
                
        return results

report_sxw.report_sxw('report.allocated.sale.order.checklist.report_landscape', 'sale.order',
    'addons/max_custom_report/sale/report/allocated_sale_order_checklist_report.rml', parser=allocated_sale_order_checklist_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
