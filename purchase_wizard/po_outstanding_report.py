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

class po_outstanding_report(osv.osv_memory):
    _name = 'po.outstanding.report'
    _description = 'PO Outstanding Report'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'partner_code_from':fields.many2one('res.partner', 'Supplier Code From', domain=[('supplier','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Supplier Code To', domain=[('supplier','=',True)], required=False),
        'po_from':fields.many2one('purchase.order', 'PO From', required=False),
        'po_to':fields.many2one('purchase.order', 'PO To', required=False),
        'currency_id':fields.many2one('res.currency', 'Currency', required=False),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d')
    }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['partner_code_from'] = 'partner_code_from' in data['form'] and data['form']['partner_code_from'] or False
        result['partner_code_to'] = 'partner_code_to' in data['form'] and data['form']['partner_code_to'] or False
        result['po_from'] = 'po_from' in data['form'] and data['form']['po_from'] or False
        result['po_to'] = 'po_to' in data['form'] and data['form']['po_to'] or False
        result['currency_id'] = 'currency_id' in data['form'] and data['form']['currency_id'] or False
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['partner_code_from', 'partner_code_to', 'po_from', 'po_to','date_from','date_to','currency_id'], context=context)[0]
        for field in ['partner_code_from', 'partner_code_to', 'po_from', 'po_to','currency_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        return self._get_tplines(cr, uid, ids, data, context=context)

    def get_date_range(self,cr, uid,form):
        
		start_date = form['date_from']
		end_date = form['date_to']
		date_period = str(start_date) + " To " + str(end_date)
		return date_period

    def _get_tplines(self, cr, uid, ids,data, context):
		res={}
		pool = pooler.get_pool(cr.dbname)
		form = data['form']
		if not ids:
			ids = data['ids']
		if not ids:
			return []

		date_from = form['date_from']
		date_to =  form['date_to']
		code_from = form['partner_code_from']
		code_to = form['partner_code_to']
		po_from = form['po_from']
		po_to = form['po_to']
		currency_id = form['currency_id']

		po_obj = self.pool.get('purchase.order')
		res_partner_obj = self.pool.get('res.partner')

		part_ref_from = form['partner_code_from'] and res_partner_obj.browse(cr, uid, form['partner_code_from']).ref or False
		part_ref_to = form['partner_code_to'] and res_partner_obj.browse(cr, uid, form['partner_code_to']).ref or False
		query = ''

		if currency_id: 
			query += " AND pprst.currency_id = " + str(currency_id)

		if code_from and part_ref_from:
			query += " AND res_partner.ref >= '" + str(part_ref_from) + "'"
		if code_to and part_ref_to:
			query += " AND res_partner.ref <= '" + str(part_ref_to) + "'"

		if po_from and po_obj.browse(cr, uid, po_from) and po_obj.browse(cr, uid, po_from).name:
			po_name = po_obj.browse(cr, uid, po_from).name
			query += " AND po.name >= '" + str(po_name) + "'"

		if po_to and po_obj.browse(cr, uid, po_to) and po_obj.browse(cr, uid, po_to).name:
			po_name = po_obj.browse(cr, uid, po_to).name
			query += " AND po.name <= '" + str(po_name) + "'"

		cr.execute("SELECT res_partner.name, res_partner.ref,po.name,ptmp.name,pline.estimated_time_departure, "\
			"pline.product_qty,pline.price_unit,po.date_order,pline.estimated_time_arrive,pline.id,pprst.name,buyer.name "\
			"FROM purchase_order_line as pline "\
			"inner join purchase_order as po on po.id= pline.order_id "\
			"inner join res_partner on res_partner.id= po.partner_id "\
			"inner join product_product as prd on prd.id= pline.product_id "\
			"inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
			"inner join product_pricelist as pprst on pprst.id = po.pricelist_id "\
			"left join res_users as buyer on buyer.id = po.buyer_id "\
			"where po.state = 'approved' %s and (po.date_order BETWEEN '%s' and '%s') order by po.name " % (query,date_from,date_to))
		polines = cr.fetchall()


		all_content_line = ''
		header = 'PO Outstanding Between,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		header += 'Supplier Name,Supplier Ref,Order,Part Name,Order Date,Estimated Time Departure,Estimated Time Arrive,Order Qty,Unit Price,Pricelist,Outstanding,Buyer' + " \n"
		acc_ids = []
		for result in polines:
			s_name =  result[0]
			s_name =  s_name.replace(',',' ')
			s_name =  s_name.replace(';',' ')
			s_ref =  result[1]
			order_name = result[2]
			part_name = result[3]
			part_name = part_name.replace(',',' ')
			part_name = part_name.replace(';',' ')
			etd = result[4] or ''
			order_qty = result[5] or 0
			unit_price = result[6]
			order_date = result[7]
			eta = result[8] or ''
			p_id = result[9]
			cr.execute("SELECT sum(product_qty) FROM stock_move where purchase_line_id = %s and state='done' " % (p_id))
			pamt = cr.fetchall()
			received_amt = pamt[0][0] or 0
			#print ":::::", received_amt
			oustanding = order_qty - received_amt
			plist_name =  result[10]
			plist_name =  plist_name.replace(',',' ')
			buyer_name =  result[11]

			header += str(s_name) + "," + str(s_ref) + "," + str(order_name) + "," + str(part_name) + "," + str(order_date) + "," + str(etd) + "," + str(eta)+ "," + str(order_qty) + "," + str(unit_price) + "," + str(plist_name)  + "," + str(oustanding) + "," + str(buyer_name) + "\n"

		all_content_line += header
		csv_content = ''

		filename = 'PO Outstanding Report.csv'
		out = base64.encodestring(all_content_line)
		self.write(cr, uid, ids,{'data':out, 'filename':filename})
		obj_model = self.pool.get('ir.model.data')
		model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','po_outstanding_result_data_view')])
		resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
		return {
		        'name':'PO Outstanding Report',
		        'view_type': 'form',
		        'view_mode': 'form',
		        'res_model': 'po.outstanding.report',
		        'views': [(resource_id,'form')],
		        'type': 'ir.actions.act_window',
		        'target':'new',
	        	'res_id':ids[0],
		        }

po_outstanding_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
