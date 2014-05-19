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

class maxmega_ap_posted_checklist_report(osv.osv_memory):
    _name = 'maxmega.ap.posted.checklist.report'
    _description = 'Posted Payment Voucher Checklist Report'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Journal', domain="[('type','in',('cash','bank'))]"),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year',required=True, help='Keep empty for all open fiscal year'),
        'from_period_id': fields.many2one('account.period', 'From Period',required=True,domain="[('fiscalyear_id','=',fiscalyear_id)]"),
        'to_period_id': fields.many2one('account.period', 'To Period',required=True,domain="[('fiscalyear_id','=',fiscalyear_id)]"),
        'supplier_ids': fields.many2many('res.partner', string='Supplier', required=True, domain="[('supplier','=',True)]"),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['fiscalyear_id', 'from_period_id', 'to_period_id','supplier_ids','journal_id'], context=context)[0]
        for field in ['fiscalyear_id', 'from_period_id', 'to_period_id','supplier_ids','journal_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        return self._get_tplines(cr, uid, ids, data, context=context)

    def get_date_period(self,cr, uid,form):
		pool = pooler.get_pool(cr.dbname)
		start_period = pool.get('account.period').browse(cr, uid, form['from_period_id']).code
		end_period = pool.get('account.period').browse(cr, uid, form['to_period_id']).code
		date_period = str(start_period) + " To " + str(end_period)
		return date_period

    def lines(self,cr,uid, account, periods, op_balance, form,context):
		ctx = context.copy()
		pool = pooler.get_pool(cr.dbname)
		ctx['fiscalyear'] = form['fiscalyear_id']
		ctx['periods'] = periods
		query = pool.get('account.move.line')._query_get(cr,uid, context=ctx)
		acc_id = account['id']
		cr.execute("SELECT l.date, j.code, l.ref, l.name, l.debit, l.credit, p.name as P_name, m.name as move_id "\
			"FROM account_move_line as l "\
			"LEFT JOIN account_journal j ON l.journal_id = j.id "\
			"LEFT JOIN account_move m ON l.move_id = m.id "\
			"LEFT JOIN res_partner p ON l.partner_id = p.id "\
			"WHERE account_id = %s AND "+query+" "\
			"ORDER by l.date", (acc_id,))
		res = cr.dictfetchall()
		sum = op_balance or 0.0
		for l in res:
			sum += (float(l['debit'] or 0.0) - float(l['credit'] or 0.0))
			l['progress'] = sum
		return res

    def _get_tplines(self, cr, uid, ids,data, context):
		res={}
		result_acc=[]
		pool = pooler.get_pool(cr.dbname)
		form = data['form']
		if not ids:
			ids = data['ids']
		if not ids:
			return []
		start_period = pool.get('account.period').browse(cr, uid, form['from_period_id']).date_start
		end_period = pool.get('account.period').browse(cr, uid, form['to_period_id']).date_stop
		cr.execute("select id from account_period where date_start BETWEEN '%s' AND '%s' ORDER BY date_start asc" % (start_period, end_period))
		periods = cr.fetchall()
		prds = []
		for prd in periods:
			prds.append(prd[0])
		period_ids = '(' + ','.join( [str(x) for x in prds] ) + ')'
		result_acc=[]
		acc_ids=[]
		journal_id = form['journal_id']
		supplier_ids = form['supplier_ids']
		if len(supplier_ids) == 0:
		    supplier_ids = pool.get('res.partner').search(cr, uid, [('supplier','=',True)])

		ac_ids = '(0)'

		all_content_line = ''
		header = 'For Period,' + str(self.get_date_period(cr, uid,data['form'])) + " \n"
		#header += 'Paymant No.,Payment Date,Cheque No. / Invoice Ref,Invoice No,Invoice Date,Currency,Cheque Amount,Cheque Home Amount\n'
		header += 'Paymant No.,Payment Date,Payment Ref.,Bank Draft No.,Cheque No. / Invoice No,Invoice Date,Currency,Currency Rate,Allocated Amt / Invoice Amt, Allocated Home/ Gain Loss, Charges, Charges Home\n'
		all_content_line += header
		for sup in pool.get('res.partner').browse(cr, uid, supplier_ids):
			header = ''
			if journal_id:
			    voucher_ids = pool.get('account.voucher').search(cr, uid, [('partner_id','=',sup.id),('period_id','in',prds),('journal_id','=',journal_id)])
			else:
			    voucher_ids = pool.get('account.voucher').search(cr, uid, [('partner_id','=',sup.id),('period_id','in',prds)])
			header = ''
			if len(voucher_ids) > 0:
			    partner_name = str(sup.name)
			    partner_name = partner_name.replace(',','')
			    header = "\n" + str(sup.ref) + "," + str(partner_name) + "\n"
			    home_amount = curr_amount = 0.00
			    for voucher in pool.get('account.voucher').browse(cr, uid, voucher_ids):
			        invoice_no = "" 
			        invoice_date = ""
			        company_cur_name = voucher.company_id and voucher.company_id.currency_id and voucher.company_id.currency_id.name or ''
			        cur_name = voucher.journal_id and voucher.journal_id.currency and voucher.journal_id.currency.name or company_cur_name
			        cur_rate = voucher.payment_rate or 1
			        allocated_home = voucher.amount * cur_rate
			        allocated_home = round(allocated_home,2)
			        bank_charge = voucher.bank_charges_amount or 0.00
			        bank_charge_home = voucher.bank_charges_in_company_currency or 0.00
			        header += str(voucher.number or '') + "," + str(voucher.date) + "," + str(voucher.reference or '') + "," + str(voucher.bank_draft_no or '') + "," + str(voucher.cheque_no or '') + "," + " " + "," + str(cur_name) + "," + str(cur_rate) + "," + str(voucher.amount) + "," + str(allocated_home) + "," + str(bank_charge) + "," + str(bank_charge_home) + "\n"
			        #header += "Invoice" + "\n"
			        for line in voucher.line_ids:
			            invoice_no = str(line.name or '') 
			            invoice_date = str(line.date_original or '')
			            gain_loss = str(line.gain_loss or '')
			            invoice_amt = line.inv_amount or 0.00
			            inv_currency = str(line.currency_id and line.currency_id.name or '')
			            if line.type == 'dr':
			                invoice_amt = invoice_amt
			            else:
			                invoice_amt = -1*invoice_amt
			            header += ",,,," + str(invoice_no) + "," + str(invoice_date) + "," + str(inv_currency) + ",," + str(invoice_amt) + "," + str(gain_loss) + "\n"

			        #home_amount += (allocated_home)
			        #curr_amount += (voucher.amount or 0.00)
			    #header += ',,,,,,,,,'+str(round(curr_amount,2)) + "," + str(round(home_amount,2)) + " \n"
			    all_content_line += header
		csv_content = ''

		filename = 'Posted Payment Voucher Checklist Report.csv'
		out = base64.encodestring(all_content_line)
		self.write(cr, uid, ids,{'data':out, 'filename':filename})
		obj_model = self.pool.get('ir.model.data')
		model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','maxmega_ap_posted_checklist_result_data_view')])
		resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
		return {
		        'name':'Posted Payment Voucher Checklist Report',
		        'view_type': 'form',
		        'view_mode': 'form',
		        'res_model': 'maxmega.ap.posted.checklist.report',
		        'views': [(resource_id,'form')],
		        'type': 'ir.actions.act_window',
		        'target':'new',
	        	'res_id':ids[0],
		        }

    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
    }
maxmega_ap_posted_checklist_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
