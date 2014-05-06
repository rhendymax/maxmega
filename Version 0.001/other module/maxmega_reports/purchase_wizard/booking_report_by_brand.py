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
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'partner_code_from':fields.many2one('res.partner', 'Customer Code From', domain=[('customer','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Customer Code To', domain=[('customer','=',True)], required=False),
        'brand_ids': fields.many2many('product.brand', 'booking_brand_rel', 'booking_id', 'brand_id', 'Product Brand', required=True),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d')
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['partner_code_from', 'partner_code_to', 'date_from','date_to','brand_ids'], context=context)[0]
        for field in ['partner_code_from', 'partner_code_to','brand_ids']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
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
		brand_ids = form['brand_ids']
		res_partner_obj = self.pool.get('res.partner')

		all_content_line = ''
		header = 'Booking Report By Brand, Date Between,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		#header += 'Date,Customer Name,PO NO,ITEM GROUP,MANUFACTURING PART NUMBER,CUSTOMER PART NO,QUANTITY,SELLING PRICE US$,DELIVERY DATE,TOTAL AMOUNT' + " \n"
		header += 'INVENTORY KEY,COST US$,QUANTITY,TOTAL COST,PURCHASE ORDER DATE,SUPPLIER,PURCHASE ORDER NO' + " \n"
		all_content_line += header
		for brand in pool.get('product.brand').browse(cr, uid, brand_ids):
			cr.execute("SELECT res_partner.name,res_partner.ref,line.ref,line.date, inv.number,pbd.name,prd.default_code, "\
			    "line.quantity,(line.debit-line.credit) as amount,line.amount_currency "\
			    "FROM account_move_line as line "\
			    "inner join account_journal on account_journal.id = line.journal_id "\
			    "inner join account_invoice as inv on inv.move_id = line.move_id "\
			    "inner join res_partner on res_partner.id= line.partner_id "\
			    "inner join product_product as prd on prd.id= line.product_id "\
			    "inner join product_brand as pbd on pbd.id= prd.brand_id "\
			    "inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
			    "WHERE account_journal.type = 'purchase' and pbd.id = %s"\
			    "AND (line.date BETWEEN '%s' and '%s') "\
			    "order by res_partner.name " % (brand.id,date_from,date_to))
			slines = cr.fetchall()

			acc_ids = []
			total_price = brand_total_price = total_qty = 0.00
			header = ""
			if len(slines) > 0:
			    header = "\n" + "INV Brank Key :, " + str(brand.name) + "\n"
			for result in slines:
			    s_name =  result[0]
			    s_name =  s_name.replace(',',' ')
			    s_ref =  result[1]
			    ref = result[2]
			    part_name = result[6]
			    part_name = part_name.replace(',',' ')
			    brand_name = result[5]
			    inv_date = result[3]
			    qty = result[7] or 1
			    total_qty += qty or 1
			    total_price = result[8] or 0.00
			    brand_total_price += total_price
			    unit_price = round((total_price/qty),6)
			    amt_currency = result[9]
			    oustanding = 0
			    header += str(part_name) + "," + str(unit_price) + "," +str(qty) + "," + str(total_price) + "," + str(inv_date) + "," + str(s_name) + "," + str(ref) + "\n"
			if len(slines) > 0:
			    header += ",," + str(total_qty) + "," + str(brand_total_price) + "\n"
			all_content_line += header
			csv_content = ''

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
