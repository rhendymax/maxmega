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

class maxmega_trial_balance_report(osv.osv_memory):
    _name = 'maxmega.trial.balance.report'
    _description = 'Trial Balance Report'

    def onchange_chart_id(self, cr, uid, ids, chart_account_id=False, context=None):
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(cr, uid, chart_account_id, context=context).company_id.id
        return {'value': {'company_id': company_id}}

    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by"),
        'period_from': fields.many2one('account.period', 'Start Period', required=True),
        'period_to': fields.many2one('account.period', 'End Period', required=True),
        'journal_ids': fields.many2many('account.journal', string='Journals', required=True),
        'date_from': fields.date("Start Date"),
        'date_to': fields.date("End Date"),
        'target_move': fields.selection([('posted', 'All Posted Entries'),('all', 'All Entries'),], 'Target Moves', required=True),
        'display_account': fields.selection([('all','All'), ('movement','With movements'),('not_zero','With balance is not equal to 0'),
                                            ],'Display Accounts', required=True),
        'journal_ids': fields.many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id', 'Journals', required=True),
        'account_ids': fields.many2many('account.account', string='Accounts', required=True, domain="[('type','!=','view')]"),
    }

    def _check_company_id(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context=context):
            company_id = wiz.company_id.id
            if wiz.fiscalyear_id and company_id != wiz.fiscalyear_id.company_id.id:
                return False
            if wiz.period_from and company_id != wiz.period_from.company_id.id:
                return False
            if wiz.period_to and company_id != wiz.period_to.company_id.id:
                return False
        return True

    _constraints = [
        (_check_company_id, 'The fiscalyear, periods or chart of account chosen have to belong to the same company.', ['chart_account_id','fiscalyear_id','period_from','period_to']),
    ]


    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(maxmega_trial_balance_report, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=False)
        if context.get('active_model', False) == 'account.account' and view_id:
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='chart_account_id']")
            for node in nodes:
                node.set('readonly', '1')
                node.set('help', 'If you print the report from Account list/form view it will not consider Charts of account')
            res['arch'] = etree.tostring(doc)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {'value': {}}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False ,'date_to': False}
        if filter == 'filter_date':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.special = false
                               ORDER BY p.date_start ASC, p.special ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods =  [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res

    def _get_account(self, cr, uid, context=None):
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        now = time.strftime('%Y-%m-%d')
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, [('date_start', '<', now), ('date_stop', '>', now)], limit=1 )
        return fiscalyears and fiscalyears[0] or False

    def _get_all_journal(self, cr, uid, context=None):
        return self.pool.get('account.journal').search(cr, uid ,[])

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id' in data['form'] and data['form']['fiscalyear_id'] or False
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['account_ids'] = 'account_ids' in data['form'] and data['form']['account_ids'] or False
        result['chart_account_id'] = 'chart_account_id' in data['form'] and data['form']['chart_account_id'] or False
        #if data['form']['filter'] == 'filter_date':
        #    result['date_from'] = data['form']['date_from']
        #    result['date_to'] = data['form']['date_to']
        #elif data['form']['filter'] == 'filter_period':
        result['filter'] = 'filter_period'
        if not data['form']['period_from'] or not data['form']['period_to']:
            raise osv.except_osv(_('Error'),_('Select a starting and an ending period'))
        result['period_from'] = data['form']['period_from']
        result['period_to'] = data['form']['period_to']
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from','date_to','fiscalyear_id', 'journal_ids', 'period_from', 'period_to','filter','chart_account_id', 'target_move','account_ids'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id', 'period_from', 'period_to','account_ids']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['filter'] = 'filter_period'
        data['form']['used_context'] = used_context
        return self._print_report(cr, uid, ids, data, context=context)

    def pre_print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data['form'].update(self.read(cr, uid, ids, ['display_account'], context=context)[0])
        return data

    def _print_report(self, cr, uid, ids, data, context=None):
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml', 'report_name': 'maxmega.trial.balance', 'datas': data}

    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'journal_ids': _get_all_journal,
            'filter': 'filter_no',
            'chart_account_id': _get_account,
            'target_move': 'posted',
            'journal_ids': [],
            'display_account': 'movement',
    }

maxmega_trial_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: