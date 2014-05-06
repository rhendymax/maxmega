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
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.brand_from = data['form']['brand_from'] and data['form']['brand_from'][0] or False
        self.brand_to = data['form']['brand_to'] and data['form']['brand_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(monthly_pos_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(monthly_pos_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_brand_from': self._get_brand_from,
            'get_brand_to': self._get_brand_to,
            })

    def _get_brand_from(self):
        return self.brand_from and self.pool.get('product.brand').browse(self.cr, self.uid, self.brand_from).name or False
    
    def _get_brand_to(self):
        return self.brand_to and self.pool.get('product.brand').browse(self.cr, self.uid, self.brand_to).name or False

    def _get_lines(self):
        results = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        brand_from = self.brand_from
        brand_to = self.brand_to
        val_brand = []
        product_brand_obj = self.pool.get('product.brand')
        if brand_from and product_brand_obj.browse(self.cr, self.uid, brand_from) and product_brand_obj.browse(self.cr, self.uid, brand_from).name:
            val_brand.append(('name', '>=', product_brand_obj.browse(self.cr, self.uid, brand_from).name))
        if brand_to and product_brand_obj.browse(self.cr, self.uid, brand_to) and product_brand_obj.browse(self.cr, self.uid, brand_to).name:
            val_brand.append(('name', '<=', product_brand_obj.browse(self.cr, self.uid, brand_to).name))
        brand_ids = product_brand_obj.search(self.cr, self.uid, val_brand, order='name ASC')
        val_ss = ''
        if brand_ids:
            for ss in brand_ids:
                if val_ss == '':
                    val_ss += str(ss)
                else:
                    val_ss += (', ' + str(ss))

        self.cr.execute("select rp.id as cust_id, " \
                        "rp.ref as cust_ref, " \
                        "rp.name as cust_name " \
                        "from account_invoice ai " \
                        "inner join account_invoice_line ail on ai.id = ail.invoice_id  " \
                        "left join res_partner rp on ai.partner_id = rp.id " \
                        "left join product_template pt on ail.product_id = pt.id " \
                        "left join product_product pp on ail.product_id = pp.id " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "left join stock_move sm on ail.stock_move_id = sm.id " \
                        "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null  " \
                        "and ai.date_invoice >= '" + str(date_from) + "' AND ai.date_invoice <= '" + str(date_to) + "' " \
                        "and pp.brand_id in (" + val_ss + ") " \
                        "group by cust_name, cust_ref, cust_id " \
                        "order by cust_name, cust_ref, cust_id")
#
#        self.cr.execute("select rp.ref as cust_ref, " \
#                        "rp.name as cust_name, " \
#                        "rp.id as cust_id, " \
#                        "pb.id as brand_id, " \
#                        "pb.name as brand_name, " \
#                        "pc.name as product_customer_name, " \
#                        "pt.name as inventory_key, " \
#                        "ail.price_unit as selling_price, " \
#                        "ail.quantity as quantity, " \
#                        "ail.price_unit * ail.quantity as total, " \
#                        "ai.date_invoice as date_inv " \
#                        "from account_invoice ai " \
#                        "inner join account_invoice_line ail on ai.id = ail.invoice_id " \
#                        "left join res_partner rp on ai.partner_id = rp.id " \
#                        "left join product_template pt on ail.product_id = pt.id " \
#                        "left join product_product pp on ail.product_id = pp.id " \
#                        "left join product_brand pb on pp.brand_id = pb.id " \
#                        "left join stock_move sm on ail.stock_move_id = sm.id " \
#                        "left join sale_order_line sol on sm.sale_line_id = sol.id " \
#                        "left join product_customer pc on sol.product_customer_id = pc.id " \
#                        "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null " \
#                        "and ai.date_invoice >= '" + str(date_from) + "' AND ai.date_invoice <= '" + str(date_to) + "' " \
#                        "and pp.brand_id in (" + val_ss + ") "
#                        "order by rp.name, rp.id, pb.name, pb.id, ai.date_invoice")
        res_general = self.cr.dictfetchall()
        for val in res_general:
            res = {}
            res['cust_name'] = '[' + val['cust_ref'] + '] ' + val['cust_name']
            self.cr.execute("select pb.name as brand_name,  " \
                        "pb.id as brand_id  " \
                        "from account_invoice ai  " \
                        "inner join account_invoice_line ail on ai.id = ail.invoice_id " \
                        "left join res_partner rp on ai.partner_id = rp.id " \
                        "left join product_template pt on ail.product_id = pt.id " \
                        "left join product_product pp on ail.product_id = pp.id  " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "left join stock_move sm on ail.stock_move_id = sm.id " \
                        "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null " \
                        "and ai.date_invoice >= '" + str(date_from) + "' AND ai.date_invoice <= '" + str(date_to) + "' " \
                        "and pp.brand_id in (" + val_ss + ") " \
                        "and ai.partner_id = " + str(val['cust_id']) + " " \
                        "group by pb.name, pb.id " \
                        "order by pb.name, pb.id")
            res_brand = self.cr.dictfetchall()
            brand_ids = []
            for val_b in res_brand:
                self.cr.execute("select pc.name as product_customer_name, " \
                                "pt.name as inventory_key, " \
                                "ail.price_unit as selling_price, " \
                                "ail.quantity as quantity, " \
                                "ail.price_unit * ail.quantity as total, " \
                                "ai.date_invoice as date_inv " \
                                "from account_invoice ai " \
                                "inner join account_invoice_line ail on ai.id = ail.invoice_id " \
                                "left join res_partner rp on ai.partner_id = rp.id " \
                                "left join product_template pt on ail.product_id = pt.id " \
                                "left join product_product pp on ail.product_id = pp.id " \
                                "left join product_brand pb on pp.brand_id = pb.id " \
                                "left join stock_move sm on ail.stock_move_id = sm.id " \
                                "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                                "left join product_customer pc on sol.product_customer_id = pc.id " \
                                "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null " \
                                "and ai.date_invoice >= '" + str(date_from) + "' AND ai.date_invoice <= '" + str(date_to) + "' " \
                                "and pp.brand_id in (" + val_ss + ") "
                                "and ai.partner_id = " + str(val['cust_id']) + " " \
                                "and pb.id = " + str(val_b['brand_id']) + " " \
                                "order by rp.name, rp.id, pb.name, pb.id, ai.date_invoice")
                res_lines = self.cr.dictfetchall()
                lines = []
                qty = 0
                total = 0
                for val_lines in res_lines:
                    lines.append({
                        'cust_name' : val['cust_name'],
                        'cust_part_no' : val_lines['product_customer_name'],
                        'inv_key': val_lines['inventory_key'],
                        'selling_price': val_lines['selling_price'],
                        'quantity': val_lines['quantity'],
                        'total': val_lines['total'],
                        'brand': val_b['brand_name'],
                        'date_inv': val_lines['date_inv'],
                        })
                    qty += val_lines['quantity']
                    total += val_lines['total']
                brand_ids.append({
                    'brand_name' : val_b['brand_name'],
                    'brand_lines' : lines,
                    'qty' : qty,
                    'total': total,
                    })
                
            res['lines'] = brand_ids
            results.append(res)
        return results

report_sxw.report_sxw('report.monthly.pos.report_landscape', 'account.invoice',
    'addons/max_custom_report/product/report/monthly_pos_report.rml', parser=monthly_pos_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
