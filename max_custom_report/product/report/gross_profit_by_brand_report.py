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

class gross_profit_by_brand_report(report_sxw.rml_parse):
    _name = 'gross.profit.by.brand.report'

    def set_context(self, objects, data, ids, report_type=None):
#        new_ids = ids
#        res = {}
#        self.date_from = data['form']['date_from']
#        self.date_to = data['form']['date_to']
#        self.brand_from = data['form']['brand_from'] and data['form']['brand_from'][0] or False
#        self.brand_to = data['form']['brand_to'] and data['form']['brand_to'][0] or False

        new_ids = ids
        res = {}
        product_brand_obj = self.pool.get('product.brand')
        val_pb = []
        
        if data['form']['date_selection'] == 'none_sel':
            self.date_from = False
            self.date_to = False
        else:
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        pb_default_from = data['form']['pb_default_from'] and data['form']['pb_default_from'][0] or False
        pb_default_to = data['form']['pb_default_to'] and data['form']['pb_default_to'][0] or False
        pb_input_from = data['form']['pb_input_from'] or False
        pb_input_to = data['form']['pb_input_to'] or False
        
        if data['form']['pb_selection'] == 'all_vall':
            pb_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
        if data['form']['pb_selection'] == 'def':
            data_found = False
            if pb_default_from and product_brand_obj.browse(self.cr, self.uid, pb_default_from) and product_brand_obj.browse(self.cr, self.uid, pb_default_from).name:
                data_found = True
                val_pb.append(('name', '>=', product_brand_obj.browse(self.cr, self.uid, pb_default_from).name))
            if pb_default_to and product_brand_obj.browse(self.cr, self.uid, pb_default_to) and product_brand_obj.browse(self.cr, self.uid, pb_default_to).name:
                data_found = True
                val_pb.append(('name', '<=', product_brand_obj.browse(self.cr, self.uid, pb_default_to).name))
            if data_found:
                pb_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'input':
            data_found = False
            if pb_input_from:
                self.cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(pb_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if pb_input_to:
                self.cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(pb_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                pb_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'selection':
            if data['form']['pb_ids']:
                pb_ids = data['form']['pb_ids']
        self.pb_ids = pb_ids

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(gross_profit_by_brand_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(gross_profit_by_brand_report, self).__init__(cr, uid, name, context=context)
        self.qty = 0.00
        self.sales = 0.00
        self.cost = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
#            'get_brand_from': self._get_brand_from,
#            'get_brand_to': self._get_brand_to,
            'total_qty' : self._total_qty,
            'total_sales' : self._total_sales,
            'total_cost' : self._total_cost,
            })

    def _total_qty(self):
        return self.qty

    def _total_sales(self):
        return self.sales

    def _total_cost(self):
        return self.cost

    def _get_lines(self):
        results = []
        cr = self.cr
        uid = self.uid
        product_product_obj = self.pool.get('product.product')
        res_company_obj = self.pool.get('res.company')
        currency_pool = self.pool.get('res.currency')
        pb_ids = self.pb_ids or False

        date_from = self.date_from
        date_to = self.date_to

        pb_qry = (pb_ids and ((len(pb_ids) == 1 and "AND pb.id = " + str(pb_ids[0]) + " ") or "AND pb.id IN " + str(tuple(pb_ids)) + " ")) or "AND pb.id IN (0) "

        date_from_qry = date_from and "AND ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "AND ai.date_invoice <= '" + str(date_to) + "' " or " "

        cr.execute("SELECT pb.id as brand_id \
        from account_invoice_line ail \
        inner join account_invoice ai on ail.invoice_id = ai.id \
        inner join product_product pp on ail.product_id = pp.id \
        inner join product_brand pb on pp.brand_id= pb.id \
        WHERE ai.state in ('open', 'paid') AND ai.type = 'out_invoice' "\
        + pb_qry \
        + date_from_qry \
        + date_to_qry  +\
        "order by pb.name")

        brnd_ids = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                brnd_ids.append(r['brand_id'])

        brnd_ids_vals_qry = (len(brnd_ids) > 0 and ((len(brnd_ids) == 1 and "where id = " +  str(brnd_ids[0]) + " ") or "where id IN " +  str(tuple(brnd_ids)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name, description " \
                "FROM product_brand " \
                + brnd_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        
        if qry:
            for s in qry:
                cr.execute("SELECT pb.id as brand_id, \
                ail.quantity as brand_qty, ail.uos_id as brand_uom, ail.price_unit as brand_price, \
                ail.product_id as product_id, ai.currency_id as currency_id, ail.company_id as company_id, \
                ai.cur_date as cur_date, ail.stock_move_id as stock_move_id \
                from account_invoice_line ail \
                inner join account_invoice ai on ail.invoice_id = ai.id \
                inner join product_product pp on ail.product_id = pp.id \
                inner join product_brand pb on pp.brand_id= pb.id \
                WHERE ai.state in ('open', 'paid') AND ai.type = 'out_invoice' " + \
                "and pb.id = " + str(s['id']) \
                + pb_qry \
                + date_from_qry \
                + date_to_qry  +\
                "order by pb.name")

                brand_qty = brand_price = brand_cost = gross_profit = gross_profit_p = 0
                qry3 = cr.dictfetchall()
                if qry3:
                    for t in qry3:
                        product_id = product_product_obj.browse(self.cr, self.uid, t['product_id'])
                        company_currency = res_company_obj.browse(self.cr, self.uid, t['company_id']).currency_id.id
                        if t['currency_id'] == company_currency:
                            price_unit = t['brand_price']
                        else:
                            ctx = {}
                            ctx.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
                            ctx2 = {}
                            ctx2.update({'date': t['cur_date']})
                            rate_inv = currency_pool.browse(self.cr, self.uid, t['currency_id'], context=ctx2).rate
                            rate_home = currency_pool.browse(self.cr, self.uid, company_currency, context=ctx).rate
                            price_unit = t['brand_price'] * rate_home / rate_inv

                        brand_qty += t['brand_qty']
                        brand_price += float_round(price_unit * t['brand_qty'],5)
                        cr.execute("select SUM(COALESCE(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
                                round(CAST(sm_in.price_unit as numeric), 5) * fc.quantity \
                                ELSE round(CAST(sm_in.price_unit / \
                                (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
                                * fc.quantity END,0)) AS test \
                                from fifo_control fc \
                                left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
                                left join stock_move sm_out on fc.out_move_id = sm_out.id \
                                left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
                                left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
                                left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
                                left join res_company rc on sm_out.company_id = rc.id \
                                where (fc.out_move_id in (" + str(t['stock_move_id']) + "))")
                        res_val = cr.dictfetchall()
                        for res_val1 in res_val:
                            brand_cost += res_val1['test']
                gross_profit = brand_price - brand_cost
                if brand_price > 0:
                    gross_profit_p = gross_profit / brand_price * 100
                self.cost += (brand_cost or 0)
                self.qty += (brand_qty or 0)
                self.sales += (brand_price or 0)
                results.append({
                    'brand_name' : s['name'],
                    'description' : s['description'],
                    'brand_qty' : brand_qty,
                    'brand_sales' : brand_price,
                    'brand_cost' : brand_cost,
                    'gross_profit' : gross_profit,
                    'gross_profit_p' : gross_profit_p,
                })



        
#         res_general = self.cr.dictfetchall()
#         sm_ids = []
#         brand_id = False
#         for r in res_general:
#             product_id = product_product_obj.browse(self.cr, self.uid, r['product_id'])
#             company_currency = res_company_obj.browse(self.cr, self.uid, r['company_id']).currency_id.id
#             if r['currency_id'] == company_currency:
#                 price_unit = r['brand_price']
#             else:
#                 ctx = {}
#                 ctx.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
#                 ctx2 = {}
#                 ctx2.update({'date': r['cur_date']})
#                 rate_inv = currency_pool.browse(self.cr, self.uid, r['currency_id'], context=ctx2).rate
#                 rate_home = currency_pool.browse(self.cr, self.uid, company_currency, context=ctx).rate
#                 price_unit = r['brand_price'] * rate_home / rate_inv
#             if r['brand_id'] not in brnd_ids:
#                 brnd_ids.append(r['brand_id'])
#                 brnd_ids_qty[r['brand_id']] = r['brand_qty']
#                 brnd_ids_sales[r['brand_id']] = float_round(price_unit * r['brand_qty'],5)
#                 brnd_ids_name[r['brand_id']] = r['brand_name']
#                 brnd_ids_desc[r['brand_id']] = r['description']
#                 if brand_id:
#                     brnd_ids_sm_ids[brand_id] = sm_ids
#                     sm_ids = []
#                 brand_id = r['brand_id']
#             else:
#                 brnd_ids_qty[r['brand_id']] += r['brand_qty']
#                 brnd_ids_sales[r['brand_id']] += float_round(price_unit * r['brand_qty'],5)
# 
# 
# 
#             sm_ids.append(r['stock_move_id'])
# 
#         if brand_id:
#             brnd_ids_sm_ids[brand_id] = sm_ids
#             sm_ids = []
# #        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(sm_ids, brnd_ids_sm_ids))
#         if brnd_ids:
# 
#             for brnd_id in brnd_ids:
#                 res = {}
#                 if brnd_ids_qty[brnd_id] > 0:
#                     res['brand_name'] = brnd_ids_name[brnd_id]
#                     res['description'] = brnd_ids_desc[brnd_id]
#                     res['brand_qty'] = brnd_ids_qty[brnd_id]
#                     res['brand_sales'] = brnd_ids_sales[brnd_id]
#                     st_m_ids = brnd_ids_sm_ids[brnd_id]
#                     val_ss = ''
#                     if st_m_ids:
#                         for ss in st_m_ids:
#                             if val_ss == '':
#                                 val_ss += str(ss)
#                             else:
#                                 val_ss += (', ' + str(ss))
#                     self.cr.execute("select SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
#                             round(CAST(sm_in.price_unit as numeric), 5) * fc.quantity \
#                             ELSE round(CAST(sm_in.price_unit / \
#                             (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
#                             * fc.quantity END) AS test \
#                             from fifo_control fc \
#                             left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
#                             left join stock_move sm_out on fc.out_move_id = sm_out.id \
#                             left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
#                             left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
#                             left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
#                             left join res_company rc on sm_out.company_id = rc.id \
#                             where (fc.out_move_id in (" + val_ss + "))")
#                     res_val = self.cr.dictfetchall()
#                     for res_val1 in res_val:
#                         res['brand_cost'] = res_val1['test']
#                         res['gross_profit'] = brnd_ids_sales[brnd_id] - res_val1['test']
#                         res['gross_profit_p'] = (brnd_ids_sales[brnd_id] - res_val1['test']) / brnd_ids_sales[brnd_id] * 100
#                         self.cost += (res_val1['test'] or 0)
#                     self.qty += (brnd_ids_qty[brnd_id] or 0)
#                     self.sales += (l)
#                     results.append(res)
        results = results and sorted(results, key=lambda val_res: val_res['brand_name']) or []
        return results

report_sxw.report_sxw('report.gross.profit.by.brand.report_landscape', 'account.invoice',
    'addons/max_custom_report/product/report/gross_profit_by_brand_report.rml', parser=gross_profit_by_brand_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
