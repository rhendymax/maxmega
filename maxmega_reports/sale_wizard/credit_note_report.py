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

class maxmega_credit_note_report(osv.osv_memory):
    _name = 'maxmega.credit.note.report'
    _description = 'Credit Note Report'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
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
        data['form'] = self.read(cr, uid, ids, ['date_from','date_to'], context=context)[0]
        #for field in ['brand_ids']:
        #    if isinstance(data['form'][field], tuple):
        #        data['form'][field] = data['form'][field][0]
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
		res_partner_obj = self.pool.get('res.partner')

		cr.execute("SELECT inv.date_invoice,inv.number,res_partner.ref,"\
			"res_partner.name,res_users.name,inv.amount_total "\
			"FROM account_invoice as inv "\
			"inner join res_partner on res_partner.id= inv.partner_id "\
			"left join res_users on res_users.id= res_partner.user_id "\
			"where inv.type = 'out_refund' AND inv.state in ('open','done') "\
			"AND inv.date_invoice BETWEEN '%s' and '%s' " % (date_from,date_to))

		polines = cr.fetchall()

		all_content_line = ''
		header = 'CREDIT NOTE REPORT BETWEEN,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		header += 'C.NOTE DATE,CREDIT NOTE NO.,REFERENCE NO.,CUSTOMER KEY,CUSTOMER NAME,SALES PERSON KEY,NAME,CREDIT AMOUNT' + " \n"
		acc_ids = []
		total_amt = 0.00
		for result in polines:
			date_invoice = result[0]
			inv_number = result[1]
			user_name = result[4] or ''
			customer_name = result[3]
			customer_name = customer_name.replace(',',' ')
			customer_ref = result[2]
			order_amt = result[5] or 0.00
			total_amt += order_amt
			header += str(date_invoice) + "," + str(inv_number) + "," + " " + "," + str(customer_ref) + "," + str(customer_name) + "," + " " + "," + str(user_name) + "," + str(order_amt) + "\n"
		header += ",," + ",," + "" + ",,Grand Total," + str(total_amt) + "\n"
		all_content_line += header
		csv_content = ''

		filename = 'Credit Note Report.csv'
		out = base64.encodestring(all_content_line)
		self.write(cr, uid, ids,{'data':out, 'filename':filename})
		obj_model = self.pool.get('ir.model.data')
		model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','maxmega_credit_note_result_data_view')])
		resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
		return {
		        'name':'Credit Note Report',
		        'view_type': 'form',
		        'view_mode': 'form',
		        'res_model': 'maxmega.credit.note.report',
		        'views': [(resource_id,'form')],
		        'type': 'ir.actions.act_window',
		        'target':'new',
	        	'res_id':ids[0],
		        }

maxmega_credit_note_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
