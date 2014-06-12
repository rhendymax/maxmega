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

import copy
from operator import itemgetter
import datetime
from report import report_sxw
from mx import DateTime
import base64

class param_gl_report(osv.osv_memory):
    _name = 'param.gl.report'
    _description = 'General Ledger Report'

    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year',required=True, help='Keep empty for all open fiscal year'),
#        'from_period_id': fields.many2one('account.period', 'From Period',required=True,domain="[('fiscalyear_id','=',fiscalyear_id)]"),
#        'to_period_id': fields.many2one('account.period', 'To Period',required=True,domain="[('fiscalyear_id','=',fiscalyear_id)]"),
#        'account_ids': fields.many2many('account.account', string='Accounts', required=True, domain="[('type','!=','view')]"),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'account_selection': fields.selection([('def','Default'),('input', 'Input'),('selection','Selection')],'Account Filter Selection', required=True),
        'account_default_from':fields.many2one('account.account', 'Account From', domain=[('type','!=','view')], required=False),
        'account_default_to':fields.many2one('account.account', 'Account To', domain=[('type','!=','view')], required=False),
        'account_input_from': fields.char('Account From', size=128),
        'account_input_to': fields.char('Account To', size=128),
        'account_ids' :fields.many2many('account.account', 'report_gl_account_rel', 'report_id', 'account_id', 'Account', domain=[('type','!=','view')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

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

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id' in data['form'] and data['form']['fiscalyear_id'] or False
        result['acount_ids'] = 'account_ids' in data['form'] and data['form']['account_ids'] or False
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['fiscalyear_id', 'account_ids', 'from_period_id', 'to_period_id'], context=context)[0]
        for field in ['fiscalyear_id', 'from_period_id', 'to_period_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        return self._get_tplines(cr, uid, ids, data, context=context)

    def get_date_period(self,cr, uid,form):
        pool = pooler.get_pool(cr.dbname)
        start_period = pool.get('account.period').browse(cr, uid, form['from_period_id']).code
        end_period = pool.get('account.period').browse(cr, uid, form['to_period_id']).code
        date_period = str(start_period) + " To " + str(end_period)
        return l

    def _opening_balance_account(self, cr,uid, account, periods, form,context):
        period_ids = '(' + ','.join( [str(x) for x in periods] ) + ')' #periods
        pool = pooler.get_pool(cr.dbname)
        acc_id = account['id']
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
        query = pool.get('account.move.line')._query_get(cr, uid, context=ctx)
        cr.execute("SELECT sum(debit-credit) "\
        		"FROM account_move_line l "\
        		"WHERE l.account_id = %s AND "+query, (acc_id,))
        opening_amt = cr.fetchone()[0] or 0.0
        return opening_amt 

    def lines(self,cr,uid, account, periods, op_balance, form,context):
        ctx = context.copy()
        pool = pooler.get_pool(cr.dbname)
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['periods'] = periods
        query = pool.get('account.move.line')._query_get(cr,uid, context=ctx)
        acc_id = account['id']
        cr.execute("SELECT l.date, j.code, l.ref, l.name, l.debit, l.credit, p.name as P_name, m.name as move_id "\
            "FROM account_move_line as l "\
            "LEFT JOIN account_journal j ON l.journal_id = j.id "\
            "LEFT JOIN account_move m ON l.move_id = m.id "\
            "LEFT JOIN res_partner p ON l.partner_id = p.id "\
            "WHERE account_id = %s AND "+query+" "\
            "ORDER by l.date", (acc_id,))
        res = cr.dictfetchall()
        sum = op_balance or 0.0
        for l in res:
        	sum += (float(l['debit'] or 0.0) - float(l['credit'] or 0.0))
        	l['progress'] = sum
        return res

    def _sum_debit_account(self,cr,uid, account,periods, form,context):
        pool = pooler.get_pool(cr.dbname)
        ctx = context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['periods'] = periods
        acc_id = account['id']
        query = pool.get('account.move.line')._query_get(cr, uid, context=ctx)
        cr.execute("SELECT sum(debit) "\
            "FROM account_move_line l "\
            "WHERE l.account_id = %s AND "+query, (acc_id,))
        return cr.fetchone()[0] or 0.0

    def _sum_credit_account(self,cr,uid, account,periods, form,context):
        pool = pooler.get_pool(cr.dbname)
        ctx = context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['periods'] = periods
        acc_id = account['id']
        query = pool.get('account.move.line')._query_get(cr,uid,context=ctx)
        cr.execute("SELECT sum(credit) "\
            "FROM account_move_line l "\
            "WHERE l.account_id = %s AND "+query, (acc_id,))
        return cr.fetchone()[0] or 0.0


    def _sum_debit(self,cr,uid,accounts,periods,form,context):
        pool = pooler.get_pool(cr.dbname)
        ctx = context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['periods'] = periods
        acc_id = '(' + ','.join( [str(x) for x in accounts] ) + ')'
        
        query = pool.get('account.move.line')._query_get(cr, uid, context=ctx)
        cr.execute("SELECT sum(debit) "\
            "FROM account_move_line l "\
            "WHERE l.account_id in "+ acc_id +" AND "+query)
        return cr.fetchone()[0] or 0.0

    def _sum_credit(self,cr,uid,accounts,periods,form,context):
        pool = pooler.get_pool(cr.dbname)
        ctx = context.copy()
        ctx['fiscalyear'] = form['fiscalyear_id']
        ctx['periods'] = periods
        acc_id = '(' + ','.join( [str(x) for x in accounts] ) + ')'
        query = pool.get('account.move.line')._query_get(cr,uid, context=ctx)
        cr.execute("SELECT sum(credit) "\
            "FROM account_move_line l "\
            "WHERE l.account_id in "+ acc_id +" AND "+query)
        return cr.fetchone()[0] or 0.0

    def _get_tplines(self, cr, uid, ids,data, context):
        res={}
        result_acc=[]
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        start_period = pool.get('account.period').browse(cr, uid, form['from_period_id']).date_start
        end_period = pool.get('account.period').browse(cr, uid, form['to_period_id']).date_stop
        cr.execute("select id from account_period where date_start BETWEEN '%s' AND '%s' ORDER BY date_start asc" % (start_period, end_period))
        periods = cr.fetchall()
        prds = []
        for prd in periods:
            rds.append(prd[0])

        result_acc=[]
        #acc_id = '(' + ','.join( [str(x) for x in form['account_ids'][0][2]] ) + ')'
        acc_id = '(' + ','.join( [str(x) for x in form['account_ids']] ) + ')'
        cr.execute("SELECT a.id, a.name, a.code "\
            "FROM account_account as a "\
            "WHERE a.id in %s "\
            "ORDER by a.code" % (acc_id))
        accounts = cr.fetchall()
        for account in accounts:
            res = {
                'id' : account[0],
                'name' : account[1],
                'code' : account[2],
            }
            result_acc.append(res)

        all_content_line = ''
        header = ',General ledger ' + " For Period " + str(self.get_date_period(cr, uid,data['form'])) + " \n"
        acc_ids = []
        for result in result_acc:
            opening_balance_amt = self._opening_balance_account(cr,uid, result, prds, data['form'],context)
            header += ',,,,,,,Opening Balance :,' + str(opening_balance_amt) + " \n"
            header += str(result['code']) + "," + str(result['name']) + "\n"
            header += 'Date,Move No.,Code,Ref.,Partner Name,Entry label,Debit,Credit,Progressive balance\n'
            line_acc = self.lines(cr,uid, result, prds, opening_balance_amt, data['form'],context)
            for l in line_acc:
                p_name = name = ''
                p_name = l['p_name']
                p_name = p_name.replace(',',' ')
                name = l['name']
                name = name.replace(',',' ')
                header += str(l['date']) + "," + str(l['move_id']) + "," + str(l['code']) + "," + str(l['ref']) + "," + str(p_name) + "," + str(name) + "," + str(l['debit']) + "," + str(l['credit']) + "," + str(l['progress']) + "\n"
            credit_amount = self._sum_credit_account(cr,uid, result,prds, data['form'],context)
            debit_amount = self._sum_debit_account(cr,uid, result,prds, data['form'],context)
            header += '\n,,,,,,' + str(round(debit_amount,2)) +"," + str(round(credit_amount,2)) + "," + str(round((debit_amount-credit_amount),2)) + " \n"
            acc_ids.append(result['id'])
            print "::: accounts :::", acc_ids
            total_debit_amount = self._sum_debit(cr,uid, acc_ids,prds, data['form'],context)
            total_credit_amount = self._sum_credit(cr,uid, acc_ids,prds, data['form'],context)
            
            header += '\n,,,,,,' + str(round(total_debit_amount,2)) +"," + str(round(total_credit_amount,2)) + "," + str(round((total_debit_amount - total_credit_amount),2)) + " \n"
            
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

    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'date_selection' : 'none_sel',
            'account_selection' : 'def',
    }

param_gl_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
