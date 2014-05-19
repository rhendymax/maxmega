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

class report(report_sxw.rml_parse):
    _name = 'deposit.bank.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        account_journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        qry_jour = ''
        val_jour = []
        
        report_type = data['form']['report_type']
        partner_ids = False
        journal_ids = False
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
            if data['form']['filter_selection'] == 'def':
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
        self.partner_ids = partner_ids
        
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

#journal
        qry_jour = "type in ('bank', 'cash')"
        val_jour.append(('type', 'in', ('bank', 'cash')))

        journal_default_from = data['form']['journal_default_from'] and data['form']['journal_default_from'][0] or False
        journal_default_to = data['form']['journal_default_to'] and data['form']['journal_default_to'][0] or False
        journal_input_from = data['form']['journal_input_from'] or False
        journal_input_to = data['form']['journal_input_to'] or False

        if data['form']['journal_selection'] == 'all_vall':
            journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')

        if data['form']['journal_selection'] == 'name':
            data_found = False
            if journal_default_from and account_journal_obj.browse(self.cr, self.uid, journal_default_from) and account_journal_obj.browse(self.cr, self.uid, journal_default_from).name:
                data_found = True
                val_jour.append(('name', '>=', account_journal_obj.browse(self.cr, self.uid, journal_default_from).name))
            if journal_default_to and account_journal_obj.browse(self.cr, self.uid, journal_default_to) and account_journal_obj.browse(self.cr, self.uid, journal_default_to).name:
                data_found = True
                val_jour.append(('name', '<=', account_journal_obj.browse(self.cr, self.uid, journal_default_to).name))
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'input':
            data_found = False
            if journal_input_from:
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
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'selection':
            if data['form']['journal_ids']:
                journal_ids = data['form']['journal_ids']
        self.journal_ids = journal_ids

        self.report_type = data['form']['report_type']

        #print self.period_ids
        return super(report, self).set_context(objects, data, new_ids, report_type=report_type)
    
    def __init__(self, cr, uid, name, context=None):
        super(report, self).__init__(cr, uid, name, context=context)
        self.amt = 0.00
        self.chgs = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_header_title': self._get_header,
            'get_partner': self._get_partner,
            'get_amt': self._get_amt,
            'get_charges': self._get_charges,
            })
        
    def _get_amt(self):
        return self.amt

    def _get_charges(self):
        return self.chgs

    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Payment Deposit Bank Report'
        elif self.report_type == 'receivable':
            header = 'Receipt Deposit Bank Report'
        return header

    def _get_partner(self):
        if self.report_type == 'payable':
            header = 'Supplier Name'
        elif self.report_type == 'receivable':
            header = 'Customer Name'
        return header
    

    def _get_lines(self):
        results = []
        # partner
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
        user_obj = self.pool.get('res.users')
        type = self.report_type
        qry_type = ''
        if type == 'payable':
            qry_type = "and l.type in ('payment') "
        elif type == 'receivable':
            qry_type = "and l.type in ('receipt') "
        partner_ids = self.partner_ids or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "

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
                "SELECT DISTINCT l.journal_id as journal_id " \
                "FROM account_voucher AS l " \
                "WHERE l.journal_id IS NOT NULL " \
                "And l.payment_option = 'without_writeoff' " \
                "AND l.state IN ('posted') " \
                + qry_type \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry \
                + journal_qry)
        journal_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                journal_ids_vals.append(r['journal_id'])
        
        journal_ids_vals_qry = (len(journal_ids_vals) > 0 and ((len(journal_ids_vals) == 1 and "where id = " +  str(journal_ids_vals[0]) + " ") or "where id IN " +  str(tuple(journal_ids_vals)) + " ")) or "where id IN (0) "
        home_currency = user_obj.browse(self.cr, self.uid, self.uid).company_id.currency_id.name
        cr.execute(
                "SELECT id " \
                "FROM account_journal " \
                + journal_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                cr.execute(
                    "SELECT l.id as voucher_id " \
                    "FROM account_voucher AS l " \
                    "WHERE l.state IN ('posted') " \
                    "And l.payment_option = 'without_writeoff' " \
                    + qry_type \
                    + partner_qry \
                    + date_from_qry \
                    + date_to_qry \
                    + period_qry  + \
                    "and l.journal_id = " + str(s['id']) + " "\
                    "order by l.date")
                qry3 = cr.dictfetchall()
                val = []
                ttl_check = ttl_check_home = ttl_char = ttl_char_home = 0
                if qry3:
                    for t in qry3:
                        inv = voucher_obj.browse(self.cr, self.uid, t['voucher_id'])
                        ttl_check += inv.writeoff_amount
                        ttl_check_home += round(inv.writeoff_amount * inv.ex_rate,2)
                        ttl_char += inv.bank_charges_amount
                        ttl_char_home += round(inv.bank_charges_amount * inv.ex_rate,2)
                        val.append({
                                    "rec_no" : inv.number,
                                    "rec_date" :inv.date,
                                    "check_amt" : inv.writeoff_amount,
                                    "check_home" : inv.writeoff_amount * inv.ex_rate,
                                    "part_name" : (inv.partner_id and inv.partner_id.name) or '',
                                    "exrate" : inv.ex_rate or 0,
                                    "bank_draft" : inv.bank_draft_no or '',
                                    "char" : inv.bank_charges_amount,
                                    "char_home" : inv.bank_charges_amount * inv.ex_rate,
                                    })
                val = val and sorted(val, key=lambda val_res: val_res['rec_date']) or []
                
                journal_id = journal_obj.browse(self.cr, self.uid, s['id'])
                self.amt += ttl_check_home
                self.chgs += ttl_char_home
                results.append({
                    'journal_name' : journal_id.name,
                    'acc_name' : (type == 'receivable' and journal_id.default_debit_account_id and journal_id.default_debit_account_id.name) or (type == 'payable' and journal_id.default_credit_account_id and journal_id.default_debit_account_id.name) or " ",
                    'cur_name': (journal_id.currency and journal_id.currency.name) or home_currency or '',
                    'vals': val,
                    'ttl_check': ttl_check,
                    'ttl_check_home': ttl_check_home,
                    'ttl_char': ttl_char,
                    'ttl_char_home': ttl_char_home,
                    })
        results = results and sorted(results, key=lambda val_res: results['journal_name']) or []
        return results

report_sxw.report_sxw('report.deposit.bank_landscape', 'account.voucher',
    'addons/max_report/report/deposit_bank_report.rml', parser=report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
