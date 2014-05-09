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

class po_oustanding_report(report_sxw.rml_parse):
    _name = 'po.oustanding.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        purchase_order_obj = self.pool.get('purchase.order')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        qry_po = ''
        val_po = []
        
        partner_ids = False
        po_ids = False
        
        data_search = data['form']['supplier_search_vals']
        
        if data['form']['supp_selection'] == 'all':
            qry_supp = 'supplier = True'
            val_part.append(('supplier', '=', True))
        elif data['form']['supp_selection'] == 'supplier':
            qry_supp = 'supplier = True and sundry = False'
            val_part.append(('supplier', '=', True))
            val_part.append(('sundry', '=', False))
        elif data['form']['supp_selection'] == 'sundry':
            qry_supp = 'supplier = True and sundry = True'
            val_part.append(('supplier', '=', True))
            val_part.append(('sundry', '=', True))
        
        partner_default_from = data['form']['partner_default_from'] and data['form']['partner_default_from'][0] or False
        partner_default_to = data['form']['partner_default_to'] and data['form']['partner_default_to'][0] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False
        
        if data_search == 'code':
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref:
                    data_found = True
                    val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref:
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))
                #print val_part
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        elif data_search == 'name':
            if data['form']['filter_selection'] == 'all_vall':
                self.partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).name:
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).name:
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).name))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        self.partner_ids = partner_ids
        
        #Period

        if data['form']['date_selection'] == 'none_sel':
            self.date_from = False
            self.date_to = False
        else:
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#purchase order
        qry_po = 'state = "approved"'
        val_po.append(('state','=', 'approved'))

        po_default_from = data['form']['po_default_from'] and data['form']['po_default_from'][0] or False
        po_default_to = data['form']['po_default_to'] and data['form']['po_default_to'][0] or False
        po_input_from = data['form']['po_input_from'] or False
        po_input_to = data['form']['po_input_to'] or False

        if data['form']['po_selection'] == 'all_vall':
            po_ids = purchase_order_obj.search(self.cr, self.uid, val_po, order='name ASC')

        if data['form']['po_selection'] == 'name':
            data_found = False
            if po_default_from and purchase_order_obj.browse(self.cr, self.uid, po_default_from) and purchase_order_obj.browse(self.cr, self.uid, po_default_from).name:
                data_found = True
                val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_default_from).name))
            if po_default_to and purchase_order_obj.browse(self.cr, self.uid, po_default_to) and purchase_order_obj.browse(self.cr, self.uid, po_default_to).name:
                data_found = True
                val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_default_to).name))
            if data_found:
                po_ids = purchase_order_obj.search(self.cr, self.uid, val_po, order='name ASC')
        elif data['form']['po_selection'] == 'input':
            data_found = False
            if po_input_from:
                self.cr.execute("select name " \
                                "from purchase_order "\
                                "where " + qry_po + " and " \
                                "name ilike '" + str(po_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_po.append(('name', '>=', qry['name']))
            if po_input_to:
                self.cr.execute("select name " \
                                "from purchase_order "\
                                "where " + qry_po + " and " \
                                "name ilike '" + str(po_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_po.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                po_ids = purchase_order_obj.search(self.cr, self.uid, val_po, order='name ASC')
        elif data['form']['po_selection'] == 'selection':
            if data['form']['po_ids']:
                po_ids = data['form']['po_ids']
        self.po_ids = po_ids

        #print self.period_ids
        return super(po_oustanding_report, self).set_context(objects, data, new_ids, report_type=report_type)

#    def set_context(self, objects, data, ids, report_type=None):
#        new_ids = ids
#        res = {}
#        self.date_from = data['form']['date_from']
#        self.date_to = data['form']['date_to']
#        self.partner_code_from = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
#        self.partner_code_to = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
#        self.po_from = data['form']['po_from'] and data['form']['po_from'][0] or False
#        self.po_to = data['form']['po_to'] and data['form']['po_to'][0] or False
#
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
#        return super(po_oustanding_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(po_oustanding_report, self).__init__(cr, uid, name, context=context)
        
        self.oustanding = 0.00
        
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'total_oustanding': self._total_oustanding,
            })

    def _total_oustanding(self):
        return self.oustanding

    def _get_lines(self):
        results = []
        # partner
        cr              = self.cr
        uid             = self.uid
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        pol_obj = self.pool.get('purchase.order.line')
        partner_ids = self.partner_ids or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND po.partner_id = " + str(partner_ids[0]) + " ") or "AND po.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND po.partner_id IN (0) "

        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And po.date_order >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And po.date_order <= '" + str(date_to) + "' " or " "

        po_ids = self.po_ids or False
        po_qry = (po_ids and ((len(po_ids) == 1 and "AND po.id = " + str(po_ids[0]) + " ") or "AND po.id IN " + str(tuple(po_ids)) + " ")) or "AND po.id IN (0) "
        
        cr.execute(
            "SELECT pol.id as line_id, pt.name as prod_name, po.name as po_name, rp.name as rp_name, rp.ref as rp_ref, " \
            "(pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) as oustanding " \
            "FROM purchase_order_line pol " \
            "LEFT JOIN purchase_order po on pol.order_id = po.id " \
            "LEFT JOIN res_partner rp on po.partner_id = rp.id " \
            "LEFT JOIN product_template pt on pol.product_id = pt.id " \
            "WHERE po.state IN ('approved') " \
            "And (pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) > 0 " \
            + partner_qry \
            + date_from_qry \
            + date_to_qry \
            + po_qry + \
            "order by po.date_order")
        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                pol = pol_obj.browse(self.cr, self.uid, t['line_id'])
                
#                if pol.oustanding_qty > 0:
#                partner_name = ''
#
#                if pol.order_id:
#                    partner_name = pol.order_id.partner_id and pol.order_id.partner_id.name or ''
#                if partner_name: partner_name = partner_name.replace('&','&amp;')
#
                res = {
                    's_name' : t['rp_name'] or '',
                    's_ref' : t['rp_ref'] or '',
                    'order_name' : t['po_name'] or '',
                    'part_name' : t['prod_name'] or '',
                    'etd' : pol.estimated_time_departure or False,
                    'order_qty' : pol.product_qty or '',
                    'unit_price': pol.price_unit,
                    'oustanding': t['oustanding'] or 0,
                }
                self.oustanding += (t['oustanding'] or 0)
                results.append(res)
        return results
#    def _get_code_from(self):
#        return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
#    
#    def _get_code_to(self):
#        return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
#    
#    def _get_po_from(self):
#        return self.po_from and self.pool.get('purchase.order').browse(self.cr, self.uid, self.po_from).name or False
#    
#    def _get_po_to(self):
#        return self.po_to and self.pool.get('purchase.order').browse(self.cr, self.uid, self.po_to).name or False
####        
#
#    def _get_lines(self):
#        results = []
#        val_part = []
#        val_po = []
#        date_from = self.date_from
#        date_to =  self.date_to + ' ' + '23:59:59'
#        code_from = self.partner_code_from
#        code_to = self.partner_code_to
#        po_from = self.po_from
#        po_to = self.po_to
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(code_from, code_to))
#
#        purchase_order_line_obj = self.pool.get('purchase.order.line')
#        purchase_order_obj = self.pool.get('purchase.order')
#        res_partner_obj = self.pool.get('res.partner')
#        
#        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
#            val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_from).name))
#        if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
#            val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_to).name))
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(vals, code_to))
#
#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part)
#        po_ids = purchase_order_obj.search(self.cr, self.uid, val_po)
#        line_ids = purchase_order_line_obj.search(self.cr, self.uid, [])
#        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)
#
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
#                self.oustanding += (pur.oustanding_qty or '')
#                
#                results.append(res)
#                res = {}
#        return results 
#    
#    def _total_oustanding(self):
#        return self.oustanding
    
report_sxw.report_sxw('report.po.oustanding.report_landscape', 'purchase.order',
    'addons/max_custom_report/purchase/report/po_oustanding_report.rml', parser=po_oustanding_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
