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

class incoming_report(report_sxw.rml_parse):
    _name = 'incoming.report'

    def set_context(self, objects, data, ids, report_type=None):
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
        
        if data['form']['date_selection'] == 'none_sel':
            self.date_from = False
            self.date_to = False
        else:
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        pp_default_from = data['form']['product_default_from'] and data['form']['product_default_from'][0] or False
        pp_default_to = data['form']['product_default_to'] and data['form']['product_default_to'][0] or False
        pp_input_from = data['form']['product_input_from'] or False
        pp_input_to = data['form']['product_input_to'] or False

        if data['form']['product_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')

        if data['form']['product_selection'] == 'def':
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

        if data['form']['sl_selection'] == 'def':
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
                sl_ids = stock_location_obj.search(self.cr, self.uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'selection':
            if data['form']['sl_ids']:
                sl_ids = data['form']['sl_ids']
        self.sl_ids = sl_ids
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(incoming_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(incoming_report, self).__init__(cr, uid, name, context=context)
        self.total_cost = 0.00
        self.total_qty = 0.00
#      
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
#            'total_cost' : self._total_cost,
#            'total_qty' : self._total_qty,
#            'product_from': self._get_product_from,
#            'product_to': self._get_product_to,
#            'location_from': self._get_location_from,
#            'location_to': self._get_location_to,
            })

    def _get_lines(self):
        results = []
        cr = self.cr
        uid = self.uid
        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And sp.date_done >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And sp.date_done <= '" + str(date_to) + "' " or " "
        pp_ids = self.pp_ids or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND pt.id = " + str(pp_ids[0]) + " ") or "AND pt.id IN " + str(tuple(pp_ids)) + " ")) or "AND pt.id IN (0) "
        sl_ids = self.sl_ids or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sl.id = " + str(sl_ids[0]) + " ") or "AND sl.id IN " + str(tuple(sl_ids)) + " ")) or "AND sl.id IN (0) "
        res_lines = []
        cr.execute("select sp.do_date as date, " \
                        "sp.name as inc_no, " \
                        "pt.name as spn, " \
                        "rp.name as sn, " \
                        "sp.invoice_no as in, " \
                        "sm.product_qty as qty, " \
                        "po.name as po, " \
                        "sl.name as location, "\
                        "sm.id as sm_id " \
                        "from stock_move sm " \
                        "inner join stock_picking sp on sp.id = sm.picking_id " \
                        "left join stock_location sl on sm.location_dest_id = sl.id " \
                        "left join res_partner rp on sp.partner_id = rp.id " \
                        "left join product_template pt on sm.product_id = pt.id " \
                        "inner join purchase_order_line pol on sm.purchase_line_id = pol.id " \
                        "left join purchase_order po on pol.order_id=po.id " \
                        "WHERE sm.state = 'done' and sp.state = 'done' and sp.type = 'in' " \
                        + date_from_qry \
                        + date_to_qry \
                        + pp_qry \
                        + sl_qry + \
                        " order by spn, inc_no, date")
        qry = cr.dictfetchall()
        print cr
        if qry:
            for s in qry:
                    results.append({
                                    'date' : s['date'],
                                    'inc_no' : s['inc_no'],
                                    'spn' : s['spn'],
                                    'sn' : s['sn'],
                                    'in': s['in'],
                                    'qty' : s['qty'],
                                    'po' : s['po'],
                                    'location': s['location'],
                                    'sm_id' : s['sm_id'],
                                     })
#        results = results and sorted(results, key=lambda val_res: val_res['spn']) or []
#        results = results and sorted(results, key=lambda val_res: val_res['inc_no']) or []
#        results = results and sorted(results, key=lambda val_res: val_res['date']) or []
        return results


