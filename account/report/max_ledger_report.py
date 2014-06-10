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

class max_ledger_report(report_sxw.rml_parse):
    _name = 'max.ledger.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        period_obj = self.pool.get('account.period')
        self.fiscal_year = data['form']['fiscal_year']
        qry_supp = ''
        val_part = []

        report_type = data['form']['report_type']
        partner_ids = False
        if report_type == 'receivable':
            data_search = data['form']['cust_search_vals']
            qry_supp = 'customer = True'
            val_part.append(('customer', '=', True))

        elif report_type == 'payable':
            data_search = data['form']['supplier_search_vals']

            if data['form']['supp_selection'] == 'all':
                qry_supp = 'supplier = True'
                val_part.append(('supplier', '=', True))
            elif data['form']['supp_selection'] == 'supplier':
                qry_supp = 'supplier = True and sundry = False'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', False))
            elif data['form']['supp_selection'] == 'sundry':
                qry_supp = 'supplier = True and sundry = True'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', True))

        partner_default_from = data['form']['partner_default_from'] and data['form']['partner_default_from'][0] or False
        partner_default_to = data['form']['partner_default_to'] and data['form']['partner_default_to'][0] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False

        if data_search == 'code':
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref:
                    data_found = True
                    val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref:
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))
                #print val_part
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        elif data_search == 'name':
            if data['form']['filter_selection'] == 'all_vall':
                self.partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).name:
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).name:
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).name))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']

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
        elif data['form']['date_selection'] == 'period_sel':
            val_period = []
            if data['form']['period_filter_selection'] == 'def':
                if period_default_from and period_default_from.date_start:
                    val_period.append(('date_start', '>=', period_default_from.date_start))
                if period_default_to and period_default_to.date_start:
                    val_period.append(('date_start', '<=', period_default_to.date_start))
        #        period_criteria_search.append(('special', '=', False))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
                if period_input_from:
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '>=', qry['code']))
                if period_input_to:
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_to) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '<=', qry['code']))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            self.date_from = False
            self.date_to = False
        else:
            self.period_ids = False
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        self.report_type = data['form']['report_type']
        self.partner_ids = partner_ids
        #print self.period_ids
        return super(max_ledger_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(max_ledger_report, self).__init__(cr, uid, name, context=context)
        self.report_total = 0.00
        self.balance_by_cur = {}
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_report_total': self._get_report_total,
            'get_header_title': self._get_header,
            'get_balance_by_cur': self._get_balance_by_cur,
            })

    def _get_report_total(self):
        return self.report_total

    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Account Payable Ledger Report'
        elif self.report_type == 'receivable':
            header = 'Account Receivable Ledger Report'
        return header
    
    def _get_balance_by_cur(self):
        result = []
        currency_obj    = self.pool.get('res.currency')
        for item in self.balance_by_cur.items():
            result.append({
                'cur_name' : currency_obj.browse(self.cr, self.uid, item[0]).name,
                'inv' : item[1]['inv'],
                'home' : item[1]['home'],
            })
        result = result and sorted(result, key=lambda val_res: val_res['cur_name']) or []
        return result

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        aml_obj     = self.pool.get('account.move.line')
        partner_obj     = self.pool.get('res.partner')

        results         = []
        results1        = []
        fiscal_year = self.fiscal_year
        type = self.report_type

        if type == 'payable':
            sign = -1
        elif type == 'receivable':
            sign = 1

        period_ids = self.period_ids or False
        date_from = self.date_from
        date_to = self.date_to
        partner_ids = self.partner_ids or False
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
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.partner_id IS NOT NULL " \
                    "AND l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "And account.type = '" + type + "' " \
                    "AND am.state IN ('draft', 'posted') " \
                    + partner_qry \
                    + date_to_qry \
                    + period_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "
        period_qry2 = (qry_period_ids and ((len(qry_period_ids) == 1 and "and aml.period_id = " + str(qry_period_ids[0]) + " ") or "and aml.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND and aml.period_id IN (0) "
        date_from_qry2 = date_from and "And aml.date >= '" + str(date_from) + "' " or " "
        date_to_qry2 = date_to and "And aml.date <= '" + str(date_to) + "' " or " "
        val = []
        cr.execute(
                "SELECT id, name, ref " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                cr.execute("SELECT DISTINCT ap.id as period_id " \
                    "from account_move_line aml "\
                    "left join account_move am on aml.move_id = am.id "\
                    "left join account_account aa on aml.account_id = aa.id "\
                    "left join res_company rco on aml.company_id = rco.id "\
                    "left join res_currency rc on COALESCE(aml.currency_id,rco.currency_id) = rc.id "\
                    "left join res_partner rp on aml.partner_id = rp.id "\
                    "left join account_period ap on aml.period_id = ap.id "\
                    "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                    "left join account_journal aj on aml.journal_id = aj.id "\
                    "where " \
                    "am.state in ('draft', 'posted') " \
                    "and aa.type = '" + type + "' " \
                     + period_qry2 \
                    + date_to_qry2 + \
                    "and aml.partner_id = " + str(s['id']))
                period_ids_vals = []
                qry3 = cr.dictfetchall()
                if qry3:
                    for t in qry3:
                        period_ids_vals.append(t['period_id'])
                period_ids_vals_qry = (len(period_ids_vals) > 0 and ((len(period_ids_vals) == 1 and "where ap.id = " +  str(period_ids_vals[0]) + " ") or "where ap.id IN " +  str(tuple(period_ids_vals)) + " ")) or "where ap.id IN (0) "
                cr.execute(
                        "SELECT ap.id, ap.code, ap.date_start as period_startdate, af.name as fiscalyear_name " \
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
                        opening_balance = balance
                        cr.execute("select rp.id as partner_id, " \
                            "rp.ref as partner_ref, " \
                            "rp.name as partner_name, " \
                            "rc.id as currency_id, " \
                            "rc.name as currency_name, " \
                            "af.id as fiscalyear_id, " \
                            "af.name as fiscalyear_name, " \
                            "ap.id as period_id, " \
                            "ap.code as period_code, " \
                            "ap.date_start as period_startdate, " \
                            "aml.is_depo as depo_status, " \
                            "am.name as am_name, " \
                            "sum(aml.debit - aml.credit) as home_amt, " \
                            "sum(abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) " \
                            "THEN amount_currency " \
                            "ELSE aml.debit - aml.credit " \
                            "END) * (" \
                            "CASE WHEN (debit - credit) > 0 " \
                            "THEN 1 " \
                            "ELSE -1 " \
                            "END" \
                            ")) as inv_amt, " \
                            "aml.exrate as rate, " \
                            "aj.type as journal_type, " \
                            "aml.date as aml_date "\
                            "from account_move_line aml "\
                            "left join account_move am on aml.move_id = am.id "\
                            "left join account_account aa on aml.account_id = aa.id "\
                            "left join res_company rco on aml.company_id = rco.id "\
                            "left join res_currency rc on COALESCE(aml.currency_id,rco.currency_id) = rc.id "\
                            "left join res_partner rp on aml.partner_id = rp.id "\
                            "left join account_period ap on aml.period_id = ap.id "\
                            "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                            "left join account_journal aj on aml.journal_id = aj.id "\
                            "where " \
                            "am.state in ('draft', 'posted') " \
                            "and aa.type = '" + type + "' " \
                            "and ap.id = " + str(u['id']) + " "\
                            + date_to_qry2 + \
                            "and aml.partner_id = " + str(s['id']) + " "\
                            "group by rp.id, rp.ref, rp.name, rc.id, rc.name, af.id, " + \
                            "af.name, ap.id, ap.code, ap.date_start, aml.is_depo, am.name, " + \
                            "aml.exrate, aj.type, aml.date " + \
                            "order by rp.ref,af.name, ap.date_start, aml.date")
                        qry5 = cr.dictfetchall()
                        period = False
                        val_ids2 = []
                        period_id_vals = {}
                        if qry5:
                            for v in qry5:
                                balance += (v['home_amt'] * sign)
                                closing += (v['home_amt'] * sign)
                                closing_inv += (v['inv_amt'] * sign)
                                
                                if u['period_startdate'] < min_period.date_start:
                                    continue

                                else:
                                    if v['journal_type'] == 'purchase':
                                        journal_type = 'INV'
                                    elif v['journal_type'] == 'sale':
                                        journal_type = 'INV'
                                    elif v['journal_type'] == 'purchase_refund':
                                        journal_type = 'INV-REF'
                                    elif v['journal_type'] == 'sale_refund':
                                        journal_type = 'INV-REF'
                                    elif v['journal_type'] in ('bank','cash') and v['depo_status'] == True:
                                        journal_type = 'DEPOSIT'
                                    elif v['journal_type'] in ('bank', 'cash') and v['depo_status'] == False:
                                        journal_type = 'PAYMENT'
                                    val_ids2.append({
                                       'am_name' : v['am_name'],
                                       'aml_date' : v['aml_date'],
                                       'journal_type' : journal_type,
                                       'currency_name': v['currency_name'],
                                       'exchange_rate': v['rate'],
                                       'inv_amount': (v['inv_amt'] * sign),
                                       'home_amount': (v['home_amt'] * sign),
                                       'balance': balance,
                                       })
                        val_ids2 = val_ids2 and sorted(val_ids2, key=lambda val_res: val_res['aml_date']) or []

                        if u['period_startdate'] < min_period.date_start:
                            continue
                        else:
                            val.append({
                               'opening_balance' : opening_balance,
                               'fiscalyear_name' : u['fiscalyear_name'],
                               'period_code': u['code'],
                               'period_startdate': u['period_startdate'],
                               'val_ids2': val_ids2,
                               })
                val = val and sorted(val, key=lambda val_res: val_res['period_startdate']) or []
                cur_name = 'False'
                if type == 'payable':
                    cur_name = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.name
                    cur_id = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.id
                elif type == 'receivable':
                    cur_name = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist.currency_id.name
                    cur_id = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist.currency_id.id
                self.report_total += closing
                if cur_id not in self.balance_by_cur:
                    self.balance_by_cur.update({cur_id : {
                             'inv' : closing_inv,
                             'home' : closing,
                             }
                        })
                else:
                    res_currency_grouping = self.balance_by_cur[cur_id].copy()
                    res_currency_grouping['inv'] += closing_inv
                    res_currency_grouping['home'] += closing

                    self.balance_by_cur[cur_id] = res_currency_grouping
                results1.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    'cur_name': cur_name,
                    'closing' : closing_inv,
                    'val_ids' : val,
                    })
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['part_name']) or []

        return results1
report_sxw.report_sxw('report.max.ledger.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/max_ledger_report.rml', parser=max_ledger_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
