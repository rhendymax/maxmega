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
from tigernix_common_report_header import tigernix_common_report_header

class maxmega_trial_balance(report_sxw.rml_parse, tigernix_common_report_header):
    _name = 'report.maxmega.trial.balance'

    def __init__(self, cr, uid, name, context=None):
        super(maxmega_trial_balance, self).__init__(cr, uid, name, context=context)
        self.sum_opening_balance = 0.00
        self.sum_balance = 0.00
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.result_acc = []
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit_total': self._sum_debit_total,
            'sum_credit_total': self._sum_credit_total,
            'sum_opening_balance_total': self._sum_opening_balance_total,
            'sum_balance_total': self._sum_balance_total,
            'get_fiscalyear':self._get_fiscalyear,
            'get_filter': self._get_filter,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period ,
            'get_account': self._get_account,
            'get_journal': self._get_journal,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_target_move': self._get_target_move,
        })
        self.context = context

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        return super(maxmega_trial_balance, self).set_context(objects, data, new_ids, report_type=report_type)

    def _get_account(self, data):
        if data['model']=='account.account':
            return self.pool.get('account.account').browse(self.cr, self.uid, data['form']['id']).company_id.name
        return super(maxmega_trial_balance ,self)._get_account(data)

    def _opening_balance_account(self, cr,uid, account_id, periods, form,context):
		period_ids = '(' + ','.join( [str(x) for x in periods] ) + ')' #periods
		#pool = pooler.get_pool(cr.dbname)
		acc_id = account_id #account['id']
		cr.execute("select date_start,date_stop from account_period where id in %s" % (period_ids))
		dates = cr.fetchall()
		start_date = dates[0][0]
		for x in dates:
		  if start_date > x[0]:
		     start_date = x[0]
		cr.execute("select id from account_period where date_start < '%s'" % (start_date))
		periods = cr.fetchall()
		prd_ids = []
		if periods:
		   for x in periods:
		     prd_ids.append(x[0])
		else:
		     prd_ids.append(0)
		ctx = context.copy()
		cr.execute("UPDATE account_move_line SET credit = 0.00 WHERE credit is null")
		cr.execute("UPDATE account_move_line SET debit = 0.00 WHERE debit is null")
		cr.execute("UPDATE account_move_line SET partner_id = 1 WHERE partner_id is null")
		ctx['fiscalyear'] = form['fiscalyear_id']
		ctx['periods'] = prd_ids
		query = self.pool.get('account.move.line')._query_get(cr,uid, context=ctx)
		#print ":::::",query
		cr.execute("SELECT sum(debit-credit) "\
				"FROM account_move_line l "\
				"WHERE l.account_id = %s AND "+query, (acc_id,))
		opening_amt = cr.fetchone()[0] or 0.0
		return opening_amt 

    def _sum_debit_account(self,cr,uid, account,periods, form,context):
		#pool = pooler.get_pool(cr.dbname)
		ctx = context.copy()
		ctx['fiscalyear'] = form['fiscalyear_id']
		ctx['periods'] = periods
		acc_id = account['id']
		query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)
		cr.execute("SELECT sum(debit) "\
				"FROM account_move_line l "\
				"WHERE l.account_id = %s AND "+query, (acc_id,))
		return cr.fetchone()[0] or 0.0

    def _sum_credit_account(self,cr,uid, account,periods, form,context):
		#pool = pooler.get_pool(cr.dbname)
		ctx = context.copy()
		ctx['fiscalyear'] = form['fiscalyear_id']
		ctx['periods'] = periods
		acc_id = account['id']
		query = self.pool.get('account.move.line')._query_get(cr,uid,context=ctx)
		cr.execute("SELECT sum(credit) "\
				"FROM account_move_line l "\
				"WHERE l.account_id = %s AND "+query, (acc_id,))
		return cr.fetchone()[0] or 0.0

    def lines(self, form, ids=[], done=None):#, level=1):
        obj_account = self.pool.get('account.account')
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}
        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        #if form['filter'] == 'filter_period':
        #    ctx['period_from'] = form['period_from']
        #    ctx['period_to'] = form['period_to']
        ctx['state'] = form['target_move']
        parents = ids
        #child_ids = obj_account._get_children_and_consol(self.cr, self.uid, ids, ctx)
        child_ids = obj_account.search(self.cr, self.uid,[('type','!=','view')])
        if child_ids:
            ids = child_ids
        account_ids = form['account_ids']
        if len(account_ids) == 0:
            accounts = obj_account.read(self.cr, self.uid, ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id'], ctx)
        else:
            accounts = obj_account.read(self.cr, self.uid, account_ids, ['type','code','name','debit','credit','balance','parent_id','level','child_id'], ctx)

        disp_acc = form['display_account']
        start_period = self.pool.get('account.period').browse(self.cr, self.uid, form['period_from']).date_start
        end_period = self.pool.get('account.period').browse(self.cr, self.uid, form['period_to']).date_stop

        self.cr.execute("select id from account_period where date_start BETWEEN '%s' AND '%s' ORDER BY date_start asc" % (start_period, end_period))
        periods = self.cr.fetchall()
        prds = []
        for prd in periods:
            prds.append(prd[0])
        for account in accounts:
            if account['id'] in done:
                continue
            done[account['id']] = 1
            currency_obj = self.pool.get('res.currency')
            acc_id = self.pool.get('account.account').browse(self.cr, self.uid, account['id'])
            currency = acc_id.currency_id and acc_id.currency_id or acc_id.company_id.currency_id
            opening_balance_amt = self._opening_balance_account(self.cr,self.uid, account['id'], prds,form,ctx)
            credit_amount = self._sum_credit_account(self.cr,self.uid, account,prds,form,ctx)
            debit_amount = self._sum_debit_account(self.cr,self.uid, account,prds,form,ctx)
            balance_amount = opening_balance_amt + (debit_amount - credit_amount)
            res = {
                'id': account['id'],
                'type': account['type'],
                'code': account['code'],
                'name': account['name'],
                'level': account['level'],
                'opening_balance': opening_balance_amt,
                'debit': debit_amount, #account['debit'],
                'credit': credit_amount, #account['credit'],
                'balance': balance_amount, #account['balance'],
                'parent_id': account['parent_id'],
                'bal_type': '',
            }
            self.sum_debit += debit_amount #account['debit']
            self.sum_credit += credit_amount #account['credit']
            self.sum_opening_balance += opening_balance_amt
            self.sum_balance += balance_amount
            if disp_acc == 'movement':
                if not currency_obj.is_zero(self.cr, self.uid, currency, res['credit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['debit']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']) or not currency_obj.is_zero(self.cr, self.uid, currency, res['opening_balance']):
                    self.result_acc.append(res)
            elif disp_acc == 'not_zero':
                if not currency_obj.is_zero(self.cr, self.uid, currency, res['balance']):
                    self.result_acc.append(res)
            else:
                self.result_acc.append(res)

        #for parent in parents:
        #        if parent in done:
        #            continue
        #        done[parent] = 1
        #        _process_child(accounts,form['display_account'],parent)
        return self.result_acc

    def _sum_credit_total(self):
        return self.sum_credit

    def _sum_debit_total(self):
        return self.sum_debit

    def _sum_opening_balance_total(self):
        return self.sum_opening_balance

    def _sum_balance_total(self):
        return self.sum_balance

report_sxw.report_sxw('report.maxmega.trial.balance', 'account.account', 'addons/maxmega_reports/general_report/account_trial_balance.rml', parser=maxmega_trial_balance, header="internal")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
