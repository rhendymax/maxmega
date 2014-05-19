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

class po_issued_report(osv.osv_memory):
    _name = 'po.issued.report'
    _description = 'PO Issued Report'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'po_from':fields.many2one('purchase.order', 'PO From', required=False),
        'po_to':fields.many2one('purchase.order', 'PO To', required=False),
        'brand_ids': fields.many2many('product.brand', 'po_brand_rel', 'po_id', 'brand_id', 'Product Brand', required=True),
        'location_ids': fields.many2many('stock.location', 'po_location_rel', 'po_id', 'location_id', 'Location', required=True),
        'currency_id':fields.many2one('res.currency', 'Currency', required=True),
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
        data['form'] = self.read(cr, uid, ids, ['po_from', 'po_to','date_from','date_to','currency_id','brand_ids','location_ids'], context=context)[0]
        for field in ['po_from', 'po_to','currency_id','brand_ids','location_ids']:
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
		po_from = form['po_from']
		po_to = form['po_to']
		currency_id = form['currency_id']

		po_obj = self.pool.get('purchase.order')
		res_partner_obj = self.pool.get('res.partner')
		query = ''

		if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
			po_name = purchase_order_obj.browse(self.cr, self.uid, po_from).name
			query += " AND 'purchase_order.name' >= " + str(po_name)

		if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
			po_name = purchase_order_obj.browse(self.cr, self.uid, po_to).name
			query += " AND 'purchase_order.name' <= " + str(po_name)

		print ":: query ::",query
		brand_ids = form['brand_ids']
		brands = '(0)'
		if len(brand_ids) == 0:
			raise osv.except_osv(_('Error!'), _('Please select atleast one brand!'))
		elif len(brand_ids) == 1:
			brands = "(" + str(brand_ids[0]) + ")"
		else:
			brands = tuple(brand_ids)

		location_ids = form['location_ids']
		lc_ids = '(0)'
		if len(location_ids) == 0:
			raise osv.except_osv(_('Error!'), _('Please select atleast one Location!'))
		elif len(location_ids) == 1:
			lc_ids = "(" + str(location_ids[0]) + ")"
		else:
			lc_ids = tuple(location_ids)

		cr.execute("SELECT po.name,ptmp.name,prd.default_code,"\
			"pline.product_qty,pline.price_unit,po.date_order,pbd.name,location.name "\
			"FROM purchase_order_line as pline "\
			"inner join purchase_order as po on po.id= pline.order_id "\
			"inner join res_partner on res_partner.id= po.partner_id "\
			"inner join product_product as prd on prd.id= pline.product_id "\
			"inner join product_brand as pbd on pbd.id= prd.brand_id "\
			"inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
			"inner join product_pricelist as pprst on pprst.id = po.pricelist_id "\
			"inner join stock_location as location on location.id = pline.location_dest_id "\
			"where pbd.id in %s AND location.id in %s "\
			"AND pprst.currency_id = %s and po.state = 'approved' and (po.date_order BETWEEN '%s' and '%s') " % (brands,lc_ids,currency_id,date_from,date_to))
		polines = cr.fetchall()

		all_content_line = ''
		header = 'PO Issued Between,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		header += 'P.O No,INV BRAND,OEM NUMBER,COST,QTY,TOTAL COST,P.O DATE,LOCATION KEY' + " \n"
		acc_ids = []
		uprice_total = total_amt = 0.00
		for result in polines:
			order_name = result[0]
			part_name = result[2]
			part_name = part_name.replace(',',' ')
			order_qty = result[3]
			unit_price = result[4] or 0.00
			uprice_total += unit_price
			order_date = result[5]
			brand_name = result[6] or ''
			location = result[7] or ''
			sub_total = order_qty*unit_price
			total_amt += sub_total
			oustanding = 0
			header += str(order_name) + "," + str(brand_name) + "," + str(part_name) + "," + str(unit_price) + "," + str(order_qty) + "," + str(sub_total) + "," + str(order_date) + "," + str(location) + "\n"
		header += ",," + "," + str(uprice_total) + ",," + str(total_amt) + "\n"
		all_content_line += header
		csv_content = ''

		filename = 'PO Issued Report.csv'
		out = base64.encodestring(all_content_line)
		self.write(cr, uid, ids,{'data':out, 'filename':filename})
		obj_model = self.pool.get('ir.model.data')
		model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','po_issued_result_data_view')])
		resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
		return {
		        'name':'PO Issued Report',
		        'view_type': 'form',
		        'view_mode': 'form',
		        'res_model': 'po.issued.report',
		        'views': [(resource_id,'form')],
		        'type': 'ir.actions.act_window',
		        'target':'new',
	        	'res_id':ids[0],
		        }

po_issued_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
