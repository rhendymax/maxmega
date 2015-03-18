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

class so_outstanding_report(osv.osv_memory):
    _name = 'so.outstanding.report'
    _description = 'SO Outstanding Report'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'partner_code_from':fields.many2one('res.partner', 'Customer Code From', domain=[('customer','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Customer Code To', domain=[('customer','=',True)], required=False),
        'so_from':fields.many2one('sale.order', 'SO From', required=False),
        'so_to':fields.many2one('sale.order', 'SO To', required=False),
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
        result['so_from'] = 'so_from' in data['form'] and data['form']['so_from'] or False
        result['so_to'] = 'so_to' in data['form'] and data['form']['so_to'] or False
        result['currency_id'] = 'currency_id' in data['form'] and data['form']['currency_id'] or False
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['partner_code_from', 'partner_code_to', 'so_from', 'so_to','date_from','date_to','currency_id'], context=context)[0]
        for field in ['partner_code_from', 'partner_code_to', 'so_from', 'so_to','currency_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        #used_context = self._build_contexts(cr, uid, ids, data, context=context)
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
		so_from = form['so_from']
		so_to = form['so_to']
		currency_id = form['currency_id']

		so_obj = self.pool.get('sale.order')
		res_partner_obj = self.pool.get('res.partner')

		part_ref_from = form['partner_code_from'] and res_partner_obj.browse(cr, uid, form['partner_code_from']).ref
		part_ref_to = form['partner_code_to'] and res_partner_obj.browse(cr, uid, form['partner_code_to']).ref
		query = ''

		if code_from and part_ref_from:
			query += " AND 'ref' >= " + str(part_ref_from)
		if code_to and part_ref_to:
			query += " AND 'ref' <= " + str(part_ref_to)

		if so_from and so_obj.browse(self.cr, self.uid, so_from) and so_obj.browse(self.cr, self.uid, so_from).name:
			so_name = so_obj.browse(self.cr, self.uid, so_from).name
			query += " AND 'sale_order.name' >= " + str(so_name)

		if so_to and so_obj.browse(self.cr, self.uid, so_to) and so_obj.browse(self.cr, self.uid, so_to).name:
			so_name = so_obj.browse(self.cr, self.uid, so_to).name
			query += " AND 'sale_order.name' <= " + str(so_name)

		cr.execute("SELECT res_partner.name, res_partner.ref,so.name,ptmp.name,so.date_order,"\
			"sline.product_uom_qty,sline.price_unit,sline.customer_rescheduled_date,sline.customer_original_date,sline.effective_date "\
			"FROM sale_order_line as sline "\
			"inner join sale_order as so on so.id= sline.order_id "\
			"inner join res_partner on res_partner.id= so.partner_id "\
			"inner join product_product as prd on prd.id= sline.product_id "\
			"inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
			"inner join product_pricelist as pprst on pprst.id = so.pricelist_id "\
			"where pprst.currency_id = %s and so.state in ('progress','done') and (so.date_order BETWEEN '%s' and '%s') " % (currency_id,date_from,date_to))
		solines = cr.fetchall()

		all_content_line = ''
		header = 'SO Outstanding Between,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		header += 'Partner Name,Partner Ref,Order Number,Part Name,Order Date,Order Qty,Unit Price,Outstanding' + " \n"
		acc_ids = []
		for result in solines:
			s_name =  result[0]
			s_name =  s_name.replace(',',' ')
			s_ref =  result[1]
			order_name = result[2]
			part_name = result[3]
			part_name = part_name.replace(',',' ')
			so_date = result[4]
			order_qty = result[5]
			unit_price = result[6]
			oustanding = 0
			header += str(s_name) + "," + str(s_ref) + "," + str(order_name) + "," + str(part_name) + "," + str(so_date) + "," + str(order_qty) + "," + str(unit_price) + "," + str(oustanding) + "\n"

		all_content_line += header
		csv_content = ''

		filename = 'SO Outstanding Report.csv'
		out = base64.encodestring(all_content_line)
		self.write(cr, uid, ids,{'data':out, 'filename':filename})
		obj_model = self.pool.get('ir.model.data')
		model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','so_outstanding_result_data_view')])
		resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
		return {
		        'name':'SO Outstanding Report',
		        'view_type': 'form',
		        'view_mode': 'form',
		        'res_model': 'so.outstanding.report',
		        'views': [(resource_id,'form')],
		        'type': 'ir.actions.act_window',
		        'target':'new',
	        	'res_id':ids[0],
		        }
so_outstanding_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
