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

class param_so_oustanding_report(osv.osv_memory):
    _name = 'param.so.oustanding.report'
    _description = 'Param SO Oustanding Report'
    _columns = {
        'customer_search_vals': fields.selection([('code','Customer Code'),('name', 'Customer Name')],'Customer Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Cust Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Customer From', domain=[('customer','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Customer To', domain=[('customer','=',True)], required=False),
        'partner_input_from': fields.char('Customer From', size=128),
        'partner_input_to': fields.char('Customer To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_oustanding_customer_rel', 'report_id', 'partner_id', 'Customer', domain=[('customer','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'so_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'SO Filter Selection', required=True),
        'so_default_from':fields.many2one('sale.order', 'SO From', domain=[('state','=','progress')], required=False),
        'so_default_to':fields.many2one('sale.order', 'SO To', domain=[('state','=','progress')], required=False),
        'so_input_from': fields.char('SO From', size=128),
        'so_input_to': fields.char('SO To', size=128),
        'so_ids' :fields.many2many('sale.order', 'report_oustanding_so_rel', 'report_id', 'so_id', 'Sale Order', domain=[('state','=','progress')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d')
        'date_selection': 'none_sel',
        'customer_search_vals': 'code',
        'filter_selection': 'all_vall',
        'so_selection': 'all_vall',
    }
    
    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.so.oustanding.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'so.oustanding.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        sale_order_obj = self.pool.get('sale.order')
        period_obj = self.pool.get('account.period')
        qry_cust = ''
        val_part = []
        qry_so = ''
        val_so = []
    
        partner_ids = False
        so_ids = False
        data_search = data['form']['customer_search_vals']
        
        qry_cust = 'customer = True'
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

#sale order
        qry_so = 'state = "progress"'
        val_so.append(('state','=', 'progress'))

        so_default_from = data['form']['so_default_from'] or False
        so_default_to = data['form']['so_default_to'] or False
        so_input_from = data['form']['so_input_from'] or False
        so_input_to = data['form']['so_input_to'] or False
        so_default_from_str = so_default_to_str = ''
        so_input_from_str = so_input_to_str= ''
        
        if data['form']['so_selection'] == 'all_vall':
            so_ids = sale_order_obj.search(cr, uid, val_so, order='name ASC')
        if data['form']['so_selection'] == 'def':
            data_found = False
            if so_default_from and sale_order_obj.browse(cr, uid, so_default_from) and sale_order_obj.browse(cr, uid, so_default_from).name:
                so_default_from_str = sale_order_obj.browse(cr, uid, so_default_from).name
                data_found = True
                val_so.append(('name', '>=', sale_order_obj.browse(cr, uid, so_default_from).name))
            if so_default_to and sale_order_obj.browse(cr, uid, so_default_to) and sale_order_obj.browse(cr, uid, so_default_to).name:
                so_default_to_str = sale_order_obj.browse(cr, uid, so_default_to).name
                data_found = True
                val_so.append(('name', '<=', sale_order_obj.browse(cr, uid, so_default_to).name))
            if data_found:
                result['so_selection'] = '"' + so_default_from_str + '" - "' + so_default_to_str + '"'
                so_ids = sale_order_obj.search(cr, uid, val_so, order='name ASC')
        elif data['form']['so_selection'] == 'input':
            data_found = False
            if so_input_from:
                cr.execute("select name " \
                                "from sale_order "\
                                "where " + qry_so + " and " \
                                "name ilike '" + str(so_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    so_input_from_str = sale_order_obj.browse(cr, uid, so_input_from).name
                    data_found = True
                    val_so.append(('name', '>=', qry['name']))
            if so_input_to:
                cr.execute("select name " \
                                "from sale_order "\
                                "where " + qry_so + " and " \
                                "name ilike '" + str(so_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    so_input_to_str = sale_order_obj.browse(cr, uid, so_input_to).name
                    data_found = True
                    val_so.append(('name', '<=', qry['name']))
            if data_found:
                result['so_selection'] = '"' + so_input_from_str + '" - "' + so_input_to_str + '"'
                so_ids = sale_order_obj.search(cr, uid, val_so, order='name ASC')
        elif data['form']['so_selection'] == 'selection':
            s_ids = ''
            if data['form']['so_ids']:
                for so in  sale_order_obj.browse(cr, uid, data['form']['so_ids']):
                    s_ids += '"' + str(so.name) + '",'
                so_ids = data['form']['so_ids']
            result['so_selection'] = '[' + s_ids +']'
        result['so_ids'] = so_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['customer_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to', \
                                                'so_selection','so_default_from','so_default_to', 'so_input_from','so_input_to','so_ids' \
                                                ], context=context)[0]
        for field in ['customer_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                    'date_selection', 'date_from', 'date_to', \
                    'so_selection','so_default_from','so_default_to', 'so_input_from','so_input_to','so_ids'\
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
        oustanding = 0
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        sol_obj = self.pool.get('sale.order.line')

        partner_ids = form['partner_ids'] or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND so.partner_id = " + str(partner_ids[0]) + " ") or "AND so.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND so.partner_id IN (0) "

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And so.date_order >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And so.date_order <= '" + str(date_to) + "' " or " "

        so_ids = form['so_ids'] or False
        so_qry = (so_ids and ((len(so_ids) == 1 and "AND so.id = " + str(so_ids[0]) + " ") or "AND so.id IN " + str(tuple(so_ids)) + " ")) or "AND so.id IN (0) "
        data_search = form['data_search']
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Customer Delivery Outstanding Sale Order' + " \n"
        header += ('filter_selection' in form and 'Customer search  ;' + form['filter_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing']) + "\n") or ''
        
        header += ('so_selection' in form and 'SO : ' + form['so_selection'] + "\n") or ''
        header += 'Customer Key;Customer Name;SO Number;Item Description;Order Qty(PCS);Unit Price;Oustanding Qty' + " \n"

        cr.execute(
            "SELECT sol.id as line_id, pt.name as prod_name, so.name as so_name, rp.name as rp_name, rp.ref as rp_ref, " \
            "(sol.product_uom_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id group by sm.product_id),0)) as oustanding " \
            "FROM sale_order_line sol " \
            "LEFT JOIN sale_order so on sol.order_id = so.id " \
            "LEFT JOIN res_partner rp on so.partner_id = rp.id " \
            "LEFT JOIN product_template pt on sol.product_id = pt.id " \
            "WHERE so.state IN ('progress') " \
            "And (sol.product_uom_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id group by sm.product_id),0)) > 0 " \
            + partner_qry \
            + date_from_qry \
            + date_to_qry \
            + so_qry + \
            "order by so.name")
        qry3 = cr.dictfetchall()

        if qry3:
            for t in qry3:
                sol = sol_obj.browse(cr, uid, t['line_id'])
                header += str(t['rp_name'] or '') + ";" + str(t['rp_ref'] or '') + ";" + str(t['so_name'] or '') + ";" \
                + str(t['prod_name'] or '') + ";" + str(sol.product_uom_qty or 0.00) \
                + ";" + str(sol.price_unit or 0.00)+ ";" + str(t['oustanding'] or 0.00) + " \n"

                oustanding += (t['oustanding'] or 0)
        header += "Report Total;;;;;;;" + str(oustanding)  + " \n"

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'SO Outstanding Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','so_outstanding_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'SO Outstanding Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.so.oustanding.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_so_oustanding_report()

class sale_order_line(osv.osv):
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

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
