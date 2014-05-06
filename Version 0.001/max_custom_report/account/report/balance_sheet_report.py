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
from tools import float_round, float_is_zero, float_compare

class balance_sheet_report(report_sxw.rml_parse):
    _name = 'balance.sheet.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_from = data['form']['period_from'] and data['form']['period_from'][0] or False
        self.period_to = data['form']['period_to'] and data['form']['period_to'][0] or False
        return super(balance_sheet_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(balance_sheet_report, self).__init__(cr, uid, name, context=context)
        self.equity_one = 0.00
        self.equity_all = 0.00
        self.profit_lost_one = 0.00
        self.profit_lost_all = 0.00
        self.fixed_asset_one = 0.00
        self.fixed_asset_all = 0.00
        self.accumulated_one = 0.00
        self.accumulated_all = 0.00
        self.investment_one = 0.00
        self.investment_all = 0.00
        self.curr_asset_one = 0.00
        self.curr_asset_all = 0.00
        self.curr_liabilities_one = 0.00
        self.curr_liabilities_all = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_sales': self._get_sales,
            'total_equity_one' : self._total_equity_one,
            'total_equity_all' : self._total_equity_all,
            'total_profit_lost_one' : self._total_profit_lost_one,
            'total_profit_lost_all' : self._total_profit_lost_all,
            'total_fixed_asset_one' : self._total_fixed_asset_one,
            'total_fixed_asset_all' : self._total_fixed_asset_all,
            'total_accumulated_one' : self._total_accumulated_one,
            'total_accumulated_all' : self._total_accumulated_all,
            'total_summary1_one' : self._total_summary1_one,
            'total_summary1_all' : self._total_summary1_all,
            'total_curr_asset_one' : self._total_curr_asset_one,
            'total_curr_asset_all' : self._total_curr_asset_all,
            'total_curr_liabilities_one' : self._total_curr_liabilities_one,
            'total_curr_liabilities_all' : self._total_curr_liabilities_all,
            'total_summary2_one' : self._total_summary2_one,
            'total_summary2_all' : self._total_summary2_all,
            'total_summary3_one' : self._total_summary3_one,
            'total_summary3_all' : self._total_summary3_all,
            'get_period_from': self._get_period_from,
            'get_period_to': self._get_period_to,
            })

    def _total_profit_lost_one(self):
        val_period = []
        val_account_in = []
        val_account_out = []
        period_from = self.period_from
        period_to = self.period_to
        account_period_obj = self.pool.get('account.period')
        account_account_obj = self.pool.get('account.account')
        self.cr.execute("SELECT l.id as period_id " \
               " FROM account_period l " \
               " GROUP BY l.id, l.date_start, l.special order by l.date_start desc, l.special desc")
        period_id_search = self.cr.dictfetchone()
        cr_period_to = period_to or period_id_search and period_id_search['period_id']
        total = 0.00
        val_account_in.append(('pl_type', 'in', ['income', 'other_income']))
        acc_ids_in = account_account_obj.search(self.cr, self.uid, val_account_in, order='code ASC')
        if acc_ids_in:
            account_ids_in = account_account_obj.browse(self.cr, self.uid, acc_ids_in)
            for acc_in in account_ids_in:
                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc_in.id) + " and period_id = " + str(cr_period_to) + " " \
                       " GROUP BY l.account_id")
                total_one = False
                total_one = self.cr.dictfetchone()
                total_one = total_one and float_round(total_one['balance'],2) or 0.00
                total += (-1 * total_one)

        val_account_out.append(('pl_type', 'in', ['expense', 'other_expense']))
        acc_ids_out = account_account_obj.search(self.cr, self.uid, val_account_out, order='code ASC')
        if acc_ids_out:
            account_ids_out = account_account_obj.browse(self.cr, self.uid, acc_ids_out)
            for acc_out in account_ids_out:
                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc_out.id) + " and period_id = " + str(cr_period_to) + " " \
                       " GROUP BY l.account_id")
                total_one = False
                total_one = self.cr.dictfetchone()
                total_one = total_one and float_round(total_one['balance'],2) or 0.00
                total -= total_one
        self.profit_lost_one += total
        display =locale.format("%(amount).2f", {'amount': abs(float_round(total,2))},1)
        if total < 0:
            display = "(" + display + ")"
        return display

    def _total_profit_lost_all(self):
        val_period = []
        val_account_in = []
        val_account_out = []
        period_from = self.period_from
        period_to = self.period_to
        account_period_obj = self.pool.get('account.period')
        account_account_obj = self.pool.get('account.account')
        if period_from and account_period_obj.browse(self.cr, self.uid, period_from) and account_period_obj.browse(self.cr, self.uid, period_from).date_start:
            val_period.append(('date_start', '>=', account_period_obj.browse(self.cr, self.uid, period_from).date_start))
        if period_to and account_period_obj.browse(self.cr, self.uid, period_to) and account_period_obj.browse(self.cr, self.uid, period_to).date_start:
            val_period.append(('date_start', '<=', account_period_obj.browse(self.cr, self.uid, period_to).date_start))
        period_ids = account_period_obj.search(self.cr, self.uid, val_period, order='date_start, special desc')
        val_ss = ''
        if period_ids:
            for ss in period_ids:
                if val_ss == '':
                    val_ss += str(ss)
                else:
                    val_ss += (', ' + str(ss))
        total = 0.00
        val_account_in.append(('pl_type', 'in', ['income', 'other_income']))
        acc_ids_in = account_account_obj.search(self.cr, self.uid, val_account_in, order='code ASC')
        if acc_ids_in:
            account_ids_in = account_account_obj.browse(self.cr, self.uid, acc_ids_in)
            for acc_in in account_ids_in:
                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc_in.id) + " and period_id in (" + val_ss + ") " \
                       " GROUP BY l.account_id")
                total_all = False
                total_all = self.cr.dictfetchone()
                total_all = total_all and float_round(total_all['balance'],2) or 0.00
                total += (-1 * total_all)

        val_account_out.append(('pl_type', 'in', ['expense', 'other_expense']))
        acc_ids_out = account_account_obj.search(self.cr, self.uid, val_account_out, order='code ASC')
        if acc_ids_out:
            account_ids_out = account_account_obj.browse(self.cr, self.uid, acc_ids_out)
            for acc_out in account_ids_out:
                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc_out.id) + " and period_id in (" + val_ss + ") " \
                       " GROUP BY l.account_id")
                total_all = False
                total_all = self.cr.dictfetchone()
                total_all = total_all and float_round(total_all['balance'],2) or 0.00
                total -= total_all
        self.profit_lost_all += total
        display =locale.format("%(amount).2f", {'amount': abs(float_round(total,2))},1)
        if total < 0:
            display = "(" + display + ")"
        return display

    def _total_equity_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.equity_one - self.profit_lost_one,2))},1)
        if -1 * (self.equity_one - self.profit_lost_one) < 0:
            display = "(" + display + ")"
        return display

    def _total_equity_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.equity_all - self.profit_lost_all,2))},1)
        if -1 * (self.equity_all - self.profit_lost_all) < 0:
            display = "(" + display + ")"
        return display

    def _total_fixed_asset_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.fixed_asset_one,2))},1)
        if 1 * self.fixed_asset_one < 0:
            display = "(" + display + ")"
        return display

    def _total_fixed_asset_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.fixed_asset_all,2))},1)
        if 1 * self.fixed_asset_all < 0:
            display = "(" + display + ")"
        return display

    def _total_accumulated_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.accumulated_one,2))},1)
        if -1 * self.accumulated_one < 0:
            display = "(" + display + ")"
        return display

    def _total_accumulated_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.accumulated_all,2))},1)
        if -1 * self.accumulated_all < 0:
            display = "(" + display + ")"
        return display

    def _total_summary1_one(self):
        summary = (self.fixed_asset_one) - (-1 * self.accumulated_one)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary1_all(self):
        summary = (self.fixed_asset_all) - (-1 * self.accumulated_all)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_curr_asset_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.curr_asset_one,2))},1)
        if 1 * self.curr_asset_one < 0:
            display = "(" + display + ")"
        return display

    def _total_curr_asset_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.curr_asset_all,2))},1)
        if 1 * self.curr_asset_all < 0:
            display = "(" + display + ")"
        return display

    def _total_curr_liabilities_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.curr_liabilities_one,2))},1)
        if -1 * self.curr_liabilities_one < 0:
            display = "(" + display + ")"
        return display

    def _total_curr_liabilities_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.curr_liabilities_all,2))},1)
        if -1 * self.curr_liabilities_all < 0:
            display = "(" + display + ")"
        return display

    def _total_summary2_one(self):
        summary = (self.curr_asset_one) - (-1 * self.curr_liabilities_one)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary2_all(self):
        summary = (self.curr_asset_all) - (-1 * self.curr_liabilities_all)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary3_one(self):
        summary = ((self.fixed_asset_one) - (-1 * self.accumulated_one)) +  self.investment_one + ((self.curr_asset_one) - (-1 * self.curr_liabilities_one))
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary3_all(self):
        summary = ((self.fixed_asset_all) - (-1 * self.accumulated_all)) +  self.investment_all + ((self.curr_asset_all) - (-1 * self.curr_liabilities_all))
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _get_period_from(self):
        period_from = self.period_from and self.pool.get('account.period').browse(self.cr, self.uid,self.period_from).name or False
        self.cr.execute("SELECT l.id as period_id, l.name as period " \
               " FROM account_period l " \
               " GROUP BY l.id, l.name, l.date_start, l.special order by l.date_start, l.special desc")
        period_id_search = self.cr.dictfetchone()
        cr_period_from = period_from or period_id_search and period_id_search['period']
        return cr_period_from
    
    def _get_period_to(self):
        period_to = self.period_to and self.pool.get('account.period').browse(self.cr, self.uid, self.period_to).name or False
        self.cr.execute("SELECT l.id as period_id, l.name as period " \
               " FROM account_period l " \
               " GROUP BY l.id, l.name, l.date_start, l.special order by l.date_start desc, l.special desc")
        period_id_search = self.cr.dictfetchone()
        cr_period_to = period_to or period_id_search and period_id_search['period']

        return cr_period_to

    def _get_sales(self, type, sign):
        results = []
        val_account = []
        val_period = []

        period_from = self.period_from
        period_to = self.period_to
        account_period_obj = self.pool.get('account.period')
        account_account_obj = self.pool.get('account.account')

        self.cr.execute("SELECT l.id as period_id " \
               " FROM account_period l " \
               " GROUP BY l.id, l.date_start, l.special order by l.date_start desc, l.special desc")
        period_id_search = self.cr.dictfetchone()
        cr_period_to = period_to or period_id_search and period_id_search['period_id']
        if period_from and account_period_obj.browse(self.cr, self.uid, period_from) and account_period_obj.browse(self.cr, self.uid, period_from).date_start:
            val_period.append(('date_start', '>=', account_period_obj.browse(self.cr, self.uid, period_from).date_start))
        if period_to and account_period_obj.browse(self.cr, self.uid, period_to) and account_period_obj.browse(self.cr, self.uid, period_to).date_start:
            val_period.append(('date_start', '<=', account_period_obj.browse(self.cr, self.uid, period_to).date_start))
        period_ids = account_period_obj.search(self.cr, self.uid, val_period, order='date_start, special desc')
        val_ss = ''
        if period_ids:
            for ss in period_ids:
                if val_ss == '':
                    val_ss += str(ss)
                else:
                    val_ss += (', ' + str(ss))
        val_account.append(('pl_type', '=', type))
        acc_ids = account_account_obj.search(self.cr, self.uid, val_account, order='code ASC')
        if acc_ids:
            account_ids = account_account_obj.browse(self.cr, self.uid, acc_ids)
            for acc in account_ids:
                res = {}
                res['acc_code'] = acc.code
                res['acc_name'] = acc.name


                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc.id) + " and period_id = " + str(cr_period_to) + " " \
                       " GROUP BY l.account_id")
                total_one = self.cr.dictfetchone()
                total_one2 = total_one and float_round(total_one['balance'],2) or 0.00
                if type == 'equity':
                    self.equity_one += total_one2
                if type == 'fixed_asset':
                    self.fixed_asset_one += total_one2
                if type == 'accumulated':
                    self.accumulated_one += total_one2
                if type == 'investment':
                    self.investment_one += total_one2
                if type == 'curr_asset':
                    self.curr_asset_one += total_one2
                if type == 'curr_liabilities':
                    self.curr_liabilities_one += total_one2
                res['total_one'] = total_one2
    
                one_display = '0.00'
                if total_one:
                    one_display =locale.format("%(amount).2f", {'amount': abs(float_round(total_one['balance'],2))},1)
                    if sign * total_one['balance'] < 0:
                        one_display = "(" + one_display + ")"

                res['total_one_display'] = one_display
 
                self.cr.execute("SELECT l.account_id as id, " \
                       " COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                       " FROM account_move_line l" \
                       " WHERE l.account_id = " + str(acc.id) + " and period_id in (" + val_ss + ") " \
                       " GROUP BY l.account_id")
                total_all = self.cr.dictfetchone()
                total_all2 = total_all and float_round(total_all['balance'],2) or 0.00
                if type == 'equity':
                    self.equity_all += total_all2
                if type == 'fixed_asset':
                    self.fixed_asset_all += total_all2
                if type == 'accumulated':
                    self.accumulated_all += total_all2
                if type == 'investment':
                    self.investment_all += total_all2
                if type == 'curr_asset':
                    self.curr_asset_all += total_all2
                if type == 'curr_liabilities':
                    self.curr_liabilities_all += total_all2
                res['total_all'] = total_all2
                all_display = '0.00'
                if total_all:
                    all_display =locale.format("%(amount).2f", {'amount': abs(float_round(total_all['balance'],2))},1)
                    if sign * total_all['balance'] < 0:
                        all_display = "(" + all_display + ")"
                res['total_all_display'] = all_display
                results.append(res)
        return results

report_sxw.report_sxw('report.balance.sheet.report', 'account.account',
    'addons/max_custom_report/account/report/balance_sheet_report.rml', parser=balance_sheet_report, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
