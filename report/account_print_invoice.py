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
from report import report_sxw
from osv import osv
import pooler
import locale
from mx import DateTime as dt
from report.interface import report_rml
from tools import to_xml
import calendar
import math
from tools import float_round, float_is_zero, float_compare
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_ALL, '')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class maxmega_tax_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(maxmega_tax_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_cust_po': self._get_cust_po,
            'get_total': self._get_total,
            'get_currency_name': self._get_currency_name,
            'get_currency_rate': self._get_currency_rate,
            'get_tax': self._get_tax,
            'get_description': self._get_description,
#             'get_mail_add': self._get_mail_add,
        })

#     def _get_mail_add(self, o):
#         mail = ''
#         if o.partner_id and o.partner_id.address.type:
#             print o.partner_id.address.id.type
#         else:
#             print 'test'
#         return mail

#     def _get_description(self, l):
#         description = ''
#         len_note_pn = len((l.stock_move_id and l.stock_move_id.note) or "")
#         len_note_pn_remark = 0
#         if len_note_pn > 1:
#             pn_note_lines = str((l.stock_move_id and l.stock_move_id.note) or "").split('\n')
#             while (len_note_pn_remark < 1):
#                 part_note = str(pn_note_lines[len_note_pn_remark])
#                 len_note_pn_remark += 1
#         if len_note_pn > 0:
# #             description = str(l.product_id.default_code)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#             description = str(l.product_id.name)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.stock_move_id and l.stock_move_id.product_customer_id.name)
#         else:
# #             description = str(l.product_id.default_code)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#             description = str(l.product_id.name)+'\n' +"CUST P/N:" + str(l.stock_move_id and l.stock_move_id.product_customer_id.name)
#         return description

    def _get_description(self, l):
        description = ''
#         len_note_pn = len((l.stock_move_id and l.stock_move_id.note) or "")
#         len_note_pn_remark = 0
#         if len_note_pn > 1:
#             pn_note_lines = str((l.stock_move_id and l.stock_move_id.note) or "").split('\n')
#             while (len_note_pn_remark < 1):
        if str((l.stock_move_id and l.stock_move_id.note) or "") <> '':
            part_note = str((l.stock_move_id and l.stock_move_id.note.strip() + '\n') or "")
        elif l.note:
            part_note = str((l.note.strip() + '\n') or "")
        else:
            part_note = ''
#         if len_note_pn > 0:
#             description = str(l.product_id.default_code)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)


        cust_part_no = (l.stock_move_id and l.stock_move_id.product_customer_id and "CUST P/N:" + str(l.stock_move_id.product_customer_id.name)) or ''
        description = str((l.product_id and l.product_id.name) or '') + '\n' +str(part_note) + cust_part_no
#         else:
# #             description = str(l.product_id.default_code)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#             description = str(l.product_id.name)+'\n' +"CUST P/N:" + str(l.stock_move_id and l.stock_move_id.product_customer_id.name)
        return description

    def _get_tax(self, o):
        tax = 'Not Found'
        if o.tax_line:
            for taxes in o.tax_line:
                if taxes.name in ('Purchase Out-Of-Scope - GST_Purchase_OFS', 'Sale Out-Of-Scope - GST_Sales_OFS'):
                    tax = 'OFS 0.00 %'
                elif taxes.name in ('Purchase GST 0% - GST_Purchase_Zero%','Sale GST 0% - GST_Sale_Zero%'):
                    tax = 'ZERO 0.00 %'
                elif taxes.name in ('Purchase GST 7% - GST_purchase_7%','Sale GST 7% - GST_Sales_7%'):
                     tax = 'GST 7.00 %'
        else:
            tax = 'ZERO 0.00 %'
#         if o.partner_id and o.partner_id.property_account_position:
#             tax = 'yes'
#             fiscal_position = o.partner_id.property_account_position
#             tax_id = False
#             for tax in fiscal_position.tax_ids:
#                 tax_id = tax.tax_dest_id.id
#             if tax_id:
#                 if tax_id in (13,14):
#                     
#                 if tax_id in (10,12):
#                    
#         else:
#             tax = 'ZERO 0.00 %'
        return tax

    def _get_cust_po(self, invoice_id):
        cust_po_no = False
        invoice_qry = ''
        if invoice_id:
            invoice_qry = "AND ail.id = %s "%invoice_id
        else:
            invoice_qry = "AND ail.id IN (0) "
        self.cr.execute("select so.client_order_ref from account_invoice_line ail " \
                        "inner join stock_move sm on ail.stock_move_id = sm.id " \
                        "inner join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "inner join sale_order so on so.id = sol.order_id " \
                        + invoice_qry)

        qry = self.cr.dictfetchall()
        if qry:
            for s in qry:
                if cust_po_no == False:
                    cust_po_no = str(s['client_order_ref'])
                else:
                    cust_po_no += ', %s'%s['client_order_ref']
        return cust_po_no

    def _get_currency_name(self, inv):
        currency_name = inv.company_id.currency_tax_id.name
        return currency_name

    def _get_currency_rate(self, inv):
        rate = 0.00
        context = {}
        currency_obj      = self.pool.get('res.currency')
        tgl = str(inv.cur_date)
        tgl2 = datetime.strftime(datetime.strptime(tgl,'%m/%d/%Y %H:%M:%S'),'%Y-%m-%d')
        context['date'] = tgl2
        rate = currency_obj.browse(self.cr, self.uid, inv.company_id.currency_tax_id.id, context=context).rate
        return rate
    
    def _get_total(self, inv, type):
        subtotal_tax = 0.00
        context = {}

        currency_obj      = self.pool.get('res.currency')
        tgl = str(inv.cur_date)
        tgl2 = datetime.strftime(datetime.strptime(tgl,'%m/%d/%Y %H:%M:%S'),'%Y-%m-%d')
        context['date'] = tgl2
        if type == '1':
            subtotal_tax = currency_obj.compute(self.cr, self.uid, inv.currency_id.id, inv.company_id.currency_tax_id.id, inv.amount_untaxed, context=context)
            subtotal_tax = float_round(subtotal_tax,2)
        elif type == '2':
            subtotal_tax = currency_obj.compute(self.cr, self.uid, inv.currency_id.id, inv.company_id.currency_tax_id.id, inv.amount_tax, context=context)
            subtotal_tax = float_round(subtotal_tax,2)
        else:
            subtotal_tax = currency_obj.compute(self.cr, self.uid, inv.currency_id.id, inv.company_id.currency_tax_id.id, inv.amount_total, context=context)
            subtotal_tax = float_round(subtotal_tax,2)
        
#         datetime_object = datetime_object.strftime('%Y-%m-%d')
#         print datetime_object
#         print 'test'
#         if qry:
#             for l in qry:
#            if invoice.currency_id and invoice.currency_id.name == 'SGD':
#                if invoice.invoice_date:
#                    date_qry = "AND name <= '" + invoice_date + "'"
#                else:
#                    date_qry = ""
#            else:
#                
#
#        self.cr.execute("select rate from res_currency_rate where currency_id = 38 " \
#                        + date_qry + " order by name desc limit 1 ")
#        qry = self.cr.dictfetchall()
#        if qry:
#            for s in qry:
#                rate = str(s['rate'])
        return subtotal_tax

report_sxw.report_sxw(
    'report.max.maxmega.invoice2',
    'account.invoice',
    'addons/maxmega_report_addons/report/account_print_invoice.rml',
    parser=maxmega_tax_invoice, header=False)