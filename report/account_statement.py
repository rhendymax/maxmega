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
import locale
from report import report_sxw
from datetime import datetime
from mx import DateTime as dt
from mx.DateTime import RelativeDateTime as rdt
from datetime import timedelta

class statement(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        period_id   = data['form']['period_id']
        self.period = self.pool.get('account.period').browse(self.cr, self.uid, period_id[0])
        return super(statement, self).set_context(objects, data, ids, report_type=report_type)
    
    def __init__(self, cr, uid, name, context=None):
        super(statement, self).__init__(cr, uid, name, context=context)
        self.total_debit = 0.00
        self.total_credit = 0.00
        self.current = 0.00
        self.due_1 = 0.00
        self.due_2 = 0.00
        self.due_3 = 0.00
        self.due_4 = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
            'to_upper': self.to_upper,
            'get_statement_date': self.get_statement_date,
            'get_invoice': self.get_invoice,
            'get_type': self.get_type,
            'get_debit': self.get_debit,
            'get_credit': self.get_credit,
            'get_balance': self.get_balance,
            'get_cust_po': self.get_cust_po,
            'get_all_data': self.get_all_data,
        })

    def to_upper(self, s):
        return s.upper()

    def get_statement_date(self):
        return self.period.date_stop

    def get_all_data(self,key_in):
        if key_in == '1':
            return self.current
        if key_in == '2':
            return self.due_1
        if key_in == '3':
            return self.due_2
        if key_in == '4':
            return self.due_3
        if key_in == '5':
            return self.due_4

#     def to_upper(self, s):
#         return s.upper()

