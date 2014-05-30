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

class param_allocated_sale_order_checklist_report(osv.osv_memory):
    _name = 'param.allocated.sale.order.checklist.report'
    _description = 'Param Allocated Sale Order Checklist Report'
    _columns = {
        'pp_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'pp_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[], required=False),
        'pp_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[], required=False),
        'pp_input_from': fields.char('Supplier Part No From', size=128),
        'pp_input_to': fields.char('Supplier Part No To', size=128),
        'pp_ids' :fields.many2many('product.product', 'report_sale_checklist_supp_rel', 'report_id', 'pp_id', 'Supplier Part No', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'pp_selection': 'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.allocated.sale.order.checklist.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'allocated.sale.order.checklist.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        product_product_obj = self.pool.get('product.product')
        qry_pp = ''
        val_pp = []
        pp_ids = False

        pp_default_from = data['form']['pp_default_from'] or False
        pp_default_to = data['form']['pp_default_to'] or False
        pp_input_from = data['form']['pp_input_from'] or False
        pp_input_to = data['form']['pp_input_to'] or False
        pp_default_from_str = pp_default_to_str = ''
        pp_input_from_str = pp_input_to_str= ''
        
        if data['form']['pp_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')

        if data['form']['pp_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(cr, uid, pp_default_from) and product_product_obj.browse(cr, uid, pp_default_from).name:
                data_found = True
                pp_default_from_str = product_product_obj.browse(cr, uid, pp_default_from).name
                val_pp.append(('name', '>=', product_product_obj.browse(cr, uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(cr, uid, pp_default_to) and product_product_obj.browse(cr, uid, pp_default_to).name:
                data_found = True
                pp_default_to_str = product_product_obj.browse(cr, uid, pp_default_to).name
                val_pp.append(('name', '<=', product_product_obj.browse(cr, uid, pp_default_to).name))
            if data_found:
                result['pp_selection'] = '"' + pp_default_from_str + '" - "' + pp_default_to_str + '"'
                pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        elif data['form']['pp_selection'] == 'input':
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
        elif data['form']['pp_selection'] == 'selection':
            p_ids = ''
            if data['form']['pp_ids']:
                for pp in  product_product_obj.browse(cr, uid, data['form']['pp_ids']):
                    p_ids += '"' + str(pp.name) + '",'
                pp_ids = data['form']['pp_ids']
            result['pp_selection'] = '[' + p_ids +']'
        result['pp_ids'] = pp_ids
        return result
    
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['pp_selection','pp_default_from','pp_default_to', 'pp_input_from','pp_input_to','pp_ids'], context=context)[0]
        
        for field in ['pp_selection','pp_default_from','pp_default_to', 'pp_input_from','pp_input_to','pp_ids']:
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
        
        
        pp_obj = self.pool.get('product.product')
        pp_ids = form['pp_ids'] or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND pp.id = " + str(pp_ids[0]) + " ") or "AND pp.id IN " + str(tuple(pp_ids)) + " ")) or "AND pp.id IN (0) "
        line_ids = []
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Allocated Sale Order Checklist' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No : ' + form['pp_selection'] + "\n") or ''
        header += 'Sale Order No.;Customer Ref;CPN;Location;Qty;UOM' + " \n"
        
        cr.execute("select  DISTINCT sol.product_id \
                from sale_order_line sol \
                left join product_template pt on sol.product_id = pt.id \
                left join product_product pp on pt.id = pp.id \
                left join product_brand pb on pp.brand_id = pb.id \
                where sol.state not in ('draft','done','cancel') \
                and COALESCE(sol.qty_onhand_allocated, 0) \
                + (select COALESCE(sum(received_qty),0) from sale_allocated where sale_line_id = sol.id) \
                - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
                where sm2.sale_line_id = sol.id and sm2.state = 'done') > 0 " \
                + pp_qry )
#                " order by pb.name, pt.name")
        product_ids_vals = []
        qry = cr.dictfetchall()
        if qry:
            for r in qry:
                product_ids_vals.append(r['product_id'])

        product_ids_vals_qry = (len(product_ids_vals) > 0 and ((len(product_ids_vals) == 1 and "where pp.id = " +  str(product_ids_vals[0]) + " ") or "where pp.id IN " +  str(tuple(product_ids_vals)) + " ")) or "where pp.id IN (0) "

        cr.execute(
                "SELECT pp.id, pt.name, pb.name as brand_name " \
                "FROM product_product pp inner join product_template pt on pp.id = pt.id " \
                "left join product_brand pb on pp.brand_id = pb.id " \
                + product_ids_vals_qry \
                + " order by pt.name")
        qry1 = cr.dictfetchall()
        if qry1:
            for s in qry1:
                cr.execute("select sol.product_id, \
                    pb.name as brand_name, \
                    pt.name as product_name, \
                    so.name as so_name, \
                    rp.ref as customer_ref, \
                    rp.name as customer_name, \
                    pc.name as cpn, \
                    sl.name as location_name, \
                    COALESCE(sol.qty_onhand_allocated, 0) + (select COALESCE(sum(received_qty),0) \
                    from sale_allocated where sale_line_id = sol.id) \
                    - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
                    where sm2.sale_line_id = sol.id and sm2.state = 'done') as qty, \
                    pu.name as uom \
                    from sale_order_line sol \
                    left join product_uom pu on sol.product_uom = pu.id \
                    left join stock_location sl on sol.location_id = sl.id \
                    left join product_customer pc on sol.product_customer_id = pc.id \
                    left join product_template pt on sol.product_id = pt.id \
                    left join product_product pp on pt.id = pp.id \
                    left join product_brand pb on pp.brand_id = pb.id \
                    left join sale_order so on sol.order_id = so.id \
                    left join res_partner rp on so.partner_id = rp.id \
                    where sol.state not in ('draft','done','cancel') \
                    and COALESCE(sol.qty_onhand_allocated, 0) \
                    + (select COALESCE(sum(received_qty),0) from sale_allocated where sale_line_id = sol.id) \
                    - (select COALESCE(sum(sm2.product_qty), 0) from stock_move sm2 \
                    where sm2.sale_line_id = sol.id and sm2.state = 'done') > 0 " \
                    "and sol.product_id = " + str(s['id']) + " "\
                    " order by pb.name, pt.name")

                #Print Group By
                header += str('[' + s['brand_name'] + ']' + s['name'],)  + " \n"
                totalQty = 0
                qry3 = cr.dictfetchall()
                val = []
                if qry3:
                    for t in qry3:
                        header += str(t['so_name'] or '') + ";" + '[' + str(t['customer_ref']) + '] ' + str(t['customer_name']) + ";" \
                        + str(t['cpn'] or '') + ";" + str(t['location_name'] or '') + ";" + str(t['qty'] or '0') + ";" + str(t['uom'] or '')+ "\n"
                        totalQty += (t['qty'] or 0)
                header += "Total for " + str('[' + s['brand_name'] + ']' + s['name'],)  + ";;;; " + str(totalQty or '0')  + " \n"
                header += " \n"

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Allocated Sale Order Check list Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','allocated_sale_order_checklist_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Allocated Sale Order Check list Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.allocated.sale.order.checklist.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_allocated_sale_order_checklist_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
