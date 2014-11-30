# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
# Copyright (c) 2006-2010 OpenERP S.A
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

#from pickle import append
import time
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from report import report_sxw
import locale
from mx import DateTime as dt
locale.setlocale(locale.LC_ALL, '')
from tools import float_round, float_is_zero, float_compare

class general_ledger_report(report_sxw.rml_parse):
    _name = 'general.ledger.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        account_fiscalyear_obj = self.pool.get('account.fiscalyear')
        self.fiscal_year = data['form']['fiscalyear_id']

        fiscal_year_name =  data['form']['fiscalyear_id'] and data['form']['fiscalyear_id'][1] or False
        self.fiscal_year_name = fiscal_year_name
        qry_acc = ''
        val_acc = []
        qry_acc = "type <> 'view'"
        val_acc.append(('type','!=','view'))
        partner_ids = False
        account_ids = False
        account_selection = False
        
        account_default_from = data['form']['account_default_from'] and data['form']['account_default_from'][0] or False
        account_default_to = data['form']['account_default_to'] and data['form']['account_default_to'][0] or False
        account_input_from = data['form']['account_input_from'] or False
        account_input_to = data['form']['account_input_to'] or False
        account_default_from_str = account_default_to_str = ''
        account_input_from_str = account_input_to_str= ''
        data_search = data['form']['account_search_vals']

        if data_search == 'code':
            self.data_search_output = 'Code'
            if data['form']['account_selection'] == 'def':
                data_found = False
                if account_default_from and account_obj.browse(self.cr, self.uid, account_default_from) and account_obj.browse(self.cr, self.uid, account_default_from).code:
                    account_default_from_str = account_obj.browse(self.cr, self.uid, account_default_from).code
                    data_found = True
                    val_acc.append(('code', '>=', account_obj.browse(self.cr, self.uid, account_default_from).code))
                if account_default_to and account_obj.browse(self.cr, self.uid, account_default_to) and account_obj.browse(self.cr, self.uid, account_default_to).code:
                    account_default_to_str = account_obj.browse(self.cr, self.uid, account_default_to).code
                    data_found = True
                    val_acc.append(('code', '<=', account_obj.browse(self.cr, self.uid, account_default_to).code))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(self.cr, self.uid, val_acc, order='code ASC')
            elif data['form']['account_selection'] == 'input':
                data_found = False
                if account_input_from:
                    account_input_from_str = account_input_from
                    self.cr.execute("select code " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "code ilike '" + str(account_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('code', '>=', qry['code']))
                if account_input_to:
                    account_input_to_str = account_input_to
                    self.cr.execute("select code " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "code ilike '" + str(account_input_to) + "%' " \
                                    "order by code desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('code', '<=', qry['code']))
                #print val_part
                account_selection = '"' + account_input_from_str + '" - "' + account_input_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(self.cr, self.uid, val_acc, order='code ASC')
            elif data['form']['account_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  account_obj.browse(self.cr, self.uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.name) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'
        elif data_search == 'name':
            self.data_search_output = 'Name'
            if data['form']['account_selection'] == 'def':
                data_found = False
                if account_default_from and account_obj.browse(self.cr, self.uid, account_default_from) and account_obj.browse(self.cr, self.uid, account_default_from).name:
                    account_default_from_str = account_obj.browse(self.cr, self.uid, account_default_from).name
                    data_found = True
                    val_acc.append(('name', '>=', account_obj.browse(self.cr, self.uid, account_default_from).name))
                if account_default_to and account_obj.browse(self.cr, self.uid, account_default_to) and account_obj.browse(self.cr, self.uid, account_default_to).name:
                    account_default_to_str = account_obj.browse(self.cr, self.uid, account_default_to).name
                    data_found = True
                    val_acc.append(('name', '<=', account_obj.browse(self.cr, self.uid, account_default_to).name))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(self.cr, self.uid, val_acc, order='name ASC')
            elif data['form']['account_selection'] == 'input':
                data_found = False
                if account_input_from:
                    account_input_from_str = account_input_from
                    self.cr.execute("select name " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "name ilike '" + str(account_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('name', '>=', qry['name']))
                if account_input_to:
                    account_input_to_str = account_input_to
                    self.cr.execute("select name " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "name ilike '" + str(account_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('name', '<=', qry['name']))
                #print val_part
                account_selection = '"' + account_input_from_str + '" - "' + account_input_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(self.cr, self.uid, val_acc, order='name ASC')
            elif data['form']['account_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  account_obj.browse(self.cr, self.uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.name) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'
        
        period_default_from = data['form']['period_default_from'] and data['form']['period_default_from'][0] or False
        period_default_from = period_default_from and period_obj.browse(self.cr, self.uid, period_default_from) or False
        period_default_to = data['form']['period_default_to'] and data['form']['period_default_to'][0] or False
        period_default_to = period_default_to and period_obj.browse(self.cr, self.uid, period_default_to) or False

        period_input_from = data['form']['period_input_from'] or False
        period_input_to = data['form']['period_input_to'] or False

        if data['form']['date_selection'] == 'none_sel':
            self.period_ids = False
            self.date_from = False
            self.date_to = False
            self.date_search = ''
        elif data['form']['date_selection'] == 'period_sel':
            self.date_search = 'period'
            val_period = []
            period_from_txt = period_to_txt = ''
            if data['form']['period_filter_selection'] == 'def':
                if period_default_from and period_default_from.date_start:
                    period_from_txt = period_default_from.code
                    val_period.append(('date_start', '>=', period_default_from.date_start))
                if period_default_to and period_default_to.date_start:
                    period_to_txt = period_default_to.code
                    val_period.append(('date_start', '<=', period_default_to.date_start))
        #        period_criteria_search.append(('special', '=', False))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
                if period_input_from:
                    period_from_txt = period_input_from
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '>=', qry['code']))
                if period_input_to:
                    period_to_txt = period_input_to
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_to) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '<=', qry['code']))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            self.date_showing = '"' + period_from_txt + '" - "' + period_to_txt + '"'
            self.date_from = False
            self.date_to = False
        else:
            self.period_ids = False
            self.date_search = 'date'
            self.date_showing = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#        self.report_type = data['form']['report_type']
        self.account_ids = account_ids
        self.account_selection = account_selection
        #print self.period_ids
        return super(general_ledger_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(general_ledger_report, self).__init__(cr, uid, name, context=context)
        self.debit_total = 0.00
        self.credit_total = 0.00
        self.grand_total = 0.00

        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_debit_total': self._get_debit_total,
            'get_credit_total': self._get_credit_total,
            'get_total': self._get_total,
            'get_fiscal_year' : self._get_fiscal_year,
            'get_search_by_account' : self._get_search_by_account,
            'get_date' : self._get_date,
            })

    def _get_date(self):
        header = False
        if self.date_search == 'date':
            if self.date_showing:
                header = 'Date : ' + self.date_showing
        elif self.date_search == 'period':
            if self.date_showing:
                header = 'Period : ' + self.date_showing
        return header
