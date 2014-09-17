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
import pooler
import base64
from tools import float_round, float_is_zero, float_compare

class param_receipt_register_by_deposit_bank(osv.osv_memory):
    _name = 'param.receipt.register.by.deposit.bank'
    _description = 'Param Receipt Register By Deposit Bank'
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'journal_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Bank Filter Selection', required=True),
        'journal_default_from':fields.many2one('account.journal', 'Bank From', domain=[('type','in',('bank','cash'))], required=False),
        'journal_default_to':fields.many2one('account.journal', 'Bank To', domain=[('type','in',('bank','cash'))], required=False),
        'journal_input_from': fields.char('Bank From', size=128),
        'journal_input_to': fields.char('Bank To', size=128),
        'journal_ids' :fields.many2many('account.journal', 'report_receipt_deposit_bank_rel', 'report_id', 'journal_id', 'Bank', domain=[('type','in',('bank', 'cash'))]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'report_type' : 'receivable',
        'date_selection': 'none_sel',
        'journal_selection': 'all_vall',
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
        datas['model'] = 'param.payment.register.by.deposit.bank'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.payment.register.report_landscape',
            'datas': datas,
            'nodestroy':True,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
                                                'journal_selection','journal_default_from','journal_default_to', 'journal_input_from','journal_input_to','journal_ids' \
                                                ], context=context)[0]
        for field in ['date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
                                                'journal_selection','journal_default_from','journal_default_to', 'journal_input_from','journal_input_to','journal_ids'\
                    ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self.pool.get('param.payment.register.by.deposit.bank')._build_contexts(cr, uid, ids, data, 'receivable', context=context)

        return self.pool.get('param.payment.register.by.deposit.bank')._get_tplines(cr, uid, ids, used_context, 'receivable', context=context)

param_receipt_register_by_deposit_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