#    def _get_product_from(self):
#           return self.product_from and self.pool.get('product.product').browse(self.cr, self.uid, self.product_from).name or False
#    
#    def _get_product_to(self):
#        return self.product_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_to).name or False
#    
#    def _get_location_from(self):
#        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_from).name or False
#    
#    def _get_location_to(self):
#        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_to).nameor or False
##        
#    def _get_lines(self):
#        
#        results = []
#        val_product = []
#        val_location = []
##        date_from = self.date_from
##        date_to = self.date_to + ' ' + '23:59:59'
#
##        location_from = self.location_from
##        location_to = self.location_to
#        res_temp1 = []
#        res_temp2 = []
#        res_temp3 = []
#        res_temp4 = []
#        dest_loc_group = {}
#        product_group = {}
#        inc_group = {}
#        date_group = {}
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(code_from, code_to))
#
#        product_product_obj = self.pool.get('product.product')
#        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
#        stock_location_obj = self.pool.get('stock.location')
#        stock_move_obj = self.pool.get('stock.move')
#        uom_obj = self.pool.get('product.uom')
##        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
##            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
##        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
##            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))
##        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
##            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
##        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
##            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))
#
##        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
##            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
##        if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
##            val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_from).name))
##        if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
##            val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_to).name))
#        
##        part_ids = res_partner_obj.search(self.cr, self.uid, val_part)
#        product_ids = self.pp_ids
##        print product_ids
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %('', ''))
#
##        product_ids = product_product_obj.search(self.cr, self.uid, val_product, order='name')
##        location_ids = stock_location_obj.search(self.cr, self.uid, val_location)
##        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)
#        for product_id in product_ids:
#            pp = product_product_obj.browse(self.cr, self.uid, product_id)
##            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(pp.id, pp.name))
#            stock_move_ids = stock_move_obj.search(self.cr, self.uid, [('product_id', '=', product_id), ('state', '=', 'done')])
##            print stock_move_ids
##            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %('', ''))
#
#            if stock_move_ids:
#                for stock_move_id in stock_move_ids:
#                    sm = stock_move_obj.browse(self.cr, self.uid, stock_move_id)
#                    if sm.picking_id and sm.picking_id.type == 'in':
#                        qty = uom_obj._compute_qty(self.cr, self.uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
#                        res_temp1.append({
#                                        'date' : sm.picking_id.date_done,
#                                        'inc_no' : sm.picking_id.name or '',
#                                        'spn' : sm.product_id.name or '',
#                                        'sn' : sm.picking_id.partner_id and sm.picking_id.partner_id.name or '',
#                                        'in': sm.picking_id.invoice_no or '',
#                                        'qty' : qty or 0.00,
#                                        'po' : sm.purchase_line_id and sm.purchase_line_id.order_id and sm.purchase_line_id.order_id.name or '',
#                                        'location': sm.location_dest_id.name or '',
#                                        'sm_id' : sm.id,
#                                         }
#                                        )
#                        #sort by loc
#                        dest_loc_group[sm.id] = sm.location_dest_id.name
#
#        if res_temp1:
#            for key, value in sorted(dest_loc_group.iteritems(), key=lambda (k, v): (v, k)):
##                for key, value in sorted(customer_group.iteritems(), key=lambda (k,v): (v,k)):
#                for temp in res_temp1:
#                    if temp['sm_id'] == key:
#                        #sort by product
#                        product_group[temp['sm_id']] = temp['spn']
#                        res_temp2.append({
#                                        'date' : temp['date'],
#                                        'inc_no' : temp['inc_no'],
#                                        'spn' : temp['spn'],
#                                        'sn' : temp['sn'],
#                                        'in': temp['in'],
#                                        'qty' : temp['qty'],
#                                        'po' : temp['po'],
#                                        'location': temp['location'],
#                                        'sm_id' : temp['sm_id'],
#                                        })
#
#        if res_temp2:
#            for key, value in sorted(product_group.iteritems(), key=lambda (k, v): (v, k)):
##                for key, value in sorted(customer_group.iteritems(), key=lambda (k,v): (v,k)):
#                for temp in res_temp2:
#                    if temp['sm_id'] == key:
#                        #sort by inc
#                        inc_group[temp['sm_id']] = temp['inc_no']
#                        res_temp3.append({
#                                        'date' : temp['date'],
#                                        'inc_no' : temp['inc_no'],
#                                        'spn' : temp['spn'],
#                                        'sn' : temp['sn'],
#                                        'in': temp['in'],
#                                        'qty' : temp['qty'],
#                                        'po' : temp['po'],
#                                        'location': temp['location'],
#                                        'sm_id' : temp['sm_id'],
#                                        })
#
#        if res_temp3:
#            for key, value in sorted(inc_group.iteritems(), key=lambda (k, v): (v, k)):
##                for key, value in sorted(customer_group.iteritems(), key=lambda (k,v): (v,k)):
#                for temp in res_temp3:
#                    if temp['sm_id'] == key:
#                        #sort by date
#                        date_group[temp['sm_id']] = temp['date']
#                        res_temp4.append({
#                                                                    'date' : temp['date'],
#                                        'inc_no' : temp['inc_no'],
#                                        'spn' : temp['spn'],
#                                        'sn' : temp['sn'],
#                                        'in': temp['in'],
#                                        'qty' : temp['qty'],
#                                        'po' : temp['po'],
#                                        'location': temp['location'],
#                                        'sm_id' : temp['sm_id'],
#                                        })
#
#        if res_temp4:
#            for key, value in sorted(date_group.iteritems(), key=lambda (k, v): (v, k)):
#                for temp in res_temp4:
#                    if temp['sm_id'] == key:
#                        res = {
#                            'date' : temp['date'],
#                            'inc_no' : temp['inc_no'],
#                            'spn' : temp['spn'],
#                            'sn' : temp['sn'],
#                            'in': temp['in'],
#                            'qty' : temp['qty'],
#                            'po' : temp['po'],
#                            'location': temp['location'],
#                        }
#                        results.append(res)
#                        res = {}
#        print 'test'
#        return results 
#
#    def _total_cost(self):
#        return self.total_cost
#    
#    def _total_qty(self):
#        return self.total_qty
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
        
report_sxw.report_sxw('report.incoming.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/incoming_report.rml', parser=incoming_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
