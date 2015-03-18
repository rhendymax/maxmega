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

class max_profit_and_lost_report(report_sxw.rml_parse):
    _name = 'max.profit.and.lost.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.period_from = data['form']['period_from'] and data['form']['period_from'][0] or False
        self.period_to = data['form']['period_to'] and data['form']['period_to'][0] or False
        return super(max_profit_and_lost_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(max_profit_and_lost_report, self).__init__(cr, uid, name, context=context)
        self.sale_one = 0.00
        self.sale_all = 0.00
        self.expense_one = 0.00
        self.expense_all = 0.00
        self.other_income_one = 0.00
        self.other_income_all = 0.00
        self.other_expense_one = 0.00
        self.other_expense_all = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_sales': self._get_sales,
            'total_sale_one' : self._total_sale_one,
            'total_sale_all' : self._total_sale_all,
            'total_expense_one' : self._total_expense_one,
            'total_expense_all' : self._total_expense_all,
            'total_gross_profit_one' : self._total_gross_profit_one,
            'total_gross_profit_all' : self._total_gross_profit_all,
            'total_summary1_one' : self._total_summary1_one,
            'total_summary1_all' : self._total_summary1_all,
            'total_other_expense_one' : self._total_other_expense_one,
            'total_other_expense_all' : self._total_other_expense_all,
            'total_summary2_one' : self._total_summary2_one,
            'total_summary2_all' : self._total_summary2_all,
            'get_period_from': self._get_period_from,
            'get_period_to': self._get_period_to,
            })

    def _total_sale_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.sale_one,2))},1)
        if -1 * self.sale_one < 0:
            display = "(" + display + ")"
        return display

    def _total_sale_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.sale_all,2))},1)
        if -1 * self.sale_all < 0:
            display = "(" + display + ")"
        return display

    def _total_expense_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.expense_one,2))},1)
        if 1 * self.expense_one < 0:
            display = "(" + display + ")"
        return display

    def _total_expense_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.expense_all,2))},1)
        if 1 * self.expense_all < 0:
            display = "(" + display + ")"
        return display

    def _total_other_expense_one(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.other_expense_one,2))},1)
        if 1 * self.other_expense_one < 0:
            display = "(" + display + ")"
        return display

    def _total_other_expense_all(self):
        display =locale.format("%(amount).2f", {'amount': abs(float_round(self.other_expense_all,2))},1)
        if 1 * self.other_expense_all < 0:
            display = "(" + display + ")"
        return display

    def _total_summary2_one(self):
        summary = (-1 * self.sale_one) - (self.expense_one) + (-1 * self.other_income_one) - (self.other_expense_one)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary2_all(self):
        summary = (-1 * self.sale_all) - (self.expense_all) + (-1 * self.other_income_all)- (self.other_expense_all)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary1_one(self):
        summary = (-1 * self.sale_one) - (self.expense_one) + (-1 * self.other_income_one)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_summary1_all(self):
        summary = (-1 * self.sale_all) - (self.expense_all) + (-1 * self.other_income_all)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(summary,2))},1)
        if summary < 0:
            display = "(" + display + ")"
        return display

    def _total_gross_profit_one(self):
        gross_profit = (-1 * self.sale_one) - (self.expense_one)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(gross_profit,2))},1)
        if gross_profit < 0:
            display = "(" + display + ")"
        return display

    def _total_gross_profit_all(self):
        gross_profit = (-1 * self.sale_all) - (self.expense_all)
        display =locale.format("%(amount).2f", {'amount': abs(float_round(gross_profit,2))},1)
        if gross_profit < 0:
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
                if type == 'income':
                    self.sale_one += total_one2
                elif type == 'expense':
                    self.expense_one += total_one2
                elif type == 'other_income':
                    self.other_income_one += total_one2
                elif type == 'other_expense':
                    self.other_expense_one += total_one2
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
                if type == 'income':
                    self.sale_all += total_all2
                elif type == 'expense':
                    self.expense_all += total_all2
                elif type == 'other_income':
                    self.other_income_all += total_all2
                elif type == 'other_expense':
                    self.other_expense_all += total_all2
                res['total_all'] = total_all2
                all_display = '0.00'
                if total_all:
                    all_display =locale.format("%(amount).2f", {'amount': abs(float_round(total_all['balance'],2))},1)
                    if sign * total_all['balance'] < 0:
                        all_display = "(" + all_display + ")"
                res['total_all_display'] = all_display
                results.append(res)
        return results

report_sxw.report_sxw('report.max.profit.and.lost.report', 'account.account',
    'addons/max_custom_report/account/report/max_profit_and_lost_report.rml', parser=max_profit_and_lost_report, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
