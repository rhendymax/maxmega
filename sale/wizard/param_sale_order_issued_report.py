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
import pooler
import base64
import time

class param_sale_order_issued_report(osv.osv_memory):
    _name = 'param.sale.order.issued.report'
    _description = 'Param Sale Order Issued Report'
    _columns = {
        'cust_search_vals': fields.selection([('code','Customer Code'),('name', 'Customer Name')],'Customer Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Customer Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Customer From', domain=[('customer','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Customer To', domain=[('customer','=',True)], required=False),
        'partner_input_from': fields.char('Customer From', size=128),
        'partner_input_to': fields.char('Customer To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_sale_issued_cust_rel', 'report_id', 'partner_id', 'Customer', domain=[('customer','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
}

    _defaults = {
        'date_selection': 'none_sel',
        'cust_search_vals': 'code',
        'filter_selection': 'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.sale.order.issued.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'sale.order.issued.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        res_partner_obj = self.pool.get('res.partner')
        qry_supp = ''
        val_part = []
        partner_ids = False

        data_search = data['form']['cust_search_vals']

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
                    data_found = True
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).ref
                    val_part.append(('ref', '<=', res_partner_obj.browse(cr, uid, partner_default_to).ref))
                result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    partner_input_from_str = partner_input_from
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
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
                                    "where " + qry_supp + " and " \
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
                    data_found = True
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).name
                    val_part.append(('name', '>=', res_partner_obj.browse(cr, uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).name:
                    data_found = True
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).name
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
                                    "where " + qry_supp + " and " \
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
                                    "where " + qry_supp + " and " \
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

        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['cust_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to'], context=context)[0]
        
        for field in ['cust_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to']:
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
        date_from_qry = date_from and "And so.date_order >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And so.date_order <= '" + str(date_to) + "' " or " "

        partner_ids = form['partner_ids'] or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND rp.id = " + str(partner_ids[0]) + " ") or "AND rp.id IN " + str(tuple(partner_ids)) + " ")) or "AND rp.id IN (0) "
        data_search = form['data_search']
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Sale Order Issued' + " \n"
        
        header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing'])+ "\n") or ''
        
        header += 'Sale Order No;Sale Order Date;Customer PO No;Unit Price;Qty;Total Sell;Location;Customer Code;Customer Name;Customer Part No;Part No;Brand' + " \n"
        cr.execute("select so.name as so_no, " \
                        "so.date_order as so_date, " \
                        "so.client_order_ref as customer_po_no, " \
                        "sol.price_unit as unit_price, " \
                        "sol.product_uom_qty as qty, " \
                        "sol.price_unit * sol.product_uom_qty as total, " \
                        "sl.name as location, " \
                        "rp.ref as partner_ref, " \
                        "rp.name as partner_name, " \
                        "pc.name as customer_part_no, " \
                        "pt.name as part_no, " \
                        "pb.name as brand " \
                        "from sale_order so " \
                        "inner join sale_order_line sol on so.id = sol.order_id " \
                        "left join stock_location sl on sol.location_id = sl.id " \
                        "left join res_partner rp on so.partner_id = rp.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "left join product_template pt on sol.product_id2 = pt.id " \
                        "left join product_product pp on sol.product_id2 = pp.id " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "WHERE so.state in ('progress','done') " \
                        + date_from_qry \
                        + date_to_qry \
                        + partner_qry + \
                        " order by so.name")
        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                header += str(t['so_no'] or '') + ";" + str(t['so_date'] or '') + ";" + str(t['customer_po_no'] or '') + ";" + str(t['unit_price'] or 0.00) + ";"\
                        + str(t['qty'] or 0.00) + ";"  + str(t['total'] or 0.00) + ";" + str(t['location'] or '') + ";" + str(t['partner_ref'] or '') + ";"\
                        + str(t['partner_name'] or '') + ";" + str(t['customer_part_no'] or '')+ ";" + str(t['part_no'] or '') + ";" + str(t['brand'] or '') + "\n"

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Sale Order Issued Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','sale_order_issued_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Sale Order Issued Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.sale.order.issued.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_sale_order_issued_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