#    
    def _get_search_by_account(self):
        header = False
        if self.account_selection:
            header = 'Account '+ self.data_search_output  +' Search : ' + self.account_selection
        return header
    
    def _get_fiscal_year(self):
        header = False
        if self.fiscal_year_name:
            header = 'Fiscal Year : ' + self.fiscal_year_name
        return header

    def _get_debit_total(self):
        return self.debit_total

    def _get_credit_total(self):
        return self.credit_total

    def _get_total(self):
        return self.grand_total
#
    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        aml_obj     = self.pool.get('account.move.line')
        results         = []
        results1        = []
        fiscal_year = self.fiscal_year

        period_ids = self.period_ids or False
        date_from = self.date_from
        date_to = self.date_to
        account_ids = self.account_ids or False
        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)
        if fiscal_year:
            if min_period:
                if fiscal_year[0] != period_obj.browse(cr, uid, min_period[0]).fiscalyear_id.id:
                    min_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start', limit=1)
            else:
                min_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start', limit=1)

        if not min_period:
            min_period = period_obj.search(cr, uid, [], order='date_start', limit=1)
        min_period = period_obj.browse(cr, uid, min_period[0])

        max_period = False
        if period_ids:
            max_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start Desc', limit=1)
        elif date_to:
            max_period = period_obj.search(cr, uid, [('date_start', '<=', date_to)], order='date_start Desc', limit=1)
        if fiscal_year:
            if max_period:
                if fiscal_year[0] != period_obj.browse(cr, uid, max_period[0]).fiscalyear_id.id:
                    max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
            else:
                max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
        if not max_period:
            max_period = period_obj.search(cr, uid, [], order='date_start Desc', limit=1)
        max_period = period_obj.browse(cr, uid, max_period[0])

        date_start_min_period = min_period and min_period.date_start or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        val_period = []
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))

        qry_period_ids = period_obj.search(cr, uid, val_period)
        account_qry = (account_ids and ((len(account_ids) == 1 and "AND l.account_id = " + str(account_ids[0]) + " ") or "AND l.account_id IN " + str(tuple(account_ids)) + " ")) or "AND l.account_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT DISTINCT l.account_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "AND am.state IN ('draft', 'posted') " \
                    + account_qry \
                    + date_to_qry \
                    + period_qry)
        account_ids_vals = []
        qry = cr.dictfetchall()
        if qry:
            for r in qry:
                account_ids_vals.append(r['account_id'])
        
        account_ids_vals_qry = (len(account_ids_vals) > 0 and ((len(account_ids_vals) == 1 and "where id = " +  str(account_ids_vals[0]) + " ") or "where id IN " +  str(tuple(account_ids_vals)) + " ")) or "where id IN (0) "
        period_qry2 = (qry_period_ids and ((len(qry_period_ids) == 1 and "and aml.period_id = " + str(qry_period_ids[0]) + " ") or "and aml.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND and aml.period_id IN (0) "
        date_from_qry2 = date_from and "And aml.date >= '" + str(date_from) + "' " or " "
        date_to_qry2 = date_to and "And aml.date <= '" + str(date_to) + "' " or " "
        cr.execute(
                "SELECT id, code, name " \
                "FROM account_account " \
                + account_ids_vals_qry \
                + " order by code")
        qry2 = cr.dictfetchall()
        if qry2:
            for s in qry2:
                val = []
                period_end = False
                cr.execute("SELECT DISTINCT ap.id as period_id " \
                    "from account_move_line aml "\
                    "left join account_journal aj on aml.journal_id = aj.id "\
                    "left join account_move am on aml.move_id = am.id "\
                    "left join res_partner rp on aml.partner_id = rp.id "\
                    "left join account_period ap on aml.period_id = ap.id "\
                    "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                    "where " \
                    "am.state in ('draft', 'posted') " \
                    + period_qry2 \
                    + date_to_qry2 + \
                    "and aml.account_id = " + str(s['id']))
                period_ids_vals = []
                qry3 = cr.dictfetchall()
                if qry3:
                    for t in qry3:
                         period_ids_vals.append(t['period_id'])
                period_ids_vals_qry = (len(period_ids_vals) > 0 and ((len(period_ids_vals) == 1 and "where ap.id = " +  str(period_ids_vals[0]) + " ") or "where ap.id IN " +  str(tuple(period_ids_vals)) + " ")) or "where ap.id IN (0) "
                cr.execute(
                         "SELECT ap.id, ap.code, ap.date_start as period_startdate, af.name as fiscalyear_name, ap.date_stop as period_stopdate " \
                         "FROM account_period ap " \
                         "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                         + period_ids_vals_qry \
                         + " order by ap.date_start")
                qry4 = cr.dictfetchall()
                balance = 0
                closing = 0
                closing_inv = 0
                if qry4:
                    for u in qry4:
                        val_ids2 = []
                        opening_balance = balance
                        cr.execute("select av.cheque_no as cheque_no, rp.name as part_name, aj.type as jour_type, aj.name as jour_name, ap.id as period_id, aml.date as aml_date, " \
                            "aml.ref as aml_ref, " \
                            "aml.name as aml_name, " \
                            "aml.amount_currency, " \
                            "rc.currency_id as rc_currency_id, " \
                            "aml.currency_id as aml_currency_id, " \
                            "rcurr.name as aml_cur_name, " \
                            "rcur.name as rc_cur_name, " \
                            "aml.debit as aml_debit, " \
                            "aml.credit as aml_credit, " \
                            "am.name as am_name, " \
                            "ai.invoice_no as supplier_invoice_no " \
                            "from account_move_line aml "\
                            "left join account_move am on aml.move_id = am.id "\
                            "left join account_account aa on aml.account_id = aa.id "\
                            "left join account_voucher av on am.id = av.move_id "\
                            "left join res_partner rp on aml.partner_id = rp.id "\
                            "left join account_period ap on aml.period_id = ap.id "\
                            "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                            "left join account_journal aj on aml.journal_id = aj.id "\
                            "left join res_company rc on aml.company_id = rc.id " \
                            "left join res_currency rcurr on aml.currency_id = rcurr.id " \
                            "left join res_currency rcur on rc.currency_id = rcur.id " \
                            "left join account_invoice ai on aml.move_id = ai.move_id "\
                            "where " \
                            "am.state in ('draft', 'posted') " \
                            "and ap.id = " + str(u['id']) + " "\
                            + date_to_qry2 + \
                            "and aml.account_id = " + str(s['id']) + " "\
                            "order by aa.code, af.name, ap.date_start, aml.date")
                        qry5 = cr.dictfetchall()
                        
                        if qry5:
                            home_currency = ''
                            amount_currency = 0.00
                            for v in qry5:
                                balance += (v['aml_debit'] - v['aml_credit'])
#                                 closing += (v['home_amt'] * sign)
#                                 closing_inv += (v['inv_amt'] * sign)
                                
                                #RT
                                if v['aml_currency_id']:
                                    if v['aml_currency_id'] <> v['rc_currency_id']:
                                        amount_currency = v['amount_currency']
                                        home_currency = v['aml_cur_name']
                                    else:
                                        amount_currency = v['aml_debit'] - v['aml_credit']
                                        home_currency = v['rc_cur_name']
                                else:
                                    amount_currency = v['aml_debit'] - v['aml_credit']
                                    home_currency = v['rc_cur_name']
                                #
                                
                                if u['period_startdate'] < min_period.date_start:
                                    continue
# 
                                else:
                                    part_name = (v['part_name'] and  '@Partner : ' + v['part_name'] + ' ') or ''
                                    name = (v['aml_name'] and  '@Other : ' + v['aml_name'] + ' ') or ''
                                    jour_type = v['jour_type'] or False
                                    
                                    if jour_type and jour_type in ('bank', 'cash'):
                                        jour_name = (v['jour_name'] and  '@Payment Method : ' + v['jour_name'] + ' ') or ''
                                    else:
                                        jour_name = ''
                                    cheque_no = (v['cheque_no'] and  '@Cheque No : ' + v['cheque_no'] + ' ') or ''
                                    val_ids2.append({
                                        'aml_date' : v['aml_date'],
                                        'am_name' : v['am_name'],
                                        'aml_ref' : v['aml_ref'],
                                        'supplier_invoice_no' : v['supplier_invoice_no'],
                                        'aml_name' : part_name + jour_name + cheque_no + name,
                                        'aml_amount': amount_currency,
                                        'aml_currency': home_currency,
                                        'aml_debit' : v['aml_debit'],
                                        'aml_credit' : v['aml_credit'],
                                        })
                                    self.debit_total += v['aml_debit']
                                    self.credit_total += v['aml_credit']
                        val_ids2 = val_ids2 and sorted(val_ids2, key=lambda val_res: val_res['aml_date']) or []
# 
                        if u['period_startdate'] < min_period.date_start:
                            continue
                        else:
                            period_end = datetime.strftime(datetime.strptime(u['period_stopdate'],'%Y-%m-%d'),'%d %B %Y')
                            val.append({
                               'fiscalyear_name' : u['fiscalyear_name'],
                               'period_code': u['code'],
                               'period_startdate': u['period_startdate'],
                               'opening_balance' : opening_balance,
                               'val_ids2': val_ids2,
                               'period_end': datetime.strftime(datetime.strptime(u['period_stopdate'],'%Y-%m-%d'),'%d %B %Y'),
                               })
#                 val = val and sorted(val, key=lambda val_res: val_res['period_startdate']) or []
#                 cur_name = 'False'
#                 if type == 'payable':
#                     cur_name = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.name
#                     cur_id = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.id
#                 elif type == 'receivable':
#                     cur_name = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist.currency_id.name
#                     cur_id = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist.currency_id.id
#                 self.report_total += closing
#                 if cur_id not in self.balance_by_cur:
#                     self.balance_by_cur.update({cur_id : {
#                              'inv' : closing_inv,
#                              'home' : closing,
#                              }
#                         })
#                 else:
#                     res_currency_grouping = self.balance_by_cur[cur_id].copy()
#                     res_currency_grouping['inv'] += closing_inv
#                     res_currency_grouping['home'] += closing
# 
#                     self.balance_by_cur[cur_id] = res_currency_grouping
                results1.append({
                    'acc_name' : s['name'],
                    'acc_code' : s['code'],
                    'period_end': period_end,
                    'closing' : balance,
                    'val_ids' : val,
                    })
                self.grand_total += balance
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['acc_code']) or []
#
        return results1
report_sxw.report_sxw('report.general.ledger.report_landscape', 'account.account',
    'addons/max_custom_report/account/report/general_ledger_report.rml', parser=general_ledger_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
