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

class param_gross_profit_by_brand_report(osv.osv_memory):
    _name = 'param.gross.profit.by.brand.report'
    _description = 'Param Gross Profit By Inventory Brand Report'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("Voucher Date From"),
        'date_to': fields.date("Voucher Date To"),
        #Product Brand Selection
        'pb_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Inventory Brand Filter Selection', required=True),
        'pb_default_from':fields.many2one('product.brand', 'Inventory Brand From', domain=[], required=False),
        'pb_default_to':fields.many2one('product.brand', 'Inventory Brand To', domain=[], required=False),
        'pb_input_from': fields.char('Inventory Brand From', size=128),
        'pb_input_to': fields.char('Inventory Brand To', size=128),
        'pb_ids' :fields.many2many('product.brand', 'report_gross_profit_pb_rel', 'report_id', 'pb_id', 'Inventory Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'pb_selection':'all_vall',
        'date_selection':'none_sel',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.gross.profit.by.brand.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'gross.profit.by.brand.report_landscape',
            'datas': datas,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')

        data['form'] = self.read(cr, uid, ids, ['date_selection', 'date_from', 'date_to', \
                                                'pb_selection','pb_default_from','pb_default_to', 'pb_input_from','pb_input_to','pb_ids', \
                                                ], context=context)[0]
        for field in ['date_selection', 'date_from', 'date_to', \
                                                'pb_selection','pb_default_from','pb_default_to', 'pb_input_from','pb_input_to','pb_ids']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        new_ids = ids
        res = {}
        product_brand_obj = self.pool.get('product.brand')
        val_pb = []
        pb_ids = False
        
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        pb_default_from = data['form']['pb_default_from'] or False
        pb_default_to = data['form']['pb_default_to'] or False
        pb_input_from = data['form']['pb_input_from'] or False
        pb_input_to = data['form']['pb_input_to'] or False
        pb_default_from_str = pb_default_to_str = ''
        pb_input_from_str = pb_input_to_str= ''
        
        if data['form']['pb_selection'] == 'all_vall':
            pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        if data['form']['pb_selection'] == 'def':
            data_found = False
            if pb_default_from and product_brand_obj.browse(cr, uid, pb_default_from) and product_brand_obj.browse(cr, uid, pb_default_from).name:
                pb_default_from_str = product_brand_obj.browse(cr, uid, pb_default_from).name
                data_found = True
                val_pb.append(('name', '>=', product_brand_obj.browse(cr, uid, pb_default_from).name))
            if pb_default_to and product_brand_obj.browse(cr, uid, pb_default_to) and product_brand_obj.browse(cr, uid, pb_default_to).name:
                pb_default_to_str = product_brand_obj.browse(cr, uid, pb_default_to).name
                data_found = True
                val_pb.append(('name', '<=', product_brand_obj.browse(cr, uid, pb_default_to).name))
            result['pb_selection'] = '"' + pb_default_from_str + '" - "' + pb_default_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'input':
            data_found = False
            if pb_input_from:
                pb_input_from_str = pb_input_from
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(pb_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if pb_input_to:
                pb_input_to_str = pb_input_to
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(pb_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '<=', qry['name']))
            #print val_part
            result['pb_selection'] = '"' + pb_input_from_str + '" - "' + pb_input_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(self.cr, self.uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'selection':
            pbr_ids = ''
            if data['form']['pb_ids']:
                for pbro in product_brand_obj.browse(cr, uid, data['form']['pb_ids']):
                    pbr_ids += '"' + str(pbro.name) + '",'
                pb_ids = data['form']['pb_ids']
            result['pb_selection'] = '[' + pbr_ids +']'
        result['pb_ids'] = pb_ids

        return result

    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []

        results = []
        cr = cr
        uid = uid
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        cost = 0
        qty = 0
        sales = 0
        product_product_obj = self.pool.get('product.product')
        res_company_obj = self.pool.get('res.company')
        currency_pool = self.pool.get('res.currency')
        pb_ids = form['pb_ids'] or False
        brnd_ids = []
        brnd_ids_sm_ids = {}
        brnd_ids_qty = {}
        brnd_ids_sales = {}
        brnd_ids_cost = {}
        brnd_ids_name = {}
        brnd_ids_desc = {}
        date_from = date_from
        date_to = date_to

        pb_qry = (pb_ids and ((len(pb_ids) == 1 and "AND pb.id = " + str(pb_ids[0]) + " ") or "AND pb.id IN " + str(tuple(pb_ids)) + " ")) or "AND pb.id IN (0) "

        date_from_qry = date_from and "AND ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "AND ai.date_invoice <= '" + str(date_to) + "' " or " "

        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Gross Profit By Inventory Brand Report' + " \n"
        header += ('pb_selection' in form and 'Inventory Brand Selection : ' + form['pb_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing']) + "\n") or ''
        header += 'Inventory Brand Key;Main Description;Qty;Sales;Cost;Gross;GP %' + " \n"
        cost = qty = sales = 0
        cr.execute("SELECT distinct pb.id as brand_id \
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
                        product_id = product_product_obj.browse(cr, uid, t['product_id'])
                        company_currency = res_company_obj.browse(cr, uid, t['company_id']).currency_id.id
                        if t['currency_id'] == company_currency:
                            price_unit = t['brand_price']
                        else:
                            ctx = {}
                            ctx.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
                            ctx2 = {}
                            ctx2.update({'date': t['cur_date']})
                            rate_inv = currency_pool.browse(cr, uid, t['currency_id'], context=ctx2).rate
                            rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
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
                cost += (brand_cost or 0)
                qty += (brand_qty or 0)
                sales += (brand_price or 0)
                header += str(s['name'] or '') + ";" + str(s['description'] or '') + ";" \
                            + str("%.2f" % brand_qty) + ";" + str("%.5f" % brand_price) + ";" + str("%.5f" % brand_cost) + ";" \
                            + str("%.5f" % gross_profit) + ";" + str("%.5f" % gross_profit_p) + "% \n"
                results.append({
                    'brand_name' : s['name'],
                    'description' : s['description'],
                    'brand_qty' : brand_qty,
                    'brand_sales' : brand_price,
                    'brand_cost' : brand_cost,
                    'gross_profit' : gross_profit,
                    'gross_profit_p' : gross_profit_p,
                })
        header += 'Report Total;;' + str("%.2f" % qty or 0) + ";" + str("%.2f" % sales or 0.00) + ";" + str("%.2f" % cost or 0) + ";" + str("%.2f" % (sales - cost) or 0) + ";" + str("%.5f" % ((sales - cost) / sales * 100) or 0) + "% \n" 
        
#         cr.execute("SELECT pb.id as brand_id, pb.name as brand_name, pb.description as description, \
#         ail.quantity as brand_qty, ail.uos_id as brand_uom, ail.price_unit as brand_price, \
#         ail.product_id as product_id, ai.currency_id as currency_id, ail.company_id as company_id, \
#         ai.cur_date as cur_date, ail.stock_move_id as stock_move_id \
#         from account_invoice_line ail \
#         inner join account_invoice ai on ail.invoice_id = ai.id \
#         inner join product_product pp on ail.product_id = pp.id \
#         inner join product_brand pb on pp.brand_id= pb.id \
#         WHERE ai.state in ('open', 'paid') AND ai.type = 'out_invoice' "\
#         + pb_qry \
#         + date_from_qry \
#         + date_to_qry  +\
#         "order by pb.name")
# 
#         res_general = cr.dictfetchall()
#         sm_ids = []
#         brand_id = False
#         for r in res_general:
#             product_id = product_product_obj.browse(cr, uid, r['product_id'])
#             company_currency = res_company_obj.browse(cr, uid, r['company_id']).currency_id.id
#             if r['currency_id'] == company_currency:
#                 price_unit = r['brand_price']
#             else:
#                 ctx = {}
#                 ctx.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
#                 ctx2 = {}
#                 ctx2.update({'date': r['cur_date']})
#                 rate_inv = currency_pool.browse(cr, uid, r['currency_id'], context=ctx2).rate
#                 rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
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
#                     cr.execute("select SUM(CASE WHEN COALESCE(pp_in.currency_id, rc.currency_id) = rc.currency_id THEN \
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
#                     res_val = cr.dictfetchall()
#                     for res_val1 in res_val:
#                         res['brand_cost'] = res_val1['test']
#                         res['gross_profit'] = brnd_ids_sales[brnd_id] - res_val1['test']
#                         res['gross_profit_p'] = (brnd_ids_sales[brnd_id] - res_val1['test']) / brnd_ids_sales[brnd_id] * 100
#                         cost += (res_val1['test'] or 0)
#                     qty += (brnd_ids_qty[brnd_id] or 0)
#                     sales += (brnd_ids_sales[brnd_id] or 0)
#                     header += str(res['brand_name'] or '') + ";" + str(res['description'] or '') + ";" \
#                             + str("%.2f" % res['brand_qty'] or 0) + ";" + str("%.5f" % res['brand_sales'] or 0) + ";" + str("%.5f" % res['brand_cost'] or 0) + ";" \
#                             + str("%.5f" % res['gross_profit'] or 0) + ";" + str("%.5f" % res['gross_profit_p'] or 0) + "% \n"
#             header += 'Report Total;;' + str("%.2f" % qty or 0) + ";" + str("%.2f" % sales or 0.00) + ";" + str("%.2f" % cost or 0) + ";" + str("%.2f" % (sales - cost) or 0) + ";" + str("%.5f" % ((sales - cost) / sales * 100) or 0) + "% \n" 
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Gross Profit By Inventory Brand Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','gross_profit_by_brand_report_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Gross Profit By Inventory Brand Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.gross.profit.by.brand.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_gross_profit_by_brand_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
