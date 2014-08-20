# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import time
import pooler
import base64
from tools import float_round, float_is_zero, float_compare

class param_gross_margin_product_report(osv.osv_memory):
    _name = 'param.gross.margin.product.report'
    _description = 'Param Gross Margin Product Report'
    _columns = {
        'date_selection': fields.selection([('none_sel', 'None'), ('date_sel', 'Date')], 'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'invoice_selection': fields.selection([('all_vall', 'All'), ('def', 'Default'), ('input', 'Input'), ('selection', 'Selection')], 'Invoice Filter Selection', required=True),
        'invoice_default_from':fields.many2one('account.invoice', 'Invoice From', domain=[('type', '=', 'out_invoice'), ('state', 'in', ('open', 'paid'))], required=False),
        'invoice_default_to':fields.many2one('account.invoice', 'Invoice To', domain=[('type', '=', 'out_invoice'), ('state', 'in', ('open', 'paid'))], required=False),
        'invoice_input_from': fields.char('Invoice From', size=128),
        'invoice_input_to': fields.char('Invoice To', size=128),
        'invoice_ids' :fields.many2many('account.invoice', 'report_gross_margin_product_invoice_rel', 'report_id', 'invoice_id', 'Invoice No', domain=[('type', '=', 'out_invoice'), ('state', 'in', ('open', 'paid'))]),
        'product_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'product_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[], required=False),
        'product_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[], required=False),
        'product_input_from': fields.char('Supplier Part No From', size=128),
        'product_input_to': fields.char('Supplier Part No To', size=128),
        'product_ids' :fields.many2many('product.product', 'report_gross_margin_pro_pro_rel', 'report_id', 'product_id', 'Product', domain=[]),
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Inventory Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Inventory Brand From', domain=[]),
        'brand_default_to':fields.many2one('product.brand', 'Inventory Brand To', domain=[]),
        'brand_input_from': fields.char('Inventory Brand From', size=128),
        'brand_input_to': fields.char('Inventory Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_gross_margin_pb_rel', 'report_id', 'product_id', 'Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name', size=64),
    }

    _defaults = {
         'date_selection':'none_sel',
         'invoice_selection':'all_vall',
         'product_selection':'all_vall',
         'brand_selection':'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.gross.margin.product.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'gross.margin.product.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        account_invoice_obj = self.pool.get('account.invoice')
        product_product_obj = self.pool.get('product.product')
        product_brand_obj = self.pool.get('product.brand')

        val_pb = []
        val_pp = []
        val_ai = []

        partner_ids = False
        invoice_ids = False
        pb_ids = False
        pp_ids = False
#            data_search = data['form']['supplier_search_vals']            
        #Date
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_from'] = data['form']['date_from']
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'
        
        #Account Invoice
        qry_ai = "type = 'out_invoice' and state in ('open','paid') "
        val_ai.append(('type', '=', 'out_invoice'))
        val_ai.append(('state', 'in', ('open', 'paid')))

        ai_default_from = data['form']['invoice_default_from'] or False
        ai_default_to = data['form']['invoice_default_to'] or False
        ai_input_from = data['form']['invoice_input_from'] or False
        ai_input_to = data['form']['invoice_input_to'] or False
        ai_default_from_str = ai_default_to_str = ''
        ai_input_from_str = ai_input_to_str= ''

        if data['form']['invoice_selection'] == 'all_vall':
            invoice_ids = account_invoice_obj.search(cr, uid, val_ai, order='number ASC')
        if data['form']['invoice_selection'] == 'def':
            data_found = False
            if ai_default_from and account_invoice_obj.browse(cr, uid, ai_default_from) and account_invoice_obj.browse(cr, uid, ai_default_from).number:
                ai_default_from_str = account_invoice_obj.browse(cr, uid, ai_default_from).number
                data_found = True
                val_ai.append(('number', '>=', account_invoice_obj.browse(cr, uid, ai_default_from).number))
            if ai_default_to and account_invoice_obj.browse(cr, uid, ai_default_to) and account_invoice_obj.browse(cr, uid, ai_default_to).number:
                ai_default_to_str = account_invoice_obj.browse(cr, uid, ai_default_to).number
                data_found = True
                val_ai.append(('number', '<=', account_invoice_obj.browse(cr, uid, ai_default_to).number))
                result['ai_selection'] = '"' + ai_default_from_str + '" - "' + ai_default_to_str + '"'
            if data_found:
                invoice_ids = account_invoice_obj.search(cr, uid, val_ai, order='number ASC')
        elif data['form']['invoice_selection'] == 'input':
            data_found = False
            if ai_input_from:
                ai_input_from_str = ai_input_from
                cr.execute("select number " \
                                "from account_invoice "\
                                "where " + qry_ai + " and " \
                                "name ilike '" + str(ai_input_from) + "%' " \
                                "order by number limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_ai.append(('number', '>=', qry['number']))
            if ai_input_to:
                ai_input_to_str = ai_input_to
                cr.execute("select number " \
                                "from account_invoice "\
                                "where " + qry_ai + " and " \
                                "name ilike '" + str(ai_input_to) + "%' " \
                                "order by number desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_ai.append(('number', '<=', qry['number']))
            #print val_part
            result['ai_selection'] = '"' + ai_input_from_str + '" - "' + ai_input_to_str + '"'
            if data_found:
                invoice_ids = account_invoice_obj.search(cr, uid, val_ai, order='number ASC')
        elif data['form']['invoice_selection'] == 'selection':
            av_ids = ''
            if data['form']['invoice_ids']:
                for a in  account_invoice_obj.browse(cr, uid, data['form']['invoice_ids']):
                    av_ids += '"' + str(a.name) + '",'
                invoice_ids = data['form']['invoice_ids']
            result['ai_selection'] = '[' + av_ids +']'
        result['invoice_ids'] = invoice_ids

#product_product
        pp_default_from = data['form']['product_default_from'] or False
        pp_default_to = data['form']['product_default_to'] or False
        pp_input_from = data['form']['product_input_from'] or False
        pp_input_to = data['form']['product_input_to'] or False
        pp_default_from_str = pp_default_to_str = ''
        pp_input_from_str = pp_input_to_str= ''

        if data['form']['product_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')

        elif data['form']['product_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(cr, uid, pp_default_from) and product_product_obj.browse(cr, uid, pp_default_from).name:
                pp_default_from_str = product_product_obj.browse(cr, uid, pp_default_from).name
                data_found = True
                val_pp.append(('name', '>=', product_product_obj.browse(cr, uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(cr, uid, pp_default_to) and product_product_obj.browse(cr, uid, pp_default_to).name:
                pp_default_to_str = product_product_obj.browse(cr, uid, pp_default_to).name
                data_found = True
                val_pp.append(('name', '<=', product_product_obj.browse(cr, uid, pp_default_to).name))
            result['pp_selection'] = '"' + pp_default_from_str + '" - "' + pp_default_to_str + '"'
            if data_found:
                pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        
        elif data['form']['product_selection'] == 'input':
            data_found = False
            if pp_input_from:
                pp_input_from_str = pp_input_from
                cr.execute("select name " \
                                "from product_template "\
                                 "where name ilike '" + str(pp_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '>=', qry['name']))
            if pp_input_to:
                pp_input_to_str = pp_input_to
                cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '<=', qry['name']))
            result['pp_selection'] = '"' + pp_input_from_str + '" - "' + pp_input_to_str + '"'
            if data_found:
                pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        elif data['form']['product_selection'] == 'selection':
            ppr_ids = ''
            if data['form']['product_ids']:
                for ppro in product_product_obj.browse(cr, uid, data['form']['product_ids']):
                    ppr_ids += '"' + str(ppro.name) + '",'
                pp_ids = data['form']['product_ids']
            result['pp_selection'] = '[' + ppr_ids +']'
        result['pp_ids'] = pp_ids

#Product Brand
        brand_default_from = data['form']['brand_default_from'] or False
        brand_default_to = data['form']['brand_default_to'] or False
        brand_input_from = data['form']['brand_input_from'] or False
        brand_input_to = data['form']['brand_input_to'] or False
        brand_default_from_str = brand_default_to_str = ''
        brand_input_from_str = brand_input_to_str= ''

        if data['form']['brand_selection'] == 'all_vall':
            pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')

        elif data['form']['brand_selection'] == 'def':
            data_found = False
            if brand_default_from and product_brand_obj.browse(cr, uid, brand_default_from) and product_brand_obj.browse(cr, uid, brand_default_from).name:
                brand_default_from_str = product_brand_obj.browse(cr, uid, brand_default_from).name
                data_found = True
                val_pb.append(('name', '>=', product_brand_obj.browse(cr, uid, brand_default_from).name))
            if brand_default_to and product_brand_obj.browse(cr, uid, brand_default_to) and product_brand_obj.browse(cr, uid, brand_default_to).name:
                brand_default_to_str = product_brand_obj.browse(cr, uid, brand_default_to).name
                data_found = True
                val_pb.append(('name', '<=', product_brand_obj.browse(cr, uid, brand_default_to).name))
            result['brand_selection'] = '"' + brand_default_from_str + '" - "' + brand_default_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')

        elif data['form']['brand_selection'] == 'input':
            data_found = False
            if brand_input_from:
                brand_input_from_str = brand_input_from
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(brand_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if brand_input_to:
                brand_input_to_str = brand_input_to
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(brand_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '<=', qry['name']))
            result['brand_selection'] = '"' + brand_input_from_str + '" - "' + brand_input_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['brand_selection'] == 'selection':
            pbr_ids = ''
            if data['form']['brand_selection']:
                for pbro in product_brand_obj.browse(cr, uid, data['form']['brand_ids']):
                    pbr_ids += '"' + str(pbro.name) + '",'
                pb_ids = data['form']['brand_ids']
            result['brand_selection'] = '[' + pbr_ids +']'
        result['pb_ids'] = pb_ids
        print pb_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['invoice_selection', 'invoice_default_from', 'invoice_default_to','invoice_input_from', \
                                                'invoice_input_to', 'invoice_ids','brand_selection','brand_default_from','brand_default_to', \
                                                'brand_input_from', 'brand_input_to','brand_ids','product_selection','product_default_from', \
                                                'product_default_to', 'product_input_from','product_input_to','product_ids', \
                                                'date_selection', 'date_from', 'date_to'], context=context)[0]
        
        for field in ['invoice_selection', 'invoice_default_from', 'invoice_default_to', 'invoice_input_from', \
                                                'invoice_input_to', 'invoice_ids','brand_selection','brand_default_from', \
                                                'brand_default_to','brand_input_from', 'brand_input_to','brand_ids','product_selection', \
                                                'product_default_from','product_default_to', 'product_input_from','product_input_to', \
                                                'product_ids','date_selection', 'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_tplines(self, cr, uid, ids, data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        cr = cr
        uid = uid
        
        gt_qty = gt_sales_total = gt_qty_cost = gt_cost_total = gt_margin = gt_gm = 0.00
        gt_sell_price = gt_cost_price = 0.00000

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False

        date_from_qry = date_from and "And l.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date_invoice <= '" + str(date_to) + "' " or " "

        invoice_ids = form['invoice_ids'] or False
        invoice_qry = (invoice_ids and ((len(invoice_ids) == 1 and "AND l.id = " + str(invoice_ids[0]) + " ") or "AND l.id IN " + str(tuple(invoice_ids)) + " ")) or "AND l.id IN (0) "

        pp_ids = form['pp_ids'] or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND ail.product_id = " + str(pp_ids[0]) + " ") or "AND ail.product_id IN " + str(tuple(pp_ids)) + " ")) or "AND ail.product_id IN (0) "

        pb_ids = form['pb_ids'] or False
        pb_qry = (pb_ids and ((len(pb_ids) == 1 and "AND pb.id = " + str(pb_ids[0]) + " ") or "AND pb.id IN " + str(tuple(pb_ids)) + " ")) or "AND pb.id IN (0) "

        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Gross Margin Report by Product' + " \n"
        header += ('ai_selection' in form and 'Invoice Filter Selection : ' + form['ai_selection'] + " \n") or ''
        header += ('pp_selection' in form and 'Product Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('brand_selection' in form and 'Brand Filter Selection : ' + form['brand_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing']) + "\n") or ''
        header += 'CUSTOMER;CPN;SPN;COST OF SOLD;COST PRICE;QTY COST;SELLING PRICE;QTY;TOTAL SELLING;BRAND;INV NO;INV DATE;SALES ZONE;MARGIN;GM %' + " \n"

        cr.execute("select DISTINCT pb.id " \
                        "from account_invoice l " \
                        "INNER JOIN account_invoice_line ail on l.id = ail.invoice_id " \
                        "INNER JOIN product_product pp on pp.id = ail.product_id " \
                        "INNER JOIN product_brand pb on pb.id = pp.brand_id " \
                        "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                        + date_from_qry \
                        + date_to_qry \
                        + invoice_qry \
                        + pp_qry \
                        + pb_qry)
#        print "select DISTINCT pb.id " \
#                        "from account_invoice l " \
#                        "inner join account_invoice_line ail on l.id = ail.invoice_id " \
#                        "inner join product_product pp on pp.id = ail.product_id " \
#                        "inner join product_brand pb on pb.id = pp.brand_id " \
#                        "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
#                        + date_from_qry \
#                        + date_to_qry \
#                        + invoice_qry \
#                        + pp_qry \
#                        + pb_qry
        pb_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                pb_ids_vals.append(r['id'])
        pb_ids_vals_qry = (len(pb_ids_vals) > 0 and ((len(pb_ids_vals) == 1 and "where id = " + str(pb_ids_vals[0]) + " ") or "where id IN " + str(tuple(pb_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name " \
                "FROM product_brand " \
                + pb_ids_vals_qry \
                + " order by name")
#        print "SELECT id, name " \
#                "FROM product_brand " \
#                + pb_ids_vals_qry \
#                + " order by name"
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                header += str(s['name'] or '') + ' \n'
                cr.execute("select rp.name as partner_name, " \
                            "sol.product_customer_id as cpn, " \
                            "pt.name as spn, " \
                            "pb.name as brand_name, " \
                            "l.number as invoice_no, " \
                            "l.date_invoice as inv_date, " \
                            "ail.quantity as quantity, " \
                            "round(CAST(ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1) as numeric), 5) as selling_price, " \
                            "round(CAST((ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1)) * ail.quantity as numeric), 2) as total, " \
                            "rpsz.name as sales_zone, " \
                            "sm.id as move_id " \
                            "from account_invoice l " \
                            "inner join account_invoice_line ail on l.id = ail.invoice_id " \
                            "left join res_partner rp on l.partner_id = rp.id " \
                            "left join product_template pt on ail.product_id = pt.id " \
                            "left join product_product pp on pt.id = pp.id " \
                            "left join product_brand pb on pp.brand_id = pb.id " \
                            "left join stock_move sm on ail.stock_move_id = sm.id " \
                            "left join res_partner_sales_zone rpsz on rpsz.id = l.sales_zone_id " \
                            "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                            "left join sale_order so on sol.order_id = so.id " \
                            "left join stock_location sl on sol.location_id = sl.id " \
                            "left join product_customer pc on sol.product_customer_id = pc.id " \
                            "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                            + date_from_qry \
                            + date_to_qry \
                            + invoice_qry \
                            + pp_qry \
                            + pb_qry + \
                            "and pp.brand_id = " + str(s['id']) + " "\
                            "order by l.date_invoice, l.number")
#                print "select rp.name as partner_name, " \
#                            "sol.product_customer_id as cpn, " \
#                            "pt.name as spn, " \
#                            "pb.name as brand_name, " \
#                            "l.date_invoice as inv_date, " \
#                            "ail.quantity as quantity, " \
#                            "round(CAST(ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1) as numeric), 5) as selling_price, " \
#                            "round(CAST((ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id and name < l.cur_date order by name desc limit 1)) * ail.quantity as numeric), 2) as total, " \
#                            "rpsz.name as sales_zone, " \
#                            "sm.id as move_id " \
#                            "from account_invoice l " \
#                            "inner join account_invoice_line ail on l.id = ail.invoice_id " \
#                            "left join res_partner rp on l.partner_id = rp.id " \
#                            "left join product_template pt on ail.product_id = pt.id " \
#                            "left join product_product pp on pt.id = pp.id " \
#                            "left join product_brand pb on pp.brand_id = pb.id " \
#                            "left join stock_move sm on ail.stock_move_id = sm.id " \
#                            "left join res_partner_sales_zone rpsz on rpsz.id = l.sales_zone_id " \
#                            "left join sale_order_line sol on sm.sale_line_id = sol.id " \
#                            "left join sale_order so on sol.order_id = so.id " \
#                            "left join stock_location sl on sol.location_id = sl.id " \
#                            "left join product_customer pc on sol.product_customer_id = pc.id " \
#                            "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
#                            + date_from_qry \
#                            + date_to_qry \
#                            + invoice_qry \
#                            + pp_qry \
#                            + pb_qry + \
#                            "and pp.brand_id = " + str(s['id']) + " "\
#                            "order by l.date_invoice, l.number"
                res_lines = cr.dictfetchall()
                lines_ids = []
                st_total_qty = st_total_cost_qty = 0
                st_total_cost = st_total = st_margin = st_gm = 0.00
                if res_lines:
                    for val_lines in res_lines:
                        cr.execute("select fc.quantity as qty, \
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
                        cost_val = cr.dictfetchall()

                        margin_percent = 0
                        margin = 0
                        first_val = False
                        for cost_lines in cost_val:
                            if not first_val:
                                cr.execute("select coalesce(SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
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
                                res_val = cr.dictfetchone()
#                                print val_lines['total']
#                                print res_val['test']
                                margin = val_lines['total'] - res_val['test']
                                if val_lines['total'] > 0:
                                    margin_percent = margin / val_lines['total'] * 100
                                else:
                                    margin_percent = 0
                                first_val = True
                                header += str(val_lines['partner_name'] or '') + ";" + str(val_lines['cpn'] or '') + ";" \
                                + str(val_lines['spn'] or '') + ";" + str(res_val['test'] or 0) + ";" \
                                + str(cost_lines['cost_price'] or 0) + ";" + str(cost_lines['qty'] or 0) + ";" \
                                + str(val_lines['selling_price'] or 0.00000) + ";" + str(val_lines['quantity'] or 0) + ";" \
                                + str(val_lines['total'] or 0) + ";" + str(val_lines['brand_name'] or '') + ";" \
                                + str(val_lines['inv_date'] or '') + ";" + str(val_lines['invoice_no'] or '') + ";" \
                                + str(val_lines['sales_zone'] or '') + ";" \
                                + str(margin or 0) + ";" + str(float_round(margin_percent, 2) or 0.00) + "% \n"
                                st_total_qty += val_lines['quantity'] or 0
                                st_total_cost_qty += cost_lines['qty'] or 0
                                st_total_cost += res_val['test'] or 0.00
                                st_total += val_lines['total'] or 0.00
                                st_margin += margin
                                st_gm += float_round(margin_percent, 2) or 0.00
                                gt_qty += val_lines['quantity'] or 0.00
                                gt_sell_price += val_lines['selling_price'] or 0.0000
                                gt_sales_total += val_lines['total'] or 0.00
                                gt_qty_cost += cost_lines['qty'] or 0.00
                                gt_cost_price += cost_lines['cost_price'] or 0.00000
                                gt_cost_total += res_val['test'] or 0.00
                                gt_margin += margin or 0.00
                                gt_gm += float_round(margin_percent, 2) or 0.00
                            else:
                                header += str('') + ";" + str('') + ";" + str('') + ";" \
                                + str('') + ";" \
                                + str(cost_lines['cost_price'] or 0) + ";" \
                                + str(cost_lines['qty'] or 0) + ";" + " \n"
                                st_total_cost_qty += cost_lines['qty'] or 0
#                                st_total_cost += (cost_lines['cost_price'] or 0.00) * (cost_lines['qty'] or 0)
                                gt_qty_cost += cost_lines['qty'] or 0.00
                                gt_cost_price += cost_lines['cost_price'] or 0.00000
                    header += 'Sub-Total : ' + ';' + ';' + ';' + str(float_round(st_total_cost,2)) + ';' + ';' \
                            + str(float_round(st_total_cost_qty,0)) + ';' + ';' + str(float_round(st_total_qty,0)) + \
                            ';' + str(float_round(st_total,2)) + ';' + ';' + ';' + ';' + ";" + str(st_margin) + ';' + str(st_gm) + '%' + ' \n'
        header += ' \n' + 'Grand Total' + ';' + ';' + ';' + str(float_round(gt_cost_total,2)) + ';' \
        + str(float_round(gt_cost_price,5)) + ';' + str(float_round(gt_qty_cost,2)) + ';' \
        + str(float_round(gt_sell_price,5)) + ';' + str(float_round(gt_qty,2)) + ';' + str(float_round(gt_sales_total,2)) + ';' \
        + ";" + ";" + ";" + ";" + str(float_round(gt_margin,2)) + ";" + str(float_round(gt_gm,2)) + '%' + ' \n'
        
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''
    
        filename = 'Gross Margin Report by Product Brand.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','gross_margin_product_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Gross Margin Report by Product Brand',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.gross.margin.product.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_gross_margin_product_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
