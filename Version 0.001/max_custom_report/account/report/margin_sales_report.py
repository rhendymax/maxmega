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
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.inv_from = data['form']['inv_from'] and data['form']['inv_from'][0] or False
        self.inv_to = data['form']['inv_to'] and data['form']['inv_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(margin_sales_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(margin_sales_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_inv_from': self._get_inv_from,
            'get_inv_to': self._get_inv_to,
            })

    def _get_inv_from(self):
        return self.inv_from and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_from).number or False
    
    def _get_inv_to(self):
        return self.inv_to and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_to).number or False

    def _get_lines(self):
        results = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        inv_from = self.inv_from
        inv_to = self.inv_to
        val_inv = []
        account_invoice_obj = self.pool.get('account.invoice')
        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
            val_inv.append(('name', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
        inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv, order='number ASC')
        val_ss = ''
        if inv_ids:
            for ss in inv_ids:
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
                        "and ai.id in (" + val_ss + ") " \
                        "group by cust_name, cust_ref, cust_id " \
                        "order by cust_name, cust_ref, cust_id")
        res_general = self.cr.dictfetchall()
        for val in res_general:
            res = {}
            res['cust_name'] = '[' + val['cust_ref'] + '] ' + val['cust_name']
            self.cr.execute("select pt.name as inventory_key, " \
                        "ai.date_invoice as inv_date, " \
                        "ai.number as invoice_no, " \
                        "ail.quantity as quantity, " \
                        "round(CAST(ail.price_unit / (select rate from res_currency_rate where currency_id = ai.currency_id and name < ai.cur_date order by name desc limit 1) as numeric), 5) as selling_price, " \
                        "round(CAST((ail.price_unit / (select rate from res_currency_rate where currency_id = ai.currency_id and name < ai.cur_date order by name desc limit 1)) * ail.quantity as numeric), 2) as total, " \
                        "sm.id as move_id " \
                        "from account_invoice ai " \
                        "inner join account_invoice_line ail on ai.id = ail.invoice_id " \
                        "left join res_partner rp on ai.partner_id = rp.id " \
                        "left join product_template pt on ail.product_id = pt.id " \
                        "left join product_product pp on pt.id = pp.id " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "left join stock_move sm on ail.stock_move_id = sm.id " \
                        "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "left join sale_order so on sol.order_id = so.id " \
                        "left join stock_location sl on sol.location_id = sl.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null " \
                        "and ai.date_invoice >= '" + str(date_from) + "' AND ai.date_invoice <= '" + str(date_to) + "' " \
                        "and pp.brand_id in (" + val_ss + ") " \
                        "and ai.partner_id = " + str(val['cust_id']) + " " \
                        "order by ai.date_invoice, invoice_no")
            res_lines = self.cr.dictfetchall()
            lines_ids = []
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
                        self.cr.execute("select SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
                                round(CAST(sm_in.price_unit as numeric), 5) * fc.quantity \
                                ELSE round(CAST(sm_in.price_unit / \
                                (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
                                * fc.quantity END) AS test \
                                from fifo_control fc \
                                left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
                                left join stock_move sm_out on fc.out_move_id = sm_out.id \
                                left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
                                left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
                                left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
                                left join res_company rc on sm_out.company_id = rc.id \
                                where (fc.out_move_id = " + str(val_lines['move_id']) + ")")
                        res_val = self.cr.dictfetchone()
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
#                self.cr.execute("select SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
#                        round(CAST(sm_in.price_unit as numeric), 5) * fc.quantity \
#                        ELSE round(CAST(sm_in.price_unit / \
#                        (select rate from res_currency_rate where currency_id = pp_in.currency_id and name >=  sp_in.do_date order by name limit 1) as numeric), 5) \
#                        * fc.quantity END) AS test \
#                        from fifo_control fc \
#                        left join stock_move sm_in on COALESCE(fc.int_in_move_id, fc.in_move_id) = sm_in.id \
#                        left join stock_move sm_out on fc.out_move_id = sm_out.id \
#                        left join stock_picking sp_in on sm_in.picking_id = sp_in.id \
#                        left join stock_picking sp_out on sm_out.picking_id = sp_out.id \
#                        left join product_pricelist pp_in on sp_in.pricelist_id = pp_in.id \
#                        left join res_company rc on sm_out.company_id = rc.id \
#                        where (fc.out_move_id = " + str(val_lines['move_id']) + ")")
#                res_val = self.cr.dictfetchone()

#                margin = val_lines['total'] - res_val['test']
#                if val_lines['total'] > 0:
#                    margin_percent = margin / val_lines['total'] * 100
#                else:
#                    margin_percent = 0
#                    lines_ids.append({
#                        'inventory_key' : val_lines['inventory_key'],
#                        'inv_date' : val_lines['inv_date'],
#                        'invoice_no' : val_lines['invoice_no'],
#                        'quantity' : val_lines['quantity'],
#                        'selling_price' : val_lines['selling_price'],
#                        'total' : val_lines['total'],
#                        'total_cost' : res_val['test'],
#                        'margin' : margin,
#                        'margin_percent' : margin_percent,
#                        })
#                    
            res['lines'] = lines_ids
            results.append(res)
        return results

report_sxw.report_sxw('report.margin.sales.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/margin_sales_report.rml', parser=margin_sales_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
