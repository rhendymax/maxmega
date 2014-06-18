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
from tools.translate import _
from tools import float_round, float_is_zero, float_compare

class param_monthly_sale_report(osv.osv_memory):
    _name = 'param.monthly.sale.report'
    _description = 'Param Monthly Sale Report'
    _columns = {
        'customer_search_vals': fields.selection([('code','Customer Code'),('name', 'Customer Name')],'Customer Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Cust Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Customer From', domain=[('customer','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Customer To', domain=[('customer','=',True)], required=False),
        'partner_input_from': fields.char('Customer From', size=128),
        'partner_input_to': fields.char('Customer To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_monthly_sale_customer_rel', 'report_id', 'partner_id', 'Customer', domain=[('customer','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'pb_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Product Brand Filter Selection', required=True),
        'pb_default_from':fields.many2one('product.brand', 'Product Brand From', domain=[], required=False),
        'pb_default_to':fields.many2one('product.brand', 'Product Brand To', domain=[], required=False),
        'pb_input_from': fields.char('Product Brand From', size=128),
        'pb_input_to': fields.char('Product Brand To', size=128),
        'pb_ids' :fields.many2many('product.brand', 'report_monthly_sale_brand_rel', 'report_id', 'pb_id', 'Product Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d')
        'date_selection': 'none_sel',
        'customer_search_vals': 'code',
        'filter_selection': 'all_vall',
        'pb_selection': 'all_vall',
    }
    
    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.monthly.sale.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'monthly.sale.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        product_brand_obj = self.pool.get('product.brand')
        period_obj = self.pool.get('account.period')
        qry_cust = ''
        val_part = []
        qry_pb = ''
        val_pb = []
    
        partner_ids = False
        so_ids = False
        data_search = data['form']['customer_search_vals']
        
        qry_supp = 'customer = True'
        val_part.append(('customer', '=', True))

        partner_default_from = data['form']['partner_default_from'] or False
        partner_default_to = data['form']['partner_default_to'] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False
        partner_default_from_str = partner_default_to_str = ''
        partner_input_from_str = partner_input_to_str= ''
        if data_search == 'code':
            result['data_search'] = 'Customer Code'
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).ref:
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).ref
                    data_found = True
                    val_part.append(('ref', '>=', res_partner_obj.browse(cr, uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).ref:
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).ref
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(cr, uid, partner_default_to).ref))
                if data_found:
                    result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    partner_input_from_str = partner_input_from
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_cust + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    partner_input_to_str = partner_input_to
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_cust + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))
                #print val_part
                result['filter_selection'] = '"' + partner_input_from_str + '" - "' + partner_input_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                pr_ids = ''
                if data['form']['partner_ids']:
                    for pr in  res_partner_obj.browse(cr, uid, data['form']['partner_ids']):
                        pr_ids += '"' + str(pr.ref) + '",'
                    partner_ids = data['form']['partner_ids']
                result['filter_selection'] = '[' + pr_ids +']'
                
        elif data_search == 'name':
            result['data_search'] = 'Customer Name'
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).name:
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).name
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(cr, uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).name:
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).name
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(cr, uid, partner_default_to).name))
                if data_found:
                    result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    partner_input_from_str = partner_input_from
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_cust + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    partner_input_to_str = partner_input_to
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_cust + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                result['filter_selection'] = '"' + partner_input_from_str + '" - "' + partner_input_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                pr_ids = ''
                if data['form']['partner_ids']:
                    for pr in  res_partner_obj.browse(cr, uid, data['form']['partner_ids']):
                        pr_ids += '"' + str(pr.name) + '",'
                    partner_ids = data['form']['partner_ids']
                result['filter_selection'] = '[' + pr_ids +']'
        result['partner_ids'] = partner_ids
        
        #Period
