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
from lxml import etree
from osv import fields, osv
from tools.translate import _
import pooler
from datetime import datetime
from mx import DateTime as dt
from mx.DateTime import RelativeDateTime as rdt
import copy
from operator import itemgetter
from report import report_sxw
import base64
from tools import float_round, float_is_zero, float_compare

class param_gl_report(osv.osv_memory):
    _name = 'param.gl.report'
    _description = 'General Ledger Report'
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'account_search_vals': fields.selection([('code','Account Code'),('name', 'Account Name')],'Account Search Values', required=True),
        'account_selection': fields.selection([('def','Default'),('input', 'Input'),('selection','Selection')],'Account Filter Selection', required=True),
        'account_default_from':fields.many2one('account.account', 'Account From', domain=[('type','!=','view')], required=False),
        'account_default_to':fields.many2one('account.account', 'Account To', domain=[('type','!=','view')], required=False),
        'account_input_from': fields.char('Account From', size=128),
        'account_input_to': fields.char('Account To', size=128),
        'account_ids' :fields.many2many('account.account', 'report_gl_account_rel', 'report_id', 'account_id', 'Account', domain=[('type','!=','view')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
#            'fiscalyear_id': _get_fiscalyear,
            'date_selection' : 'none_sel',
            'account_search_vals': 'code',
            'account_selection' : 'def',
    }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['fiscalyear_id','date_selection', 'date_from', 'date_to','period_default_from','period_default_to', \
                                                'period_filter_selection','period_input_from','period_input_to','account_search_vals','account_selection','account_default_from','account_default_to', 'account_input_from','account_input_to','account_ids' \
                                                ], context=context)[0]
        for field in ['fiscalyear_id','date_selection', 'date_from', 'date_to','period_default_from','period_default_to', \
                                                'period_filter_selection','period_input_from','period_input_to','account_search_vals','account_selection','account_default_from','account_default_to', 'account_input_from','account_input_to','account_ids' \
                                                ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.gl.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'general.ledger.report_landscape',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        res = {}
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        account_fiscalyear_obj = self.pool.get('account.fiscalyear')
        result['fiscal_year'] = data['form']['fiscalyear_id'] or ''
        fiscal_year_name =  data['form']['fiscalyear_id'] and account_fiscalyear_obj.browse(cr, uid, data['form']['fiscalyear_id']) \
                            and account_fiscalyear_obj.browse(cr, uid, data['form']['fiscalyear_id']).name or False
        result['fiscal_year_name'] = fiscal_year_name
        qry_acc = ''
        val_acc = []
        qry_acc = "type <> 'view'"
        val_acc.append(('type','<>','view'))
        partner_ids = False
        account_ids = False
        account_selection = False
        
        account_default_from = data['form']['account_default_from'] or False
        account_default_to = data['form']['account_default_to'] or False
        account_input_from = data['form']['account_input_from'] or False
        account_input_to = data['form']['account_input_to'] or False
        account_default_from_str = account_default_to_str = ''
        account_input_from_str = account_input_to_str= ''
        data_search = data['form']['account_search_vals']
        
        if data_search == 'code':
            result['data_search_output'] = 'Code'
            if data['form']['account_selection'] == 'def':
                data_found = False
                if account_default_from and account_obj.browse(cr, uid, account_default_from) and account_obj.browse(cr, uid, account_default_from).code:
                    account_default_from_str = account_obj.browse(cr, uid, account_default_from).code
                    data_found = True
                    val_acc.append(('code', '>=', account_obj.browse(cr, uid, account_default_from).code))
                if account_default_to and account_obj.browse(cr, uid, account_default_to) and account_obj.browse(cr, uid, account_default_to).code:
                    account_default_to_str = account_obj.browse(cr, uid, account_default_to).code
                    data_found = True
                    val_acc.append(('code', '<=', account_obj.browse(cr, uid, account_default_to).code))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(cr, uid, val_acc, order='code ASC')
            elif data['form']['account_selection'] == 'input':
                data_found = False
                if account_input_from:
                    account_input_from_str = account_input_from
                    cr.execute("select code " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "code ilike '" + str(account_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        account_input_to_str = account_input_to
                        data_found = True
                        val_acc.append(('code', '>=', qry['code']))
                if account_input_to:
                    account_input_to_str = account_input_to
                    cr.execute("select code " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "code ilike '" + str(account_input_to) + "%' " \
                                    "order by code desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('code', '<=', qry['code']))
                #print val_part
                account_selection = '"' + account_input_from_str + '" - "' + account_input_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(cr, uid, val_acc, order='code ASC')
            elif data['form']['account_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  account_obj.browse(cr, uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.code) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'
        
        elif data_search == 'name':
            result['data_search_output'] = 'Name'
            if data['form']['account_selection'] == 'def':
                data_found = False
                if account_default_from and account_obj.browse(cr, uid, account_default_from) and account_obj.browse(cr, uid, account_default_from).name:
                    account_default_from_str = account_obj.browse(cr, uid, account_default_from).name
                    data_found = True
                    val_acc.append(('name', '>=', account_obj.browse(cr, uid, account_default_from).name))
                if account_default_to and account_obj.browse(cr, uid, account_default_to) and account_obj.browse(cr, uid, account_default_to).name:
                    account_default_to_str = account_obj.browse(cr, uid, account_default_to).name
                    data_found = True
                    val_acc.append(('name', '<=', account_obj.browse(cr, uid, account_default_to).name))
                account_selection = '"' + account_default_from_str + '" - "' + account_default_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(cr, uid, val_acc, order='name ASC')
            elif data['form']['account_selection'] == 'input':
                data_found = False
                if account_input_from:
                    account_input_from_str = account_input_from
                    cr.execute("select name " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "name ilike '" + str(account_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        account_input_to_str = account_input_to
                        data_found = True
                        val_acc.append(('name', '>=', qry['name']))
                if account_input_to:
                    account_input_to_str = account_input_to
                    cr.execute("select name " \
                                    "from account_account "\
                                    "where " + qry_acc + " and " \
                                    "name ilike '" + str(account_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_acc.append(('name', '<=', qry['name']))
                #print val_part
                account_selection = '"' + account_input_from_str + '" - "' + account_input_to_str + '"'
                if data_found:
                    account_ids = account_obj.search(cr, uid, val_acc, order='name ASC')
            elif data['form']['account_selection'] == 'selection':
                acc_ids = ''
                if data['form']['account_ids']:
                    for aco in  account_obj.browse(cr, uid, data['form']['account_ids']):
                        acc_ids += '"' + str(aco.name) + '",'
                    account_ids = data['form']['account_ids']
                account_selection = '[' + acc_ids +']'
        
        period_default_from = data['form']['period_default_from'] or False
        period_default_from = period_default_from and period_obj.browse(cr, uid, period_default_from) or False
        period_default_to = data['form']['period_default_to'] or False
        period_default_to = period_default_to and period_obj.browse(cr, uid, period_default_to) or False

        period_input_from = data['form']['period_input_from'] or False
        period_input_to = data['form']['period_input_to'] or False

        if data['form']['date_selection'] == 'none_sel':
            result['period_ids'] = False
            result['date_from'] = False
            result['date_to'] = False
            result['date_search'] = ''
        elif data['form']['date_selection'] == 'period_sel':
            result['date_search'] = 'period'
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
                result['period_ids'] = period_obj.search(cr, uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
                if period_input_from:
                    period_from_txt = period_input_from
                    cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '>=', qry['code']))
                if period_input_to:
                    period_to_txt = period_input_to
                    cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_to) + "%' " \
                                    "order by code limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '<=', qry['code']))
                result['period_ids'] = period_obj.search(cr, uid, val_period)
            result['date_showing'] = '"' + period_from_txt + '" - "' + period_to_txt + '"'
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['period_ids'] = False
            result['date_search'] = 'date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#        self.report_type = data['form']['report_type']
        result['account_ids'] = account_ids
        result['account_selection'] = account_selection
        return result

    def onchange_date_selection(self, cr, uid, ids, date_selection, context=None):
        if context is None:
            context = {}
        res = {}
        if date_selection:
            if date_selection == 'period_sel':
                res['value'] = {'period_filter_selection': 'def',
                                 }
            else:
                res['value'] = {'period_filter_selection': False,
                                 }
        return res


    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        cr = cr
        uid = uid
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        
        period_obj = self.pool.get('account.period')
        invoice_obj = self.pool.get('account.invoice')
        aml_obj = self.pool.get('account.move.line')
        partner_obj = self.pool.get('res.partner')

        results = []
        results1 = []
        fiscal_year = form['fiscal_year'] or ''
        period_ids = form['period_ids'] or False
        account_ids = form['account_ids'] or False
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        
        header += 'General Ledger Report' + " \n"
        header += ('account_selection' in form and 'Account ' + form['data_search_output'] + ' Search : ' + form['account_selection'] + " \n") or ''
        
        fiscal_year_name = form['fiscal_year_name'] or False
        header += (fiscal_year_name and 'Fiscal Year : ' + str(fiscal_year_name) + " \n") or ''
        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += 'Trans Date;Vch. No.;Reference No;Line Item Description;Amount Currency;CurrencyDebit;Credit' + " \n"
        
        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)
        if fiscal_year:
            if min_period:
                if fiscal_year != period_obj.browse(cr, uid, min_period[0]).fiscalyear_id.id:
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
                if fiscal_year != period_obj.browse(cr, uid, max_period[0]).fiscalyear_id.id:
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
                balance = 0.00
                closing = 0.00
                closing_inv = 0.00
                if qry4:
                    for u in qry4:
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
                            "am.name as am_name " \
                            "from account_move_line aml "\
                            "left join account_move am on aml.move_id = am.id "\
                            "left join account_voucher av on am.id = av.move_id "\
                            "left join account_account aa on aml.account_id = aa.id "\
                            "left join res_partner rp on aml.partner_id = rp.id "\
                            "left join account_period ap on aml.period_id = ap.id "\
                            "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                            "left join account_journal aj on aml.journal_id = aj.id "\
                            "left join res_company rc on aml.company_id = rc.id " \
                            "left join res_currency rcurr on aml.currency_id = rcurr.id " \
                            "left join res_currency rcur on rc.currency_id = rcur.id " \
                            "where " \
                            "am.state in ('draft', 'posted') " \
                            "and ap.id = " + str(u['id']) + " "\
                            + date_to_qry2 + \
                            "and aml.account_id = " + str(s['id']) + " "\
                            "order by aa.code, af.name, ap.date_start, aml.date")
                        
                        qry5 = cr.dictfetchall()
                        val_ids2 = []
                        if qry5:
                            for v in qry5:
                                total_debit_credit = float_round((v['aml_debit'] - v['aml_credit']),2)

                                balance += total_debit_credit

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
                                    ref = (v['aml_ref'] and  '@Ref : ' + v['aml_ref'] + ' ') or ''
                                    jour_type = v['jour_type'] or False
                                    
                                    if jour_type and jour_type in ('bank', 'cash'):
                                        jour_name = (v['jour_name'] and  '@Payment Method : ' + v['jour_name'] + ' ') or ''
                                    else:
                                        jour_name = ''
                                    cheque_no = (v['cheque_no'] and  '@Cheque No : ' + v['cheque_no'] + ' ') or ''
                                    val_ids2.append({
                                        'aml_date' : v['aml_date'],
                                        'am_name' : v['am_name'],
                                        'aml_ref' : part_name + jour_name + cheque_no + ref,
                                        'aml_name' : v['aml_name'],
                                        'aml_amount': amount_currency,
                                        'aml_currency': home_currency,
                                        'aml_debit' : v['aml_debit'],
                                        'aml_credit' : v['aml_credit'],
                                        })
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
                results1.append({
                    'acc_name' : s['name'],
                    'acc_code' : s['code'],
                    'period_end': period_end,
                    'closing' : balance,
                    'val_ids' : val,
                    })
                
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['acc_code']) or []
        debit_total = credit_total = grand_total = 0
        for rs1 in results1:
            header += '[' + str(rs1['acc_code']) + '] ' + str(rs1['acc_name']) + ' \n'
            total_home_amt = 0
            for rs2 in rs1['val_ids']:
                header += str(rs2['fiscalyear_name']) + ';' + str(rs2['period_code']) + ';;' + 'Opening Balance' + ';;;;;' \
                        + str(rs2['opening_balance']) + ' \n'
                ttl_debit = ttl_credit = 0
                for rs3 in rs2['val_ids2']:
                    ttl_debit += float_round(rs3['aml_debit'],2)
                    ttl_credit += float_round(rs3['aml_credit'],2)
                    header += str(rs3['aml_date']) + ';' + str(rs3['am_name']) + ';' + str(rs3['aml_ref']) + ';' \
                        + str(rs3['aml_name']) + ';' + str(rs3['aml_amount']) + ';' + str(rs3['aml_currency']) + ';' + str(rs3['aml_debit']) + ';' + str(rs3['aml_credit']) + ' \n'
                debit_total += ttl_debit
                credit_total += ttl_debit
                header += 'Total For ' + str(rs1['acc_code']) + ';;;;;' + 'PERIOD CLOSING AS AT ' + str(rs2['period_end']) + ';' \
                + str(ttl_debit) + ';' + str(ttl_credit) + ' \n'
            grand_total += rs1['closing']
            closing = rs1['closing']
            if float_is_zero(closing, precision_digits=2):
                closing = 0.00
            header += 'Closing Balance For ' + str(rs1['acc_code']) + ';;;' + '     PERIOD CLOSING AS AT ' + str(rs1['period_end']) + ';;;' + str(closing) + ' \n \n'
        header += 'Report Total ;;;;' + str(debit_total) + ';' + str(credit_total) + ' \n'
        if float_is_zero(grand_total, precision_digits=2):
            grand_total = 0.00
        header += ';;;Balance;;;' + str(grand_total) + ' \n'
        
        all_content_line += header
        csv_content = ''

        filename = 'General ledger Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','param_gl_result_data_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'name':'General Ledger Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'param.gl.report',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target':'new',
            'res_id':ids[0],
            }
param_gl_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
