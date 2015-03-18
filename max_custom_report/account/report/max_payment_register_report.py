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

import time
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from report import report_sxw
import locale
locale.setlocale(locale.LC_ALL, '')

class max_payment_register_report(report_sxw.rml_parse):
    _name = 'max.payment.register.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        account_journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        qry_jour = ''
        val_jour = []
        
        report_type = data['form']['report_type']
        journal_ids = False
        journal_selection = False
        
        self.date_to = data['form']['date_to'] 
        self.date_to_header = data['form']['date_to'] or False
        
        #Period
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
            period_from_txt = ''
            period_to_txt = ''
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
            self.date_showing = 'Period : "' + period_from_txt + '"-"' + period_to_txt + '"'
            self.date_from = False
            self.date_to = False
        else:
            self.period_ids = False
            self.date_search = 'date'
            self.date_showing = 'Date : "' + data['form']['date_from'] + '"-"' + data['form']['date_to'] + '"'
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#journal
        qry_jour = "type in ('bank', 'cash')"
        val_jour.append(('type', 'in', ('bank', 'cash')))

        journal_default_from = data['form']['journal_default_from'] and data['form']['journal_default_from'][0] or False
        journal_default_to = data['form']['journal_default_to'] and data['form']['journal_default_to'][0] or False
        journal_input_from = data['form']['journal_input_from'] or False
        journal_input_to = data['form']['journal_input_to'] or False
        
        journal_default_from_str = journal_default_to_str = ''
        journal_input_from_str = journal_input_to_str= ''
        
        if data['form']['journal_selection'] == 'all_vall':
            journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')

        if data['form']['journal_selection'] == 'def':
            data_found = False
            if journal_default_from and account_journal_obj.browse(self.cr, self.uid, journal_default_from) and account_journal_obj.browse(self.cr, self.uid, journal_default_from).name:
                journal_default_from_str = account_journal_obj.browse(self.cr, self.uid, journal_default_from).name
                data_found = True
                val_jour.append(('name', '>=', account_journal_obj.browse(self.cr, self.uid, journal_default_from).name))
            if journal_default_to and account_journal_obj.browse(self.cr, self.uid, journal_default_to) and account_journal_obj.browse(self.cr, self.uid, journal_default_to).name:
                journal_default_to_str = account_journal_obj.browse(self.cr, self.uid, journal_default_to).name
                data_found = True
                val_jour.append(('name', '<=', account_journal_obj.browse(self.cr, self.uid, journal_default_to).name))
            journal_selection = '"' + journal_default_from_str + '" - "' + journal_default_to_str + '"'
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'input':
            data_found = False
            if journal_input_from:
                journal_input_from_str = journal_input_from
                self.cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_jour.append(('name', '>=', qry['name']))
            if journal_input_to:
                journal_input_to_str = journal_input_to
                self.cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_jour.append(('name', '<=', qry['name']))
            #print val_part
            journal_selection = '"' + journal_input_from_str + '" - "' + journal_input_to_str + '"'
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'selection':
            jou_ids = ''
            if data['form']['journal_ids']:
                for jo in  account_journal_obj.browse(self.cr, self.uid, data['form']['journal_ids']):
                    jou_ids += '"' + str(jo.name) + '",'
                journal_ids = data['form']['journal_ids']
            journal_selection = '[' + jou_ids +']'
        self.journal_ids = journal_ids
        self.journal_selection = journal_selection
        self.report_type = data['form']['report_type']

        #print self.period_ids
        return super(max_payment_register_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(max_payment_register_report, self).__init__(cr, uid, name, context=context)
        self.get_cheque_amt = 0.00
        self.get_cheque_home = 0.00
        self.get_charges_amt = 0.00
        self.get_charges_home = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_header_title': self._get_header,
            'get_date': self._get_date,
            'get_search_by_journal' : self._get_search_by_journal,
            'get_header_title': self._get_header,
            'get_cheque_amt' : self._get_cheque_amt,
            'get_cheque_home' : self._get_cheque_home,
            'get_charges_amt' : self._get_charges_amt,
            'get_charges_home' : self._get_charges_home,
            })

    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Payment Register By Deposit Bank Report'
        elif self.report_type == 'receivable':
            header = 'Receipt Register By Deposit Bank Report'
        return header

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
    def _get_search_by_journal(self):
        header = False
        if self.journal_selection:
            header = 'Journal Search By : ' + self.journal_selection
        return header

    def _get_cheque_amt(self):
        return self.get_cheque_amt

    def _get_cheque_home(self):
        return self.get_cheque_home

    def _get_charges_amt(self):
        return self.get_charges_amt

    def _get_charges_home(self):
        return self.get_charges_home

    def _get_lines(self):
        results = []
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        voucher_obj = self.pool.get('account.voucher')

        type = self.report_type
        qry_type = ''
        if type == 'payable':
            qry_type = "and l.type in ('payment') "
        elif type == 'receivable':
            qry_type = "and l.type in ('receipt') "
        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "
        
        period_ids = self.period_ids or False
        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)

        if not min_period:
            min_period = period_obj.search(cr, uid, [], order='date_start', limit=1)
        min_period = period_obj.browse(cr, uid, min_period[0])

        max_period = False
        if period_ids:
            max_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start Desc', limit=1)
        elif date_to:
            max_period = period_obj.search(cr, uid, [('date_start', '<=', date_to)], order='date_start Desc', limit=1)

        if not max_period:
            max_period = period_obj.search(cr, uid, [], order='date_start Desc', limit=1)
        max_period = period_obj.browse(cr, uid, max_period[0])
        date_start_min_period = min_period and min_period.date_start or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        val_period = []
        if date_start_min_period:
            val_period.append(('date_start', '>=', date_start_min_period))
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))
        qry_period_ids = period_obj.search(cr, uid, val_period)
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "
        journal_ids = self.journal_ids or False
        journal_qry = (journal_ids and ((len(journal_ids) == 1 and "AND l.journal_id = " + str(journal_ids[0]) + " ") or "AND l.journal_id IN " + str(tuple(journal_ids)) + " ")) or "AND l.journal_id IN (0) "

        cr.execute(
                "SELECT DISTINCT l.journal_id " \
                "FROM account_voucher AS l " \
                "WHERE l.journal_id IS NOT NULL " \
                "AND l.state IN ('posted') " \
                + qry_type \
                + journal_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry)
        journal_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                journal_ids_vals.append(r['journal_id'])
        
        journal_ids_vals_qry = (len(journal_ids_vals) > 0 and ((len(journal_ids_vals) == 1 and "where id = " +  str(journal_ids_vals[0]) + " ") or "where id IN " +  str(tuple(journal_ids_vals)) + " ")) or "where id IN (0) "
        cr.execute(
                "SELECT id, code, name " \
                "FROM account_journal " \
                + journal_ids_vals_qry \
                + " order by code")
        qry = cr.dictfetchall()
        
        if qry:
            gt_amt = gt_amt_home = gt_charges = gt_charge_home = 0.00
            for s in qry:
                cr.execute(
                        "SELECT l.id as voucher_id " \
                        "FROM account_voucher AS l " \
                        "WHERE l.journal_id IS NOT NULL " \
                        "AND l.state IN ('posted') " \
                        + qry_type \
                        + date_from_qry \
                        + date_to_qry \
                        + period_qry + \
                        "and l.journal_id = " + str(s['id']) + " "\
                        "order by l.date")
                qry3 = cr.dictfetchall()
                res = []
                if qry3:
                    t_amt = t_amt_home = t_charges = t_charge_home = 0.00
                    for t in qry3:
                        voucher = voucher_obj.browse(cr, uid, t['voucher_id'])
                        t_amt += voucher.grand_total or 0.00
                        t_amt_home += (voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00) or 0.00
                        t_charges += voucher.bank_charges_amount or 0.00
                        t_charge_home += (voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00)  or 0.00
                        gt_amt += voucher.grand_total or 0.00
                        gt_amt_home += (voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00) or 0.00
                        gt_charges += voucher.bank_charges_amount or 0.00
                        gt_charge_home += (voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00)  or 0.00
                        res.append({
                                    'payment_no' : voucher.number or '',
                                    'cheque_date' : voucher.date or '',
                                    'cheque_no' : voucher.reference or '',
                                    'cheque_amt' : voucher.grand_total or 0.00,
                                    'cheque_home' : (voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00),
                                    'partner_ref' : voucher.partner_id and voucher.partner_id.ref or '',
                                    'partner_name' : voucher.partner_id and voucher.partner_id.name or '',
                                    'ccy_line' : voucher.currency_id and voucher.currency_id.name or '',
                                    'ex_rate' : voucher.ex_rate or 0.00,
                                    'bank_draft' : voucher.bank_draft_no or '',
                                    'charges' : voucher.bank_charges_amount or 0.00,
                                    'charges_home' : (voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00),
                                })
                    res = res and sorted(res, key=lambda val_res: val_res['payment_no']) or []
                    self.get_cheque_amt += t_amt
                    self.get_cheque_home += t_amt_home
                    self.get_charges_amt += t_charges
                    self.get_charges_home += t_charge_home
                    results.append({
                                 'journal_code' : s['code'] or '',
                                 'journal_name' : s['name'] or '',
                                 'ccy' : voucher.currency_id and voucher.currency_id.name or '',
                                 't_amt' : t_amt,
                                 't_amt_home' : t_amt_home,
                                 't_charges' : t_charges,
                                 't_charge_home' : t_charge_home,
                                 'val_ids': res,
                                 })
        results = results and sorted(results, key=lambda val_res: val_res['journal_code']) or []
        return results

report_sxw.report_sxw('report.max.payment.register.report_landscape', 'account.voucher',
    'addons/max_custom_report/account/report/max_payment_register_report.rml', parser=max_payment_register_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
