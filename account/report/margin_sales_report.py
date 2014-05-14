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

class margin_sales_report(report_sxw.rml_parse):
    _name = 'margin.sales.report'

    def set_context(self, objects, data, ids, report_type=None):
            new_ids = ids
            res = {}
            account_invoice_obj = self.pool.get('account.invoice')
            qry_supp = ''
            val_part = []
            qry_ai = ''
            val_ai = []
            
            partner_ids = False
            invoice_ids = False
#            data_search = data['form']['supplier_search_vals']            
            #Date
            if data['form']['date_selection'] == 'none_sel':
                self.date_from = False
                self.date_to = False
            else:
                self.date_from = data['form']['date_from']
                self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'
    
    #invoice
            qry_ai = 'type = "out_invoice" and state in ("open","paid") '
            val_ai.append(('type','=', 'out_invoice'))
            val_ai.append(('state','in', ('open','paid')))
            ai_default_from = data['form']['invoice_default_from'] and data['form']['invoice_default_from'][0] or False
            ai_default_to = data['form']['invoice_default_to'] and data['form']['invoice_default_to'][0] or False
            ai_input_from = data['form']['invoice_input_from'] or False
            ai_input_to = data['form']['invoice_input_to'] or False
    
            if data['form']['invoice_selection'] == 'all_vall':
                invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            if data['form']['invoice_selection'] == 'def':
                data_found = False
                if ai_default_from and account_invoice_obj.browse(self.cr, self.uid, ai_default_from) and account_invoice_obj.browse(self.cr, self.uid, ai_default_from).number:
                    data_found = True
                    val_ai.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, ai_default_from).number))
                if ai_default_to and account_invoice_obj.browse(self.cr, self.uid, ai_default_to) and account_invoice_obj.browse(self.cr, self.uid, ai_default_to).number:
                    data_found = True
                    val_ai.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, ai_default_to).number))
                if data_found:
                    invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            elif data['form']['invoice_selection'] == 'input':
                data_found = False
                if ai_input_from:
                    self.cr.execute("select number " \
                                    "from account_invoice "\
                                    "where " + qry_ai + " and " \
                                    "name ilike '" + str(ai_input_from) + "%' " \
                                    "order by number limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_ai.append(('number', '>=', qry['number']))
                if ai_input_to:
                    self.cr.execute("select number " \
                                    "from account_invoice "\
                                    "where " + qry_ai + " and " \
                                    "name ilike '" + str(ai_input_to) + "%' " \
                                    "order by number desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_ai.append(('number', '<=', qry['number']))
                #print val_part
                if data_found:
                    invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            elif data['form']['invoice_selection'] == 'selection':
                if data['form']['invoice_ids']:
                    invoice_ids = data['form']['invoice_ids']
            self.invoice_ids = invoice_ids

            return super(margin_sales_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(margin_sales_report, self).__init__(cr, uid, name, context=context)
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

        invoice_ids = self.invoice_ids or False
        invoice_qry = (invoice_ids and ((len(invoice_ids) == 1 and "AND l.id = " + str(invoice_ids[0]) + " ") or "AND l.id IN " + str(tuple(invoice_ids)) + " ")) or "AND l.id IN (0) "

        self.cr.execute("select  DISTINCT l.partner_id " \
                        "from account_invoice l " \
                        "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
                        "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                        + date_from_qry \
                        + date_to_qry \
                        + invoice_qry)
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
                cr.execute("select pt.name as inventory_key, " \
                            "l.date_invoice as inv_date, " \
                            "l.number as invoice_no, " \
                            "ail.quantity as quantity, " \
                            "round(CAST(ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1) as numeric), 5) as selling_price, " \
                            "round(CAST((ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1)) * ail.quantity as numeric), 2) as total, " \
                            "sm.id as move_id " \
                            "from account_invoice l " \
                            "inner join account_invoice_line ail on l.id = ail.invoice_id " \
                            "left join res_partner rp on l.partner_id = rp.id " \
                            "left join product_template pt on ail.product_id = pt.id " \
                            "left join product_product pp on pt.id = pp.id " \
                            "left join product_brand pb on pp.brand_id = pb.id " \
                            "left join stock_move sm on ail.stock_move_id = sm.id " \
                            "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                            "left join sale_order so on sol.order_id = so.id " \
                            "left join stock_location sl on sol.location_id = sl.id " \
                            "left join product_customer pc on sol.product_customer_id = pc.id " \
                            "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                            + date_from_qry \
                            + date_to_qry \
                            + invoice_qry + \
                            "and l.partner_id = " + str(s['id']) + " "\
                            "order by l.date_invoice, l.number")
                res_lines = cr.dictfetchall()
                lines_ids = []
                if res_lines:
                    for val_lines in res_lines:
                        self.cr.execute("select fc.quantity as qty, \
                                (CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
                                round(CAST(sm_in.price_unit as numeric), 5) \
                                ELSE round(CAST(sm_in.price_unit / \
                                (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
                                 END) AS cost_price \
                                from fifo_control fc \
                                left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
                                left join stock_move sm_out on fc.out_move_id = sm_out.id \
                                left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
                                left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
                                left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
                                left join res_company rc on sm_out.company_id = rc.id \
                                where (fc.out_move_id = " + str(val_lines['move_id']) + ")")
                        cost_val = self.cr.dictfetchall()

                        margin_percent = 0
                        margin = 0
                        first_val = False
                        for cost_lines in cost_val:
                            if not first_val:
                                self.cr.execute("select coalesce(SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
                                        round(CAST(sm_in.price_unit as numeric), 5) * fc.quantity \
                                        ELSE round(CAST(sm_in.price_unit / \
                                        (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
                                        * fc.quantity END),0) AS test \
                                        from fifo_control fc \
                                        left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
                                        left join stock_move sm_out on fc.out_move_id = sm_out.id \
                                        left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
                                        left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
                                        left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
                                        left join res_company rc on sm_out.company_id = rc.id \
                                        where (fc.out_move_id = " + str(val_lines['move_id']) + ")")
                                res_val = self.cr.dictfetchone()
#                                print val_lines['total']
#                                print res_val['test']
                                margin = val_lines['total'] - res_val['test']
                                if val_lines['total'] > 0:
                                    margin_percent = margin / val_lines['total'] * 100
                                else:
                                    margin_percent = 0
                                first_val = True
                                lines_ids.append({
                                    'inventory_key' : val_lines['inventory_key'],
                                    'inv_date' : val_lines['inv_date'],
                                    'invoice_no' : val_lines['invoice_no'],
                                    'quantity' : val_lines['quantity'],
                                    'selling_price' : val_lines['selling_price'],
                                    'total' : val_lines['total'],
                                    'qty_cost' : cost_lines['qty'],
                                    'cost_price' : cost_lines['cost_price'],
                                    'total_cost' : res_val['test'],
                                    'margin' : margin,
                                    'margin_percent' : str(float_round(margin_percent,2)) + '%',
                                    })
                            else:
                                lines_ids.append({
                                    'inventory_key' : '',
                                    'inv_date' : '',
                                    'invoice_no' : '',
                                    'quantity' : '',
                                    'selling_price' : '',
                                    'total' : '',
                                    'qty_cost' : cost_lines['qty'],
                                    'cost_price' : cost_lines['cost_price'],
                                    'total_cost' : '',
                                    'margin' : '',
                                    'margin_percent' : '',
                                    })
                results.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    'lines': lines_ids,
                    })
            
        results = results and sorted(results, key=lambda val_res: val_res['part_name']) or []
        return results

report_sxw.report_sxw('report.margin.sales.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/margin_sales_report.rml', parser=margin_sales_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
