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

from osv import fields, osv
import time

class param_trial_balance_report(osv.osv_memory):
    _name = 'param.trial.balance.report'
    _description = 'Param Trial Balance Report'

    _columns = {
        'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)]),
        'target_move': fields.selection([('posted', 'All Posted Entries'),('all', 'All Entries'),], 'Target Moves', required=True),
        'acc_search_vals': fields.selection([('code','Account Code'),('name', 'Account Name')],'Account Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Acc Filter Selection', required=True),
        'account_default_from':fields.many2one('account.account', 'Account From', domain=[('type','<>','view')], required=False),
        'account_default_to':fields.many2one('account.account', 'Account To', domain=[('type','<>','view')], required=False),
        'account_input_from': fields.char('Account From', size=128),
        'account_input_to': fields.char('Account To', size=128),
        'account_ids' :fields.many2many('account.account', 'acc_trial_balance_rel', 'report_id', 'partner_id', 'Account', domain=[('type','<>','view')]),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_to': fields.date("To Date"),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_to': fields.char('Period To', size=128),

    }

    def _get_account(self, cr, uid, context=None):
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False)], limit=1)
        return accounts and accounts[0] or False

    _defaults = {
        'date_selection': 'none_sel',
        'acc_search_vals': 'code',
        'filter_selection': 'all_vall',
        'chart_account_id': _get_account,
        'target_move': 'posted',
        
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

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.trial.balance.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'trial.balance.report_landscape',
            'datas': datas,
        }

param_trial_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
