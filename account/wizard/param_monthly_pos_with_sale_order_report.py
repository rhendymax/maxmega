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

class param_monthly_pos_with_sale_order_report(osv.osv_memory):
    _name = 'param.monthly.pos.with.sale.order.report'
    _description = 'Param Monthly POS Report with Sale Order'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'invoice_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Invoice Filter Selection', required=True),
        'invoice_default_from':fields.many2one('account.invoice', 'Invoice From', domain=[('type','=','out_invoice'),('state','in',('open','paid'))], required=False),
        'invoice_default_to':fields.many2one('account.invoice', 'Invoice To', domain=[('type','=','out_invoice'),('state','in',('open','paid'))], required=False),
        'invoice_input_from': fields.char('Invoice From', size=128),
        'invoice_input_to': fields.char('Invoice To', size=128),
        'invoice_ids' :fields.many2many('account.invoice', 'report_monthly_sale_invoice_rel', 'report_id', 'invoice_id', 'Invoice No', domain=[('type','=','out_invoice'),('state','in',('open','paid'))]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }
    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'date_selection': 'none_sel',
        'invoice_selection': 'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.monthly.pos.with.sale.order.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'monthly.pos.with.sale.order.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        account_invoice_obj = self.pool.get('account.invoice')
        qry_supp = ''
        val_part = []
        qry_ai = ''
        val_ai = []
        
        partner_ids = False
        invoice_ids = False

        #invoice
        qry_ai = "type = 'out_invoice' and state in ('open','paid') "
        val_ai.append(('type','=', 'out_invoice'))
        val_ai.append(('state','in', ('open','paid')))
        ai_default_from = data['form']['invoice_default_from'] or False
        ai_default_to = data['form']['invoice_default_to'] or False
        ai_input_from = data['form']['invoice_input_from'] or False
        ai_input_to = data['form']['invoice_input_to'] or False
        ai_default_from_str = ai_default_to_str = ''
        ai_input_from_str = ai_input_to_str= ''
        
        #Date
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'
        
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
                qry = self.cr.dictfetchone()
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

        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['invoice_selection','invoice_default_from','invoice_default_to', 'invoice_input_from', \
                                                'invoice_input_to','invoice_ids', 'date_selection', 'date_from', 'date_to'], context=context)[0]
        
        for field in ['invoice_selection','invoice_default_from','invoice_default_to', 'invoice_input_from', \
                                                'invoice_input_to','invoice_ids', 'date_selection', 'date_from', 'date_to']:
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
        cr = cr
        uid = uid
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And ai.date_invoice <= '" + str(date_to) + "' " or " "

        invoice_ids = form['invoice_ids'] or False
        invoice_qry = (invoice_ids and ((len(invoice_ids) == 1 and "AND ai.id = " + str(invoice_ids[0]) + " ") or "AND ai.id IN " + str(tuple(invoice_ids)) + " ")) or "AND ai.id IN (0) "
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Monthly Pos With Sale Order' + " \n"
        header += ('ai_selection' in form and 'Invoice Filter Selection : ' + form['ai_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + form['date_showing'] + "\n") or ''
        header += 'Date;Invoice No;SO No;Customer PO No;Customer;Location;CPN;MPN;Selling Price;Qty;Total;Brand' + " \n"

        cr.execute("select ai.number as invoice_no, " \
                        "ai.date_invoice as date_inv, " \
                        "so.name as so_no, " \
                        "so.client_order_ref as customer_po_no, " \
                        "sl.name as location, " \
                        "rp.name as customer_name, " \
                        "pc.name as cpn, " \
                        "pt.name as mpn, " \
                        "ail.price_unit as selling_price, " \
                        "ail.quantity as quantity, " \
                        "ail.price_unit * ail.quantity as total, " \
                        "pb.name as brand_name " \
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
                        + date_from_qry \
                        + date_to_qry \
                        + invoice_qry + \
                        "order by ai.date_invoice, invoice_no, brand_name")

        results = cr.dictfetchall()
        gt_selling_price = gt_qty = gt_total = 0
        if results:
            for t in results:
                header += str(t['date_inv'] or '') + ";" + str(t['invoice_no']) + ";" + str(t['so_no'] or '') + ";'" \
                        + str(t['customer_po_no']) + ";" + str(t['customer_name'] or '') + ";" + str(t['location'] or '') + ";" \
                        + str(t['cpn'] or '') + ";" + str(t['mpn'] or '') + ";" + str(t['selling_price'] or 0.00000) + ";" + str(t['quantity'] or 0) + ";"\
                        + str(t['total'] or 0)+ ";" + str(t['brand_name'] or '') + " \n"
                gt_selling_price += t['selling_price'] or 0.00000
                gt_qty += t['quantity'] or 0
                gt_total += t['total'] or 0
            header += ' \n' + 'Grand Total' + ';' + ';' + ';' + ';' + ';' + ';' + ';' + ';' + str(float_round(gt_selling_price,5)) + ';' + str(float_round(gt_qty,0)) \
            + ';' + str(float_round(gt_total,0)) + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Monthly Pos With Sale Order Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','monthly_pos_with_sale_order_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Monthly Pos With Sale Order Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.monthly.pos.with.sale.order.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }
param_monthly_pos_with_sale_order_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
