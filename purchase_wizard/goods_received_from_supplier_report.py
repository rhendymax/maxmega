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
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'brand_ids': fields.many2many('product.brand', 'po_brand_rel', 'po_id', 'brand_id', 'Product Brand', required=True),
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
        data['form'] = self.read(cr, uid, ids, ['date_from','date_to','brand_ids'], context=context)[0]
        for field in ['brand_ids']:
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
		res_partner_obj = self.pool.get('res.partner')
		query = ''
		brand_ids = form['brand_ids']
		brands = '(0)'
		if len(brand_ids) == 0:
			raise osv.except_osv(_('Error!'), _('Please select atleast one brand!'))
		elif len(brand_ids) == 1:
			brands = "(" + str(brand_ids[0]) + ")"
		else:
			brands = tuple(brand_ids)

		cr.execute("SELECT picking.date_done,ptmp.name,prd.default_code,"\
			"pmove.product_qty,pbd.name,location.name,res_partner.name,pmove.price_unit "\
			"FROM stock_move as pmove "\
			"inner join stock_picking as picking on picking.id= pmove.picking_id "\
			"inner join res_partner on res_partner.id= picking.partner_id "\
			"inner join product_product as prd on prd.id= pmove.product_id "\
			"inner join product_brand as pbd on pbd.id= prd.brand_id "\
			"inner join product_template as ptmp on ptmp.id = prd.product_tmpl_id "\
			"inner join stock_location as location on location.id = pmove.location_dest_id "\
			"where pbd.id in %s AND picking.type = 'in' AND picking.state = 'done' "\
			"AND picking.date_done BETWEEN '%s' and '%s' " % (brands,date_from,date_to))
		polines = cr.fetchall()

		all_content_line = ''
		header = 'GOODS RECEIVED QTY FROM SUPPLIER REPORT BETWEEN,' + str(self.get_date_range(cr, uid,data['form'])) + " \n"
		header += 'DATE RECEIVE,INVENTORY BRAND,OEM NUMBER,SUPPLIER NAME,QTY,UNIT COST,TOTAL COST,LOCATION KEY' + " \n"
		acc_ids = []
		uprice_total = total_amt = total_qty = 0.00
		for result in polines:
			date_receive = result[0]
			part_name = result[2]
			part_name = part_name.replace(',',' ')
			supplier_name = result[6]
			supplier_name = supplier_name.replace(',',' ')
			order_qty = result[3]
			unit_price = result[7] or 0.00
			uprice_total += unit_price
			brand_name = result[4] or ''
			location = result[5] or ''
			sub_total = order_qty*unit_price
			total_amt += sub_total
			total_qty += order_qty
			header += str(date_receive) + "," + str(brand_name) + "," + str(part_name) + "," + str(supplier_name) + "," + str(order_qty) + "," + str(unit_price) + "," + str(sub_total) + "," + str(location) + "\n"
		header += ",," + ",Grand Total," + str(total_qty) + ",," + str(total_amt) + "\n"
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
