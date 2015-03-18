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

import time
from lxml import etree

from osv import fields, osv
from tools.translate import _
import pooler

import copy
from operator import itemgetter
import datetime
from report import report_sxw
from mx import DateTime
import base64

class goods_received_from_supplier_report(osv.osv_memory):
    _name = 'goods.received.from.supplier.report'
    _description = 'Goods Received From Supplier Report'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Product Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Product Brand From', domain=[], required=False),
        'brand_default_to':fields.many2one('product.brand', 'Product Brand To', domain=[], required=False),
        'brand_input_from': fields.char('Product Brand From', size=128),
        'brand_input_to': fields.char('Product Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_goods_received_brand_rel', 'report_id', 'brand_id', 'Product Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
#        'date_from': fields.date("From Date", required=True),
#        'date_to': fields.date("To Date", required=True),
#        'brand_ids': fields.many2many('product.brand', 'po_brand_rel', 'po_id', 'brand_id', 'Product Brand', required=True),
#        'data': fields.binary('Exported CSV', readonly=True),
#        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
       'date_selection':'none_sel',
       'brand_selection':'all_vall',
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['brand_selection','brand_default_from','brand_default_to', 'brand_input_from', \
                                                'brand_input_to','brand_ids', 'date_selection', 'date_from', 'date_to'], context=context)[0]
        
        for field in ['brand_selection','brand_default_from','brand_default_to', 'brand_input_from', \
                                                'brand_input_to','brand_ids', 'date_selection', 'date_from', 'date_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
                
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        product_brand_obj = self.pool.get('product.brand')
        qry_supp = ''
        val_part = []
        qry_pb = ''
        val_pb = []
        
        partner_ids = False
        brand_ids = False
        #Date
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#Product Brand
        brand_default_from = data['form']['brand_default_from'] and data['form']['brand_default_from'] or False
        brand_default_to = data['form']['brand_default_to'] and data['form']['brand_default_to'] or False
        brand_input_from = data['form']['brand_input_from'] or False
        brand_input_to = data['form']['brand_input_to'] or False
        brand_default_from_str = brand_default_to_str = ''
        brand_input_from_str = brand_input_to_str = ''

        if data['form']['brand_selection'] == 'all_vall':
            brand_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        if data['form']['brand_selection'] == 'def':
            data_found = False
            if brand_default_from and product_brand_obj.browse(cr, uid, brand_default_from) and product_brand_obj.browse(cr, uid, brand_default_from).name:
                brand_default_from_str = product_brand_obj.browse(cr, uid, brand_default_from).name
                data_found = True
                val_pb.append(('name', '>=', product_brand_obj.browse(cr, uid, brand_default_from).name))
            if brand_default_to and product_brand_obj.browse(cr, uid, brand_default_to) and product_brand_obj.browse(cr, uid, brand_default_to).name:
                brand_default_to_str = product_brand_obj.browse(cr, uid, brand_default_to).name
                data_found = True
                val_pb.append(('name', '<=', product_brand_obj.browse(cr, uid, brand_default_to).name))
            result['pb_selection'] = '"' + brand_default_from_str + '" - "' + brand_default_to_str + '"'
            if data_found:
                brand_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
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
            #print val_part
            result['pb_selection'] = '"' + brand_input_from_str + '" - "' + brand_input_to_str + '"'
            if data_found:
                brand_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['brand_selection'] == 'selection':
            pb_ids = ''
            if data['form']['brand_ids']:
                for pb in  product_brand_obj.browse(cr, uid, data['form']['brand_ids']):
                    pb_ids += '"' + str(pb.name) + '",'
                brand_ids = data['form']['brand_ids']
            result['pb_selection'] = '[' + pb_ids +']'
        result['brand_ids'] = brand_ids
        
        return result

    def get_date_range(self,cr, uid,form):
        
        start_date = form['date_from']
        end_date = form['date_to']
        date_period = str(start_date) + " To " + str(end_date)
        return date_period

    def _get_tplines(self, cr, uid, ids,data, context):
        res={}
        pool = pooler.get_pool(cr.dbname)
        form = data
        if not ids:
        	ids = data['ids']
        if not ids:
        	return []
        
        brand_ids = form['brand_ids'] or False
        brand_qry = (brand_ids and ((len(brand_ids) == 1 and "AND pbd.id = " + str(brand_ids[0]) + " ") or "AND pbd.id IN " + str(tuple(brand_ids)) + " ")) or "AND pbd.id IN (0) "
        
#        code_from = form['partner_code_from']
#        code_to = form['partner_code_to']
        res_partner_obj = self.pool.get('res.partner')
        
        date_from = form['date_from'] or False
        date_to =  form['date_to'] or False
        date_from_qry = date_from and "And picking.date_done >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And picking.date_done <= '" + str(date_to) + "' " or " "
        
        cr.execute("SELECT picking.date_done,picking.name as grn_no,pbd.name as brand_name,prd.default_code,"\
                    "pmove.product_qty as qty,pbd.name,location.name as location,res_partner.name as supp_name,pmove.price_unit "\
                    "FROM stock_move as pmove "\
                    "inner join stock_picking as picking on picking.id= pmove.picking_id "\
                    "inner join res_partner on res_partner.id= picking.partner_id "\
                    "inner join product_product as prd on prd.id= pmove.product_id "\
                    "inner join product_brand as pbd on pbd.id= prd.brand_id "\
                    "inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
                    "inner join stock_location as location on location.id = pmove.location_dest_id "\
                    "where picking.type = 'in' AND picking.state = 'done' "\
                    + date_from_qry \
                    + date_to_qry \
                    + brand_qry)

        p = cr.dictfetchall()
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Goods Received From Supplier Report' + " \n"
        header += ('pb_selection' in form and 'Product Brand Filter Selection : ' + form['pb_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + form['date_showing'] + "\n") or ''
        header += 'DATE RECEIVE;GRN NO;INVENTORY BRAND;OEM NUMBER;SUPPLIER NAME;QTY;UNIT COST;TOTAL COST;LOCATION KEY' + " \n"
        uprice_total = total_amt = total_qty = 0.00
        for r in p:
            header += str(r['date_done'] or '') + ";" + str(r['grn_no'] or '') + ";" + str(r['brand_name']) + ";" + str(r['default_code']) + ";" \
            + str(r['supp_name']) + ";" + str(r['qty']) + ";" + str(r['price_unit'] or 0.00) + ";" \
            + str((r['qty'] * r['price_unit'] or 0.00)) + ";" + str(r['location']) + " \n"
            uprice_total += r['price_unit'] or 0.00
            sub_total = (r['qty'] * r['price_unit'] or 0.00)
            total_amt += sub_total
            total_qty += r['qty'] or 0
        header += ";;;" + "Grand Total;" + str(total_qty) + ";;" + str(total_amt) + " \n"
        all_content_line += header
        csv_content = ''
        
        filename = 'Goods Received From Supplier Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','goods_received_from_supplier_result_data_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Goods Received From Supplier Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'goods.received.from.supplier.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

goods_received_from_supplier_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
