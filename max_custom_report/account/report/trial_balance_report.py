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
from tools import float_round, float_is_zero, float_compare
locale.setlocale(locale.LC_ALL, '')

class trial_balance_report(report_sxw.rml_parse):
    _name = 'trial.balance.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        qry_acc = ''
        val_acc = []
        account_ids = False

        self.acc_selection = 'Account'
        qry_acc = "type <> 'view'"
        val_acc.append(('type', '<>', 'view'))

        account_ids = False
        account_selection = False

        self.chart_account_id = data['form']['chart_account_id'] and data['form']['chart_account_id'][0] or False
        self.chart_account_name = data['form']['chart_account_id'] and data['form']['chart_account_id'][1] or False
        
        self.target_move = data['form']['target_move'] or False
        self.target_move_name = data['form']['target_move'] or False
        
        account_default_from = data['form']['account_default_from'] and data['form']['account_default_from'][0] or False
        account_default_to = data['form']['account_default_to'] and data['form']['account_default_to'][0] or False
        account_input_from = data['form']['account_input_from'] or False
        account_input_to = data['form']['account_input_to'] or False
        
        account_default_from_str = account_default_to_str = ''
        account_input_from_str = account_input_to_str= ''
        data_search = data['form']['acc_search_vals']
        
        if data_search == 'code':
            self.data_search_output = 'Code'
            if data['form']['filter_selection'] == 'all_vall':
                account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='code ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if account_default_from and res_account_obj.browse(self.cr, self.uid, account_default_from) and res_account_obj.browse(self.cr, self.uid, account_default_from).code:
                    account_default_from_str = res_account_obj.browse(self.cr, self.uid, account_default_from).code
                    data_found = True
                    val_acc.append(('code', '>=', res_account_obj.browse(self.cr, self.uid, account_default_from).code))
                if account_default_to and res_account_obj.browse(self.cr, self.uid, account_default_to) and res_account_obj.browse(self.cr, self.uid, account_default_to).code:
                    account_default_to_str = res_account_obj.browse(self.cr, self.uid, account_default_to).code
                    data_found = True
                    val_acc.append(('code', '<=', res_account_obj.browse(self.cr, self.uid, account_default_to).code))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='code ASC')
            elif data['form']['filter_selection'] == 'input':
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
                    account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='code ASC')
            elif data['form']['filter_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  res_account_obj.browse(self.cr, self.uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.name) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'
        elif data_search == 'name':
            self.data_search_output = 'Name'
            if data['form']['filter_selection'] == 'all_vall':
                account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if account_default_from and res_account_obj.browse(self.cr, self.uid, account_default_from) and res_account_obj.browse(self.cr, self.uid, account_default_from).name:
                    account_default_from_str = res_account_obj.browse(self.cr, self.uid, account_default_from).name
                    data_found = True
                    val_acc.append(('name', '>=', res_account_obj.browse(self.cr, self.uid, account_default_from).name))
                if account_default_to and res_account_obj.browse(self.cr, self.uid, account_default_to) and res_account_obj.browse(self.cr, self.uid, account_default_to).name:
                    account_default_to_str = res_account_obj.browse(self.cr, self.uid, account_default_to).name
                    data_found = True
                    val_acc.append(('name', '<=', res_account_obj.browse(self.cr, self.uid, account_default_to).name))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
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
                account_selection = '"' + account_input_from_str + '" - "' + account_input_to_str + '"'
                if data_found:
                    account_ids = res_account_obj.search(self.cr, self.uid, val_acc, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  res_account_obj.browse(self.cr, self.uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.name) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'

#        period_default_from = data['form']['period_default_from'] and data['form']['period_default_from'][0] or False
#        period_default_from = period_default_from and period_obj.browse(self.cr, self.uid, period_default_from) or False
        period_default_to = data['form']['period_default_to'] and data['form']['period_default_to'][0] or False
        period_default_to = period_default_to and period_obj.browse(self.cr, self.uid, period_default_to) or False

#        period_input_from = data['form']['period_input_from'] or False
        period_input_to = data['form']['period_input_to'] or False

        if data['form']['date_selection'] == 'none_sel':
            self.period_ids = False
            self.date_to = False
            self.date_search = ''
        elif data['form']['date_selection'] == 'period_sel':
            self.date_search = 'period'
            val_period = []
            period_to_txt = ''
            if data['form']['period_filter_selection'] == 'def':
                if period_default_to and period_default_to.date_start:
                    period_to_txt = period_default_to.code
                    val_period.append(('date_start', '<=', period_default_to.date_start))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
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
            self.date_showing = 'Period To : ' + period_to_txt
            self.date_to = False
        else:
            self.period_ids = False
            self.date_search = 'date'
            self.date_showing = 'Date To ' + data['form']['date_to']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

        self.account_ids = account_ids
        self.account_selection = account_selection
        return super(trial_balance_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(trial_balance_report, self).__init__(cr, uid, name, context=context)
        self.debit_total = 0.00
        self.credit_total = 0.00
        self.open_balance = 0.00
        self.balance = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_search_by_account' : self._get_search_by_account,
            'get_date' : self._get_date,
            'get_chart_account' : self._get_chart_account,
            'get_target_move' : self._get_target_move,
            'get_lines': self._get_lines,
            'get_debit_total': self._get_debit_total,
            'get_credit_total': self._get_credit_total,
            'get_balance_total': self._get_balance_total,
            'get_open_balance_total': self._get_open_balance_total,
            })

    def _get_debit_total(self):
        return self.debit_total

    def _get_credit_total(self):
        return self.credit_total

    def _get_open_balance_total(self):
        return self.open_balance

    def _get_balance_total(self):
        return self.balance

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

    def _get_chart_account(self):
        header = False
        if self.chart_account_name:
            header = 'Chart Account : ' + self.chart_account_name
        return header

    def _get_target_move(self):
        header = False
        if self.target_move_name == 'posted':
            header = 'Target Moves : All Posted Entries'
        else:
            header = 'Target Moves : All Entries'
        return header

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        aml_obj     = self.pool.get('account.move.line')
        am_obj     = self.pool.get('account.move')
        account_obj     = self.pool.get('account.account')
        results         = []

        chart_account_id = self.chart_account_id or False
        target_move = self.target_move or False
        print target_move
        period_ids = self.period_ids or False
        date_to = self.date_to or False
        account_ids = self.account_ids or False

        if chart_account_id:
            chart_account_id = account_obj.browse(cr, uid, chart_account_id)
        company_id = (chart_account_id and chart_account_id.company_id and chart_account_id.company_id.id) or False

        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_stop Desc', limit=1)

        elif date_to:
            min_period = period_obj.search(cr, uid, [('date_stop', '<=', date_to)], order='date_stop Desc', limit=1)

        if not min_period:
            min_period = period_obj.search(cr, uid, [], order='date_stop Desc', limit=1)
        min_period = period_obj.browse(cr, uid, min_period[0])

#        raise osv.except_osv(_('Error !'), _('test'))
        company_qry = (company_id and ("AND amls.company_id = " + str(company_id) + " "))
        target_move_qry = (target_move and target_move == 'posted' and "AND ams.state = 'posted' ") or " "
        date_start_max_period = min_period and min_period.date_start or False
        date_stop_max_period = min_period and min_period.date_stop or False
        
        account_qry = (account_ids and ((len(account_ids) == 1 and "AND amls.account_id = " + str(account_ids[0]) + " ") or "AND amls.account_id IN " + str(tuple(account_ids)) + " ")) or "AND amls.account_id IN (0) "

        cr.execute(
                "select aa.id, aa.code, aa.name, " \
                "coalesce( " \
                    "(select sum(aml.debit- aml.credit) from account_move_line aml " \
                    "where aml.date <= '" + str(date_start_max_period) + "' and aml.account_id = aa.id group by aml.account_id) " \
                ",0) as opening_balance, " \
                "coalesce( " \
                    "(select sum(aml.debit) from account_move_line aml " \
                    "where aml.date >= '" + str(date_start_max_period) + "' and aml.date <= '" + str(date_stop_max_period) + "' and aml.account_id = aa.id group by aml.account_id) " \
                ",0) as current_debit, " \
                "coalesce( " \
                    "(select sum(aml.credit) from account_move_line aml " \
                    "where aml.date >= '" + str(date_start_max_period) + "' and aml.date <= '" + str(date_stop_max_period) + "' and aml.account_id = aa.id group by aml.account_id) " \
                ",0) as current_credit, " \
                "coalesce( " \
                    "(select sum(aml.debit- aml.credit) from account_move_line aml " \
                    "where aml.date <= '" + str(date_stop_max_period) + "' and aml.account_id = aa.id group by aml.account_id) " \
                ",0) as balance " \
                "from account_account aa where id in (select DISTINCT account_id from account_move_line amls inner join account_move ams " \
                "on amls.move_id = ams.id where amls.date <= '" + str(date_stop_max_period) + "' " \
                + account_qry \
                + company_qry \
                + target_move_qry + \
                "order by account_id)")
        qry = cr.dictfetchall()
        
        if qry:
            for r in qry:
                self.debit_total += r['current_debit'] or 0.00
                self.credit_total += r['current_credit'] or 0.00
                self.open_balance += r['opening_balance'] or 0.00
                self.balance += r['balance'] or 0.00
                results.append({
                    'code' : r['code'],
                    'name' : r['name'],
                    'opening_balance' : r['opening_balance'],
                    'debit' : r['current_debit'],
                    'credit' : r['current_credit'],
                    'balance' : r['balance'],
                    })
                
        results = results and sorted(results, key=lambda val_res: val_res['code']) or []

        return results

report_sxw.report_sxw('report.trial.balance.report_landscape', 'account.account',
    'addons/max_custom_report/account/report/trial_balance_report.rml', parser=trial_balance_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
