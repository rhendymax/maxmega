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
 
import tools
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
from datetime import datetime
import time
import math

from tools import float_round, float_is_zero, float_compare

class max_journal_entries(osv.osv):
    _name = 'max.journal.entries'
    _description = 'Journal Entries'

    _columns = {
        'name': fields.char('Number', size=64, readonly=True),
        'ref': fields.char('Reference', size=64),
        'period_id': fields.many2one('account.period', 'Period', required=True, states={'posted':[('readonly',True)]}),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, states={'posted':[('readonly',True)]}),
        'state': fields.selection([('draft','Draft'), ('posted','Posted'),('cancel','Cancel')], 'State', required=True, readonly=True,
            help='All manually created new journal entries are usually in the state \'Unposted\', but you can set the option to skip that state on the related journal. In that case, they will be behave as journal entries automatically created by the system on document validation (invoices, bank statements...) and will be created in \'Posted\' state.'),
        'date': fields.date('Date', required=True, states={'posted':[('readonly',True)]}, select=True),
        'line_id': fields.one2many('max.journal.lines.entries', 'move_id', 'Entries', states={'posted':[('readonly',True)]}),
        'move_id':fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
    }

    def _get_period(self, cr, uid, context=None):
        periods = self.pool.get('account.period').find(cr, uid)
        if periods:
            return periods[0]
        return False

    _defaults = {
        'period_id': _get_period,
        'date': fields.date.context_today,
        'state': 'draft',
    }

    def account_move_get(self, cr, uid, voucher_id, context=None):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        voucher_brw = self.pool.get('max.journal.entries').browse(cr,uid,voucher_id,context)
        if voucher_brw.name:
            name = voucher_brw.name
        elif voucher_brw.journal_id.sequence_id:
            name = seq_obj.next_by_id(cr, uid, voucher_brw.journal_id.sequence_id.id)
        else:
            raise osv.except_osv(_('Error !'),
                        _('Please define a sequence on the journal !'))
        if not voucher_brw.ref:
            ref = name.replace('/','')
        else:
            ref = voucher_brw.ref

        move = {
            'name': name,
            'journal_id': voucher_brw.journal_id.id,
            'narration': False,
            'date': voucher_brw.date,
            'ref': ref,
            'period_id': voucher_brw.period_id and voucher_brw.period_id.id or False
        }
        return move

    def unlink(self, cr, uid, ids, context=None):
        entries = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in entries:
            if s['state'] in ['draft','cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('In order to delete a Journal Entries, it must be cancelled first!'))

        return super(max_journal_entries, self).unlink(cr, uid, unlink_ids, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')

        for voucher in self.browse(cr, uid, ids, context=context):
            recs = []
            if voucher.move_id:
                move_pool.button_cancel(cr, uid, [voucher.move_id.id])
                move_pool.unlink(cr, uid, [voucher.move_id.id])
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True

    def set_to_draft(self, cr, uid, ids, context=None):
        res = {
            'state':'draft',
        }
        self.write(cr, uid, ids, res)
        return True

    def button_validate(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''

        if context is None:
            context = {}
        '''Validation'''
        for voucher in self.browse(cr, uid, ids, context=context):
            total_debit = 0.0
            total_credit = 0.0
            for lines in voucher.line_id:
                total_debit += lines.debit_home
                total_credit += lines.credit_home
                if lines.debit_home < 0:
                    raise osv.except_osv(_('Error'), _('No Negatif Allowed for Debit'))
                if lines.credit_home < 0:
                    raise osv.except_osv(_('Error'), _('No Negatif Allowed for Credit'))
                if lines.debit_home <= 0 and lines.credit_home <= 0:
                    raise osv.except_osv(_('Error'), _('Please remove lines with zero or below zero for debit and credit'))
            if total_debit != total_credit:
                raise osv.except_osv(_('Error'), _('Total Debit And Credit Not Balance'))
#
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        user_pool = self.pool.get('res.users')
        '''Operated'''
        company_currency = user_pool.browse(cr, uid, uid, context=None).company_id.currency_id.id
            
        for vch in self.browse(cr, uid, ids, context=context):
#            # we select the context to use accordingly if it's a multicurrency case or not
#            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = {}
            ctx.update({'date': vch.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
#            
#            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
#            raise osv.except_osv(_('Error'), _('Work'))
#
#            # Create the first line of the voucher

            for ln in vch.line_id:
                current_currency = ln.currency_id and ln.currency_id.id or company_currency
                move_line = {
                        'name': vch.name or '/',
                        'debit': ln.debit_home,
                        'credit': ln.credit_home,
                        'account_id': ln.account_id.id,
                        'move_id': move_id,
                        'journal_id': vch.journal_id.id,
                        'period_id': vch.period_id.id,
                        'partner_id': False,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and (ln.debit - ln.credit) or 0.0,
                        'date': vch.date,
                        'date_maturity': vch.date,
                        'cur_date' : vch.date,
                        'exrate' : ln.ex_rate,
                    }
                move_line_pool.create(cr, uid, move_line, context)

#
            self.write(cr, uid, [vch.id], {
                'move_id': move_id,
                'state': 'posted',
                'name': name,
            })
#
            if vch.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
        return True

max_journal_entries()

class max_journal_lines_entries(osv.osv):
    _name = 'max.journal.lines.entries'
    _description = 'Journal Lines Entries'

    def _rate(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        user_pool = self.pool.get('res.users')
        res_currency_rate_obj = self.pool.get("res.currency.rate")
        for obj in self.browse(cr, uid, ids, context=context):
            company_currency = user_pool.browse(cr, uid, uid, context=None).company_id.currency_id.id
            current_currency = obj.currency_id and obj.currency_id.id or company_currency
            cur_date = obj.move_id.date or False
            if current_currency and cur_date:
                res_currency_rate_ids = res_currency_rate_obj.search(cr, uid, [('currency_id', '=', current_currency), ('name', '<=', cur_date)], order='name DESC', limit=1)
                if res_currency_rate_ids:
                    res[obj.id] = res_currency_rate_obj.browse(cr, uid, res_currency_rate_ids[0], context=context).rate
                else:
                    res[obj.id] = 0
            else:
                res[obj.id] = 0
        return res

    _columns = {
        'move_id': fields.many2one('max.journal.entries', 'Move', ondelete="cascade", help="The move of this entry line.", select=2, required=True),
        'account_id': fields.many2one('account.account', 'Account', required=True, ondelete="cascade", domain=[('type','<>','view'), ('type', '<>', 'closed')], select=2),
        'debit': fields.float('Debit', digits=(12,2)),
        'credit': fields.float('Credit', digits=(12,2)),
        'debit_home': fields.float('Debit Home', digits=(12,2)),
        'credit_home': fields.float('Credit Home', digits=(12,2)),
        'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
        'ex_rate': fields.function(_rate, type='float', digits=(12,6), string='Currency Rate'),
   }

    def onchange_currency(self, cr, uid, ids, date, currency_id, debit, credit, context=None):
        res = {'value': {'debit': 0.0, 'debit_home': 0.0}}
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')

        if not date:
            res['warning'] = {'title': _('Warning'), 'message': _('You have to select a date in the form !\nPlease set one.')}
            return res
        
        debit = round(debit,2)
        credit = round(credit,2)
        res['value'].update({'debit': debit, 'credit': credit})
        
        company_currency = user_pool.browse(cr, uid, uid, context=None).company_id.currency_id.id
        context_multi_currency = {}
        context_multi_currency.update({'date': date})
        if currency_id:
            if currency_id == company_currency:
                res['value'].update({'debit_home': debit, 'credit_home': credit})
            else:
                debit_home = currency_pool.compute(cr, uid, currency_id, company_currency, debit, context=context_multi_currency)
                credit_home = currency_pool.compute(cr, uid, currency_id, company_currency, credit, context=context_multi_currency)

                res['value'].update({'debit_home': round(debit_home,2),'credit_home': round(credit_home,2)})
        else:
            res['value'].update({'debit_home': debit, 'credit_home': credit})
        return res

    def onchange_amount_debit(self, cr, uid, ids, date, currency_id, debit, credit, context=None):
        res = {'value': {'debit': 0.0, 'debit_home': 0.0}}
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')

        if not date:
            res['warning'] = {'title': _('Warning'), 'message': _('You have to select a date in the form !\nPlease set one.')}
            return res
        if credit > 0:
            res['warning'] = {'title': _('Warning'), 'message': _('please set credit to zero before input debit.')}
            return res
        debit = round(debit,2)
        res['value'].update({'debit': debit})
        
        company_currency = user_pool.browse(cr, uid, uid, context=None).company_id.currency_id.id
        context_multi_currency = {}
        context_multi_currency.update({'date': date})
        if currency_id:
            if currency_id == company_currency:
                res['value'].update({'debit_home': debit})
            else:
                debit_home = currency_pool.compute(cr, uid, currency_id, company_currency, debit, context=context_multi_currency)
                res['value'].update({'debit_home': round(debit_home,2)})
        else:
            res['value'].update({'debit_home': debit})
        return res

    def onchange_amount_credit(self, cr, uid, ids, date, currency_id, debit, credit, context=None):
        res = {'value': {'credit': 0.0, 'credit_home' : 0.0}}
        user_pool = self.pool.get('res.users')
        currency_pool = self.pool.get('res.currency')
        if not date:
            res['warning'] = {'title': _('Warning'), 'message': _('You have to select a date in the form !\nPlease set one.')}
            return res
        if debit > 0:
            res['warning'] = {'title': _('Warning'), 'message': _('please set debit to zero before input credit.')}
            return res
        credit = round(credit,2)
        res['value'].update({'credit': credit})

        company_currency = user_pool.browse(cr, uid, uid, context=None).company_id.currency_id.id
        context_multi_currency = {}
        context_multi_currency.update({'date': date})
        if currency_id:
            if currency_id == company_currency:
                res['value'].update({'credit_home': credit})
            else:
                credit_home = currency_pool.compute(cr, uid, currency_id, company_currency, credit, context=context_multi_currency)
                res['value'].update({'credit_home': round(credit_home,2)})
        else:
            res['value'].update({'credit_home': credit})
        return res

max_journal_lines_entries()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

