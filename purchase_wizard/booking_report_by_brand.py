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

class booking_report_by_brand(osv.osv_memory):
    _name = 'booking.report.by.brand'
    _description = 'Booking Report By Brand'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Product Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Product Brand From', domain=[], required=False),
        'brand_default_to':fields.many2one('product.brand', 'Product Brand To', domain=[], required=False),
        'brand_input_from': fields.char('Product Brand From', size=128),
        'brand_input_to': fields.char('Product Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_booking_brand_rel', 'report_id', 'brand_id', 'Product Brand', domain=[]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
#        'date_from': fields.date("From Date", required=True),
#        'date_to': fields.date("To Date", required=True),
#        'partner_code_from':fields.many2one('res.partner', 'Customer Code From', domain=[('customer','=',True)], required=False),
#        'partner_code_to':fields.many2one('res.partner', 'Customer Code To', domain=[('customer','=',True)], required=False),
#        'brand_ids': fields.many2many('product.brand', 'booking_brand_rel', 'booking_id', 'brand_id', 'Product Brand', required=True),
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
        brand_default_from = data['form']['brand_default_from'] and data['form']['brand_default_from'][0] or False
        brand_default_to = data['form']['brand_default_to'] and data['form']['brand_default_to'][0] or False
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
                                "where " + qry_pb + " and " \
                                "name ilike '" + str(brand_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if brand_input_to:
                brand_input_to_str = brand_input_to
                cr.execute("select name " \
                                "from product_brand "\
                                "where " + qry_pb + " and " \
                                "name ilike '" + str(brand_input_to) + "%' " \
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
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        cr = cr
        uid = uid
        res={}
        pool = pooler.get_pool(cr.dbname)

        date_from = form['date_from'] or False
        date_to =  form['date_to'] or False
        date_from_qry = date_from and "And po.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And po.date <= '" + str(date_to) + "' " or " "

        brand_ids = form['brand_ids'] or False
        brand_qry = (brand_ids and ((len(brand_ids) == 1 and "AND pbd.id = " + str(brand_ids[0]) + " ") or "AND pbd.id IN " + str(tuple(brand_ids)) + " ")) or "AND pbd.id IN (0) "

#        code_from = form['partner_code_from']
#        code_to = form['partner_code_to']
        brand_ids = form['brand_ids']
        res_partner_obj = self.pool.get('res.partner')
        account_invoice_obj = self.pool.get('account.invoice')
        gt_total_price = gt_brand_total = gt_total_qty = 0
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Booking Report By Brand' + " \n"
        header += ('pb_selection' in form and 'Product Brand Filter Selection : ' + form['pb_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + form['date_showing'] + "\n") or ''
        #header += 'Date,Customer Name,PO NO,ITEM GROUP,MANUFACTURING PART NUMBER,CUSTOMER PART NO,QUANTITY,SELLING PRICE US$,DELIVERY DATE,TOTAL AMOUNT' + " \n"
        header += 'INVENTORY KEY;COST US$;QUANTITY;TOTAL COST;PURCHASE ORDER DATE;SUPPLIER;GRN NO;PO NO' + " \n"

        cr.execute("SELECT DISTINCT pbd.id as brand_id "\
            "from account_invoice_line ail " \
            "inner join product_template pt on pt.id = ail.product_id " \
            "left join account_invoice ai on ail.invoice_id = ai.id " \
            "left join res_partner rp on rp.id = ai.partner_id " \
            "left join stock_move as sm on sm.id = ail.stock_move_id " \
            "left join stock_picking as sp on sp.id = sm.picking_id " \
            "left join purchase_order_line as pol on pol.id = sm.purchase_line_id " \
            "left join purchase_order as po on po.id = pol.order_id " \
            "left join product_product as pp on pp.id= pt.id " \
            "left join product_brand as pbd on pbd.id= pp.brand_id " \
            "where ai.state in ('open', 'paid') and ai.type = 'in_invoice' " \
            + date_from_qry \
            + date_to_qry \
            + brand_qry)
        
        brand_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                brand_ids_vals.append(r['brand_id'])
        brand_ids_vals_qry = (len(brand_ids_vals) > 0 and ((len(brand_ids_vals) == 1 and "where id = " + str(brand_ids_vals[0]) + " ") or "where id IN " + str(tuple(brand_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT name, id " \
                "FROM product_brand " \
                + brand_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                header += "INV Brank Key : " + str(s['name']) + "\n"
        #        for brand in pool.get('product.brand').browse(cr, uid, brand_ids):
                cr.execute("select ail.quantity as qty, ai.id as invoice_id, rp.name as part_name, rp.ref as ref_partner, po.name as po_name, sp.name as grn_name, po.date_order as po_date, " \
                    "ai.number, pbd.name as pbd_name, pp.default_code as default_code, ail.price_unit as price_unit "\
                    "from account_invoice_line ail " \
                    "inner join product_template pt on pt.id = ail.product_id " \
                    "left join account_invoice ai on ail.invoice_id = ai.id " \
                    "left join res_partner rp on rp.id = ai.partner_id " \
                    "left join stock_move as sm on sm.id = ail.stock_move_id " \
                    "left join stock_picking as sp on sp.id = sm.picking_id " \
                    "left join purchase_order_line as pol on pol.id = sm.purchase_line_id " \
                    "left join purchase_order as po on po.id = pol.order_id " \
                    "left join product_product as pp on pp.id= pt.id " \
                    "left join product_brand as pbd on pbd.id= pp.brand_id " \
                    "where ai.state in ('open', 'paid') and ai.type = 'in_invoice' " \
                    + date_from_qry \
                    + date_to_qry \
                    + "and pbd.id = " + str(s['id']) + " " \
                    + "order by rp.name")
                slines = cr.dictfetchall()
                total_price = total_amount = brand_total_price = total_qty = 0
                if len(slines) > 0:
                    for result in slines:
                        rate = account_invoice_obj.browse(cr, uid, result['invoice_id']).cur_rate
                        price_unit = result['price_unit']
                        price_unit_home = round((price_unit/rate),6)
                        total_amt = round((result['price_unit'] * result['qty'])/rate,2)
                        header += str(result['default_code'] or '') + ";" + str(price_unit_home) + ";" \
                        + str(result['qty'] or 1) + ";" + str(total_amt) + ";" + str(result['po_date'] or '') + ";" \
                        + str(result['part_name'] or '') + ";" + str(result['grn_name'] or '') + ";" + str(result['po_name'] or '') + "\n"
                        qty = result['qty'] or 1
                        total_qty += qty or 1
                        brand_total_price += total_amt
                        gt_total_price += price_unit
                    gt_total_qty += total_qty
                    gt_brand_total += brand_total_price
                if len(slines) > 0:
                    header += ";;" + str(total_qty) + ";" + str(brand_total_price) + "\n"
        header += "Grand Total" + ";" + str(gt_total_price) + ";" + str(gt_total_qty) + ";" + str(gt_brand_total) + "\n"
        all_content_line += header


        filename = 'Booking Report By Brand.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','booking_report_by_brand_result_data_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Booking Report By Brand',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'booking.report.by.brand',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }
booking_report_by_brand()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
