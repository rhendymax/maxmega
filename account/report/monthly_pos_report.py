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
from tools import float_round, float_is_zero, float_compare

class monthly_pos_report(report_sxw.rml_parse):
    _name = 'monthly.pos.report'

    def set_context(self, objects, data, ids, report_type=None):
                new_ids = ids
                res = {}
                product_brand_obj = self.pool.get('product.brand')
                qry_supp = ''
                val_part = []
                qry_pb = ''
                val_pb = []
                
                partner_ids = False
                brand_ids = False
                #Date
                if data['form']['date_selection'] == 'none_sel':
                    self.date_from = False
                    self.date_to = False
                else:
                    self.date_from = data['form']['date_from']
                    self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'
        
        #Inventory Brand
                brand_default_from = data['form']['brand_default_from'] and data['form']['brand_default_from'][0] or False
                brand_default_to = data['form']['brand_default_to'] and data['form']['brand_default_to'][0] or False
                brand_input_from = data['form']['brand_input_from'] or False
                brand_input_to = data['form']['brand_input_to'] or False
        
                if data['form']['brand_selection'] == 'all_vall':
                    brand_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
                if data['form']['brand_selection'] == 'name':
                    data_found = False
                    if brand_default_from and product_brand_obj.browse(self.cr, self.uid, brand_default_from) and product_brand_obj.browse(self.cr, self.uid, brand_default_from).name:
                        data_found = True
                        val_pb.append(('name', '>=', product_brand_obj.browse(self.cr, self.uid, brand_default_from).name))
                    if brand_default_to and product_brand_obj.browse(self.cr, self.uid, brand_default_to) and product_brand_obj.browse(self.cr, self.uid, brand_default_to).name:
                        data_found = True
                        val_pb.append(('name', '<=', product_brand_obj.browse(self.cr, self.uid, brand_default_to).name))
                    if data_found:
                        brand_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
                elif data['form']['brand_selection'] == 'input':
                    data_found = False
                    if brand_input_from:
                        self.cr.execute("select name " \
                                        "from product_brand "\
                                        "where " + qry_pb + " and " \
                                        "name ilike '" + str(brand_input_from) + "%' " \
                                        "order by name limit 1")
                        qry = self.cr.dictfetchone()
                        if qry:
                            data_found = True
                            val_pb.append(('name', '>=', qry['name']))
                    if brand_input_to:
                        self.cr.execute("select name " \
                                        "from product_brand "\
                                        "where " + qry_pb + " and " \
                                        "name ilike '" + str(brand_input_to) + "%' " \
                                        "order by name desc limit 1")
                        qry = self.cr.dictfetchone()
                        if qry:
                            data_found = True
                            val_pb.append(('name', '<=', qry['name']))
                    #print val_part
                    if data_found:
                        brand_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
                elif data['form']['brand_selection'] == 'selection':
                    if data['form']['brand_ids']:
                        brand_ids = data['form']['brand_ids']
                self.brand_ids = brand_ids
        
                #print self.period_ids
                return super(monthly_pos_report, self).set_context(objects, data, new_ids, report_type=report_type)


    def __init__(self, cr, uid, name, context=None):
        super(monthly_pos_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            })

    def _get_lines(self):
        results = []
        # partner
        cr              = self.cr
        uid             = self.uid
        
        
        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And l.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date_invoice <= '" + str(date_to) + "' " or " "

        brand_ids = self.brand_ids or False
        brand_qry = (brand_ids and ((len(brand_ids) == 1 and "AND pp.brand_id = " + str(brand_ids[0]) + " ") or "AND pp.brand_id IN " + str(tuple(brand_ids)) + " ")) or "AND pp.brand_id IN (0) "

        cr.execute("select  DISTINCT l.partner_id " \
                        "from account_invoice l " \
                        "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
                        "left join product_product pp on ail.product_id = pp.id  " \
                        "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                        + date_from_qry \
                        + date_to_qry \
                        + brand_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name, ref " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                brand_ids = []
                qty = total = 0
                cr.execute("select DISTINCT pp.brand_id " \
                                "from account_invoice l " \
                                "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
                                "left join product_product pp on ail.product_id = pp.id  " \
                                "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                                + date_from_qry \
                                + date_to_qry \
                                + brand_qry + \
                                "and l.partner_id = " + str(s['id']) + " "\
                                )
                brand_ids_vals = []
                qry_brand1 = cr.dictfetchall()
                if qry_brand1:
                    for brand_r in qry_brand1:
                        brand_ids_vals.append(brand_r['brand_id'])
                brand_ids_vals_qry = (len(brand_ids_vals) > 0 and ((len(brand_ids_vals) == 1 and "where id = " +  str(brand_ids_vals[0]) + " ") or "where id IN " +  str(tuple(brand_ids_vals)) + " ")) or "where id IN (0) "
                cr.execute(
                        "SELECT id, name " \
                        "FROM product_brand " \
                        + brand_ids_vals_qry \
                        + " order by name")
                qry_brand2 = cr.dictfetchall()
                for brand_s in qry_brand2:

                    cr.execute("select pc.name as cpn, " \
                                "pt.name as inv_key, " \
                                "ail.price_unit as selling_price, " \
                                "ail.quantity as quantity, " \
                                "ail.price_unit * ail.quantity as total, " \
                                "l.date_invoice as date_inv " \
                                "from account_invoice l " \
                                "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
                                "left join product_product pp on ail.product_id = pp.id  " \
                                "left join product_template pt on ail.product_id = pt.id  " \
                                "left join stock_move sm on ail.stock_move_id = sm.id " \
                                "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                                "left join product_customer pc on sol.product_customer_id = pc.id " \
                                "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                                + date_from_qry \
                                + date_to_qry + \
                                "and l.partner_id = " + str(s['id']) + " "\
                                "and pp.brand_id = " + str(brand_s['id']) + " "\
                                "order by l.date_invoice"
                                )
                    qry3 = cr.dictfetchall()

                    brand_lines = []
                    brand_qty = brand_total = 0
                    if qry3:
                        for t in qry3:
                            brand_lines.append({
                                                'cpn' : t['cpn'],
                                                'inv_key': t['inv_key'],
                                                'selling_price': t['selling_price'],
                                                'quantity': t['quantity'],
                                                'total': t['total'],
                                                'brand':brand_s['name'],
                                                'date_inv': t['date_inv'],
                                                })
                            brand_qty += t['quantity']
                            brand_total += t['total']
                    brand_ids.append({
                                      'brand_name' : brand_s['name'],
                                      'qty' : brand_qty,
                                      'total' : brand_total,
                                      'lines': brand_lines,
                                      })
                    qty += brand_qty
                    total += brand_total
                results.append({
                        'part_name' : s['name'],
                        'part_ref' : s['ref'],
                        'brand_ids': brand_ids,
                        'qty' : qty,
                        'total' : total,
                                })

        results = results and sorted(results, key=lambda val_res: val_res['part_name']) or []

        return results

report_sxw.report_sxw('report.monthly.pos.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/monthly_pos_report.rml', parser=monthly_pos_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