#        result['supp_selection'] = data['form']['supp_selection']

        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#Product Brand
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
            if data_found:
                result['pb_selection'] = '"' + pb_default_from_str + '" - "' + pb_default_to_str + '"'
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'input':
            data_found = False
            if pb_input_from:
                cr.execute("select name " \
                                "from product_brand "\
                                "where " + qry_pb + " and " \
                                "name ilike '" + str(pb_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    pb_input_from_str = product_brand_obj.browse(cr, uid, pb_input_from).name
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if pb_input_to:
                cr.execute("select name " \
                                "from product_brand "\
                                "where " + qry_pb + " and " \
                                "name ilike '" + str(pb_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    pb_input_to_str = product_brand_obj.browse(cr, uid, pb_input_to).name
                    data_found = True
                    val_pb.append(('name', '<=', qry['name']))
            if data_found:
                result['pb_selection'] = '"' + pb_input_from_str + '" - "' + pb_input_to_str + '"'
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['pb_selection'] == 'selection':
            p_ids = ''
            if data['form']['pb_ids']:
                for pb in  product_brand_obj.browse(cr, uid, data['form']['pb_ids']):
                    p_ids += '"' + str(pb.name) + '",'
                pb_ids = data['form']['pb_ids']
            result['pb_selection'] = '[' + p_ids +']'
        result['pb_ids'] = pb_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['customer_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to', \
                                                'pb_selection','pb_default_from','pb_default_to', 'pb_input_from','pb_input_to','pb_ids' \
                                                ], context=context)[0]
        for field in ['customer_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                    'date_selection', 'date_from', 'date_to', \
                    'pb_selection','pb_default_from','pb_default_to', 'pb_input_from','pb_input_to','pb_ids'\
                    ]:
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
        grand_qty = grand_total_selling_price = 0.00
        
        partner_ids = form['partner_ids'] or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND ai.partner_id = " + str(partner_ids[0]) + " ") or "AND ai.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND ai.partner_id IN (0) "

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And ai.date_invoice <= '" + str(date_to) + "' " or " "

        pb_ids = form['pb_ids'] or False
        pb_qry = (pb_ids and ((len(pb_ids) == 1 and "AND pb.id = " + str(pb_ids[0]) + " ") or "AND pb.id IN " + str(tuple(pb_ids)) + " ")) or "AND pb.id IN (0) "
        data_search = form['data_search']
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Monthly Sale Report' + " \n"
        header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing']) + "\n") or ''
        
        header += ('pb_selection' in form and 'Product Brand : ' + form['pb_selection'] + "\n") or ''
        header += 'CUSTOMER;CUST LINE ITEM;INVENTORY KEY;CURRENCY;SELLING PRICE US$;QTY;BRAND;TOTAL SELLING US$;INV. DATE;SALES ZONES' + " \n"
        
        cr.execute("select distinct rp.id as partner_id from account_invoice ai " \
                "inner join account_invoice_line ail on ail.invoice_id = ai.id " \
                "left join res_partner rp on ai.partner_id = rp.id " \
                "left join product_template pt on pt.id = ail.product_id " \
                "left join product_product pp on pp.id = ail.product_id " \
                "left join product_brand pb on pp.brand_id = pb.id " \
                "left join res_partner_sales_zone sz on sz.id = ai.sales_zone_id " \
                "where ai.type in ('out_invoice', 'out_refund') and ai.state in ('open', 'paid') and ail.product_id is not null " \
                    + partner_qry \
                    + date_from_qry \
                    + date_to_qry \
                    + pb_qry)
        partner_ids_vals = []
        qry1 = cr.dictfetchall()
        if qry1:
            for r in qry1:
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
                header += '[' + s['ref'] + '] ' + str(s['name']) + ' \n'
                cr.execute("select rp.name as cust_name, pt.name as inv_key, ail.price_unit as selling_price, " \
                       "ail.quantity as quantity, ail.price_unit * ail.quantity as total_selling, " \
                       "pb.name as brand_name, ai.date_invoice as inv_date, sz.name as sales_zone, rc.name as curr_name, ai.type as type from account_invoice ai " \
                       "inner join account_invoice_line ail on ail.invoice_id = ai.id " \
                       "left join res_currency rc on rc.id = ai.currency_id " \
                       "left join res_partner rp on ai.partner_id = rp.id " \
                       "left join product_template pt on pt.id = ail.product_id " \
                       "left join product_product pp on pp.id = ail.product_id " \
                       "left join product_brand pb on pp.brand_id = pb.id " \
                       "left join res_partner_sales_zone sz on sz.id = ai.sales_zone_id " \
                       "where ai.type in ('out_invoice', 'out_refund') and ai.state in ('open', 'paid') and ail.product_id is not null " \
                       + partner_qry \
                       + date_from_qry \
                       + date_to_qry \
                       + pb_qry \
                       + "and rp.id = " + str(s['id']) + " "\
                       + "order by cust_name, inv_date, brand_name")
                partner_ids_vals = []
                qry3 = cr.dictfetchall()
                sub_qty = sub_total_selling_price = 0.00
                if qry3:
                    qty = selling_price = total_selling_price = 0.00
                    for rs in qry3:
                        sign = 1
                        if rs['type'] == 'out_refund':
                            sign = -1
                        selling_price = round(rs['selling_price'] or 0.00,6) * sign
                        qty = (rs['quantity'] or 0) * sign
                        total_selling_price = round(rs['total_selling'] or 0.00,2) * sign
                
                        sub_qty += qty
                        sub_total_selling_price +=  total_selling_price

                        header += str(rs['cust_name'] or '') + ';;' + str(rs['inv_key'] or '') + ';' + str(rs['curr_name'] or '') + ';' + str(selling_price) + ';' \
                         + str(qty) + ';' + str("%.2f" % total_selling_price) + ';' + str(rs['brand_name'] or '') + ';' + str(rs['inv_date'] or '') + ';' \
                         + str(rs['sales_zone']) + ' \n'
                    header += ';;;;' + 'Sub Total :;' + str(sub_qty or 0.00) + ';' + str(sub_total_selling_price or 0.00) + ' \n'
                    grand_qty += sub_qty
                    grand_total_selling_price += round(sub_total_selling_price,6)
            header += ';;;;' + 'Grand Total :;' + str(grand_qty or 0.00) + ';' + str(grand_total_selling_price or 0.00) + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Monthly Sale Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','monthly_sale_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Monthly Sale Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.monthly.sale.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_monthly_sale_report()

class monthly_sale(osv.osv):
    _inherit = "sale.order.line"
    _description = "Sale Order Line"

    def _qty_oustanding(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        stock_move_obj = self.pool.get("stock.move")
        product_uom_obj = self.pool.get("product.uom")
        qty_oustanding = 0.00
        for obj in self.browse(cr, uid, ids, context=context):
            qty_delivery = 0
            move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',obj.id),('state','=','done')])
            if move_ids:
                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
            res[obj.id] = obj.product_qty - qty_delivery
        return res

    _columns = {
        'oustanding_qty': fields.function(_qty_oustanding, type='float', string='Total oustanding_qty'),
    }

monthly_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
