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

class param_monthly_pos_report(osv.osv_memory):
    _name = 'param.monthly.pos.report'
    _description = 'Param Monthly POS Report by Brand'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Inventory Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Inventory Brand From', domain=[], required=False),
        'brand_default_to':fields.many2one('product.brand', 'Inventory Brand To', domain=[], required=False),
        'brand_input_from': fields.char('Inventory Brand From', size=128),
        'brand_input_to': fields.char('Inventory Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_monthly_brand_rel', 'report_id', 'brand_id', 'Inventory Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
       'date_selection':'none_sel',
       'brand_selection':'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.monthly.pos.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'monthly.pos.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        cr              = cr
        uid             = uid
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
            if data_found:
                result['brand_selection'] = '"' + brand_default_from_str + '" - "' + brand_default_to_str + '"'
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
            if data_found:
                result['brand_selection'] = '"' + brand_input_from_str + '" - "' + brand_input_to_str + '"'
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['brand_selection'] == 'selection':
            pbr_ids = ''
            if data['form']['brand_selection']:
                for pbro in product_brand_obj.browse(cr, uid, data['form']['brand_ids']):
                    pbr_ids += '"' + str(pbro.name) + '",'
                pb_ids = data['form']['brand_ids']
            result['brand_selection'] = '[' + pbr_ids +']'
        result['pb_ids'] = pb_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['brand_selection','brand_default_from', 'brand_default_to', \
                      'brand_input_from', 'brand_input_to','brand_ids','date_selection', \
                    'date_from', 'date_to'], context=context)[0]
        
        for field in ['brand_selection','brand_default_from', 'brand_default_to', \
                      'brand_input_from', 'brand_input_to','brand_ids','date_selection', \
                    'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        results = []
        cr              = cr
        uid             = uid
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Monthly POS Report by Brand' + " \n"
        header += ('date_selection' in form and 'Inv Date : ' + str(form['date_showing']) + "\n") or ''
        header += ('brand_selection' in form and 'Product Brand : ' + form['brand_selection'] + "\n") or ''
        header += 'BRAND;CUSTOMER;CPN;SPN;S/P US$;QTY;TOTAL SELLING US$;INV DATE' + " \n"

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And l.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date_invoice <= '" + str(date_to) + "' " or " "
# 
        brand_ids = form['pb_ids'] or False
#         brand_qry = (brand_ids and ((len(brand_ids) == 1 and "AND pb.brand_id = " + str(brand_ids[0]) + " ") or "AND pp.brand_id IN " + str(tuple(brand_ids)) + " ")) or "AND pp.brand_id IN (0) "
        brand_qry = (brand_ids and ((len(brand_ids) == 1 and "AND pb.id = " + str(brand_ids[0]) + " ") or "AND pb.id IN " + str(tuple(brand_ids)) + " ")) or "AND pb.id IN (0) "
# 
#         cr.execute("select  DISTINCT l.partner_id " \
#                         "from account_invoice l " \
#                         "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
#                         "left join product_product pp on ail.product_id = pp.id  " \
#                         "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
#                         + date_from_qry \
#                         + date_to_qry \
#                         + brand_qry)
#         partner_ids_vals = []
#         qry2 = cr.dictfetchall()
#         if qry2:
#             for r in qry2:
#                 partner_ids_vals.append(r['partner_id'])
#         partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "
# 
#         cr.execute(
#                 "SELECT id, name, ref " \
#                 "FROM res_partner " \
#                 + partner_ids_vals_qry \
#                 + " order by name")
#         qry = cr.dictfetchall()
#         if qry:
#             for s in qry:
#         brand_ids = []
#         qty = total = 0
#         cr.execute("select DISTINCT pp.brand_id " \
#                         "from account_invoice l " \
#                         "inner join account_invoice_line ail on l.id = ail.invoice_id  " \
#                         "left join product_product pp on ail.product_id = pp.id  " \
#                         "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
#                         + date_from_qry \
#                         + date_to_qry \
#                         + brand_qry)
#         brand_ids_vals = []
#         qry_brand1 = cr.dictfetchall()
#         if qry_brand1:
#             for brand_r in qry_brand1:
#                 brand_ids_vals.append(brand_r['brand_id'])
#         brand_ids_vals_qry = (len(brand_ids_vals) > 0 and ((len(brand_ids_vals) == 1 and "where id = " +  str(brand_ids_vals[0]) + " ") or "where id IN " +  str(tuple(brand_ids_vals)) + " ")) or "where id IN (0) "
#         cr.execute(
#                 "SELECT id, name " \
#                 "FROM product_brand " \
#                 + brand_ids_vals_qry \
#                 + " order by name")
#         qry_brand2 = cr.dictfetchall()
#         for brand_s in qry_brand2:
        
        cr.execute("select pb.name as brand_name, rp.ref as partner_ref, rp.name as partner_name, " \
                   "pc.name as cpn, pt.name as inv_key, " \
#                     "ail.price_unit as selling_price, " \
                    "ail.price_unit / (select rate from res_currency_rate where currency_id = l.currency_id " \
                    "and name <= l.cur_date order by name desc limit 1) as selling_price, " \
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
                    "left join product_brand pb on pp.brand_id = pb.id " \
                    "left join res_partner rp on l.partner_id = rp.id " \
                    "where l.type = 'out_invoice' and l.state in ('open','paid') and ail.product_id is not null  " \
                    + brand_qry \
                    + date_from_qry \
                    + date_to_qry + \
#                     "and l.partner_id = " + str(s['id']) + " "\
#                     "and pp.brand_id = " + str(brand_s['id']) + " "\
                    "order by brand_name, partner_name, l.date_invoice"
                    )
        qry3 = cr.dictfetchall()
    
        brand_lines = []
        brand_qty = brand_total = 0
        prec_sale = self.pool.get('decimal.precision').precision_get(cr, uid, 'Sale Price')
        prec_acc = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')

#         result = round(amount, prec)
        if qry3:
            total_qty = 0
            total = 0.00000
            for t in qry3:
                price_unit = round(t['selling_price'],prec_sale)
                sub_total = round((price_unit * t['quantity']),prec_acc)
                header += str(t['brand_name'] or '') + ';' + str(('[' + t['partner_ref'] + '] ' + t['partner_name']) or '') + ';' \
                            + str(t['cpn'] or '') + ';' + str(t['inv_key'] or '') + ';' \
                            + str(price_unit) + ';' + str(t['quantity'] or 0) + ';' \
                            + str(sub_total or 0.00) + ';' + str(t['date_inv'] or '') + '\n'
                total_qty += t['quantity'] or 0
                total += sub_total
            header += ';;;;' + 'Grand Total :;' + str(total_qty) + ';' + str(total) + '\n'
#                 brand_lines.append({
#                                     'cpn' : t['cpn'],
#                                     'inv_key': t['inv_key'],
#                                     'selling_price': t['selling_price'],
#                                     'quantity': t['quantity'],
#                                     'total': t['total'],
#                                     'brand':brand_s['name'],
#                                     'date_inv': t['date_inv'],
#                                     })
#                 brand_qty += t['quantity']
#                 brand_total += t['total']
#         brand_ids.append({
#                           'brand_name' : brand_s['name'],
#                           'qty' : brand_qty,
#                           'total' : brand_total,
#                           'lines': brand_lines,
#                           })
#         qty += brand_qty
#         total += brand_total
#         self.qty += qty
#         self.total += total
#     results.append({
#             'part_name' : s['name'],
#             'part_ref' : s['ref'],
#             'brand_ids': brand_ids,
#             'qty' : qty,
#             'total' : total,
#                     })

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''
        filename = 'Monthly POS Report by Brand.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_param_monthly_pos_report_by_brand_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Monthly POS Report by Brand',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.monthly.pos.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_monthly_pos_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
