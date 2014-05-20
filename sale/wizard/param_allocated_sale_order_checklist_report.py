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
        res = {}
        product_product_obj = self.pool.get('product.product')
        qry_pp = ''
        val_pp = []
        pp_ids = False

        pp_default_from = data['form']['pp_default_from'] and data['form']['pp_default_from'][0] or False
        pp_default_to = data['form']['pp_default_to'] and data['form']['pp_default_to'][0] or False
        pp_input_from = data['form']['pp_input_from'] or False
        pp_input_to = data['form']['pp_input_to'] or False

        if data['form']['pp_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')

        if data['form']['pp_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(self.cr, self.uid, pp_default_from) and product_product_obj.browse(self.cr, self.uid, pp_default_from).name:
                data_found = True
                val_pp.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(self.cr, self.uid, pp_default_to) and product_product_obj.browse(self.cr, self.uid, pp_default_to).name:
                data_found = True
                val_pp.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, pp_default_to).name))
            if data_found:
                pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')
        elif data['form']['pp_selection'] == 'input':
            data_found = False
            if pp_input_from:
                self.cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '>=', qry['name']))
            if pp_input_to:
                self.cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '<=', qry['name']))
            if data_found:
                pp_ids = product_product_obj.search(self.cr, self.uid, val_pp, order='name ASC')
        elif data['form']['pp_selection'] == 'selection':
            if data['form']['pp_ids']:
                pp_ids = data['form']['pp_ids']
        self.pp_ids = pp_ids
        return result
    
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to', \
                                                'po_selection','po_default_from','po_default_to', 'po_input_from','po_input_to','po_ids' \
                                                ], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                    'date_selection', 'date_from', 'date_to', \
                    'po_selection','po_default_from','po_default_to', 'po_input_from','po_input_to','po_ids'\
                    ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_tplines(self, cr, uid, ids,data, context):
        res={}
        pool = pooler.get_pool(cr.dbname)
        
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        oustanding = 0
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        pol_obj = self.pool.get('purchase.order.line')

        partner_ids = form['partner_ids'] or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND po.partner_id = " + str(partner_ids[0]) + " ") or "AND po.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND po.partner_id IN (0) "

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And po.date_order >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And po.date_order <= '" + str(date_to) + "' " or " "

        po_ids = form['po_ids'] or False
        po_qry = (po_ids and ((len(po_ids) == 1 and "AND po.id = " + str(po_ids[0]) + " ") or "AND po.id IN " + str(tuple(po_ids)) + " ")) or "AND po.id IN (0) "

        all_content_line = ''
        header = 'Supplier Delivery Outstanding Purchase Order' + " \n"
        header += 'Supplier Key;Supplier Name;PO Number;Item Description;ETD Date;Order Qty(PCS);Unit Price;Oustanding Qty' + " \n"

        cr.execute(
            "SELECT pol.id as line_id, pt.name as prod_name, po.name as po_name, rp.name as rp_name, rp.ref as rp_ref, " \
            "(pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) as oustanding " \
            "FROM purchase_order_line pol " \
            "LEFT JOIN purchase_order po on pol.order_id = po.id " \
            "LEFT JOIN res_partner rp on po.partner_id = rp.id " \
            "LEFT JOIN product_template pt on pol.product_id = pt.id " \
            "WHERE po.state IN ('approved') " \
            "And (pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) > 0 " \
            + partner_qry \
            + date_from_qry \
            + date_to_qry \
            + po_qry + \
            "order by po.name")
        qry3 = cr.dictfetchall()

        if qry3:
            for t in qry3:
                pol = pol_obj.browse(cr, uid, t['line_id'])
                header += str(t['rp_name'] or '') + ";" + str(t['rp_ref'] or '') + ";" + str(t['po_name'] or '') + ";" + str(t['prod_name'] or '') + ";" + str(pol.estimated_time_departure or '') + ";" + str(pol.product_qty or 0.00) + ";" + str(pol.price_unit or 0.00)+ ";" + str(t['oustanding'] or 0.00) + "\n"

                oustanding += (t['oustanding'] or 0)
        header += "Report Total;;;;;;;" + str(oustanding)  + " \n"

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'PO Outstanding Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','po_outstanding_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'PO Outstanding Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.po.oustanding.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_allocated_sale_order_checklist_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