#     def get_statement_date(self):
#         return self.period.date_stop
#     
#     def format_date(self, date):
#         try:
#             date_format = datetime.strftime(datetime.strptime(date,'%Y-%m-%d'),'%d-%b-%y')
#         except:
#             return ''
#         return date_format

    def get_invoice(self, partner):
        cr              = self.cr
        uid             = self.uid
        period_obj = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        sale_payment_term_obj     = self.pool.get('sale.payment.term')
        sign = 1
        max_period = self.period.id or False
        date_to = max_period and period_obj.browse(cr, uid, max_period).date_stop or False
        period_1 = period_2 = period_3 = False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period).date_start or False
        val_period = []
        val_period.append(('special', '=', False))
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))

        qry_period_ids = period_obj.search(cr, uid, val_period, order='date_start DESC')
        if qry_period_ids[1]:
            period_1 = qry_period_ids[1]
        if qry_period_ids[2]:
            period_2 = qry_period_ids[2]
        if qry_period_ids[3]:
            period_3 = qry_period_ids[3]

        if date_to:
            cr.execute(
                    "select aml.is_depo as deposit, ai.id as invoice_id, aml.period_id as period_id, sp.id as picking_id, ai.sale_term_id as term_id, aml.id as aml_id, am.name as inv_name, aml.date as inv_date, ai.ref_no as inv_ref, rs.name as sales_name, aml.debit - aml.credit as home_amt, " \
                    "abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) THEN amount_currency ELSE aml.debit - aml.credit END) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) " \
                    "as inv_amt, " \
                    "abs(coalesce ( " \
                    "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                    "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), " \
                    "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid_home, " \
                    "abs(coalesce ( " \
                    "(select sum(CASE WHEN (aml4.currency_id is not null) and (aml4.cur_date is not null) THEN amount_currency ELSE aml4.debit - aml4.credit END) from account_move_line aml4 where aml4.reconcile_partial_id = aml.reconcile_partial_id and aml4.id != aml.id and aml4.date  <= '" +str(date_to) + "'), " \
                    "(select sum(CASE WHEN (aml5.currency_id is not null) and (aml5.cur_date is not null) THEN amount_currency ELSE aml5.debit - aml5.credit END) from account_move_line aml5 where aml5.reconcile_id = aml.reconcile_id and aml5.id != aml.id and aml5.date  <= '" +str(date_to) + "'), " \
                    "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid " \
                    "from account_move_line aml " \
                    "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
                    "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
                    "left join res_users rs on rs.id = ai.user_id left join stock_picking sp on ai.picking_id = sp.id where aml.partner_id IS NOT NULL " \
                    "and am.state IN ('draft', 'posted')  " \
                    "and aa.type = 'receivable' " \
                    "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                    "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                    "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                    "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), 0 " \
                    ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                    "And aml.date  <= '" +str(date_to) + "' "\
                    "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
                    "and aml.partner_id = " + str(partner.id) + " order by aml.date")
            qry3 = cr.dictfetchall()
            val = []
            total_amt1 = total_amt2= total_amt3 = total_amt4 = total_home_amt1 = total_home_amt2 = total_home_amt3 = total_home_amt4 = 0
            if qry3:
                for t in qry3:
                    due_date = False
                    sale_term_id = t['term_id'] and sale_payment_term_obj.browse(self.cr, self.uid, t['term_id']) or False
                    daysremaining = 0
                    if sale_term_id:
                        partner_grace = partner and partner.grace or 0
                        sale_grace = sale_term_id.grace or 0
                        gracedays = partner_grace > 0 and partner_grace or sale_grace
                        termdays = sale_term_id.days
                        Date = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                        due_date = Date + timedelta(days=(termdays + gracedays))
                    #print EndDate
                    due_date = due_date and due_date.strftime('%Y-%m-%d') or False
                    d = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                    delta = datetime.strptime(date_to, '%Y-%m-%d') - d
                    daysremaining = delta.days
                    remain_amt = (t['inv_amt'] * sign) - (t['paid'] * sign)

                    val.append({
                        'invoice_id': t['invoice_id'],
                        'invoice_name' : t['inv_name'],
                        'invoice_date' : t['inv_date'],
                        'due_date' : due_date,
                        'debit':  ((remain_amt > 0) and remain_amt) or 0.00,
                        'credit':  ((remain_amt < 0) and (remain_amt * -1)) or 0.00,
                        'deposit': t['deposit'],
                        })
                    self.total_debit += ((remain_amt > 0) and remain_amt) or 0.00
                    self.total_credit += ((remain_amt < 0) and (remain_amt * -1)) or 0.00
                    if t['period_id'] == max_period:
                        self.current += remain_amt
                    elif t['period_id'] == period_1:
                        self.due_1 += remain_amt
                    elif t['period_id'] == period_2:
                        self.due_2 += remain_amt
                    elif t['period_id'] == period_3:
                        self.due_3 += remain_amt
                    else:
                        self.due_4 += remain_amt
            val = val and sorted(val, key=lambda val_res: val_res['invoice_date']) or []
        return val

    def get_deposit(self, partner):
        cr          = self.cr
        uid         = self.uid
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        move_line     = []
        max_period = self.period.id or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period).date_start or False
        val_period = []
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))

        qry_period_ids = period_obj.search(cr, uid, val_period)

        move_line_ids = move_line_obj.search(cr, uid, [
                        ('partner_id','=',partner.id),
                        ('is_depo','=','True'),
                        ('debit','=', 0),
                        ('period_id','in',qry_period_ids),
                        ], order="date ASC")
        if move_line_ids:
            move_line = [mv_line for mv_line in move_line_obj.browse(cr, uid, move_line_ids)]
        return move_line

    def get_type(self, debit, credit,deposit):
        
        if deposit:
            return 'DP'
        else:
            remain = debit - credit
            if remain > 0:
                return 'IN'
            else:
                return 'CN'
    
    def get_cust_po(self, invoice_id):

        cust_po_no = False
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(cr, uid, invoice_id)
        picking_id = invoice.picking_id.id
        picking_qry = ''
        if picking_id:
            picking_qry = "AND ai.picking_id = %s "%picking_id
        else:
            picking_qry = "AND ai.picking_id IN (0) "
        #print picking_qry
        self.cr.execute("select so.client_order_ref from account_invoice ai inner join " \
                        "sale_order_picking_rel sopr on sopr.picking_id = ai.picking_id " \
                        "inner join sale_order so on so.id = sopr.order_id where ai.type = 'out_invoice' " + picking_qry)

        qry = self.cr.dictfetchall()
        if qry:
            for s in qry:
                if cust_po_no == False:
                    cust_po_no = str(s['client_order_ref'])
                else:
                    cust_po_no += ', %s'%s['client_order_ref']

        return cust_po_no

    def get_debit(self):
        return self.total_debit

    def get_credit(self):
        return self.total_credit

    def get_balance(self):
        return (self.total_debit - self.total_credit)

#     def get_oth_invoice(self, partner, seq):
#         cr          = self.cr
#         uid         = self.uid
#         invoice_obj = self.pool.get('account.invoice')
#         period_obj  = self.pool.get('account.period')
#         res         = 0
#         period_ids  = []
#         
#         oth_period_date = dt.strptime(self.period.date_start, '%Y-%m-%d') - rdt(months=seq)
#         period_ids = period_obj.search(cr, uid, [('date_start','<=',oth_period_date),('special', '=', False)], order='date_start DESC')
#         if period_ids and seq != 4:
#             period_ids = [period_ids[0]]
#         invoice_ids = invoice_obj.search(cr, uid, [
#                         ('partner_id','=',partner.id),
#                         ('state','=','open'),
#                         ('period_id','in',period_ids),
#                         ], order="date_invoice ASC")
#         if invoice_ids:
#             res = 0
#             for inv in invoice_obj.browse(cr, uid, invoice_ids):
#                 if inv.type in ['out_invoice', 'in_refund']:
#                     res += inv.residual
#                 elif inv.type in ['in_invoice', 'out_refund']:
#                     res -= inv.residual
#         return res

report_sxw.report_sxw(
                'report.max.account.statement',
                'res.partner',
                'addons/max_report/report/account_statement.rml',
                parser=statement, header="external"
                )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

