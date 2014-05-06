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

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _description = 'Accounting Voucher'

#    def name_get(self, cr, uid, ids, context=None):
#        if not ids:
#            return []
#        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
#        res = []
#        for record in reads:
#            name = record['name']
#            if record['code']:
#                name = record['code'] + ' ' + name
#            res.append((record['id'], name))
#        return res
    def _convert_amount(self, cr, uid, amount, voucher_id, context=None):
        '''
        This function convert the amount given in company currency. It takes either the rate in the voucher (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.

        :param amount: float. The amount to convert
        :param voucher: id of the voucher on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the voucher date
            field in order to select the good rate to use.
        :return: the amount in the currency of the voucher's company
        :rtype: float
        '''
        currency_obj = self.pool.get('res.currency')
        voucher = self.browse(cr, uid, voucher_id, context=context)
        res = amount
        if voucher.currency_id.id == voucher.company_id.currency_id.id:
            # the rate specified on the voucher is for the company currency
            rate_between_voucher_and_base = voucher.currency_id.rate or 1.0
            rate_between_base_and_company = voucher.payment_rate or 1.0
            res = amount
#            res = float_round(currency_obj.round(cr, uid, voucher.company_id.currency_id, (amount / rate_between_voucher_and_base * rate_between_base_and_company)),2)
        else:
            # the rate specified on the voucher is not relevant, we use all the rates in the system

            res = float_round(currency_obj.compute(cr, uid, voucher.currency_id.id, voucher.company_id.currency_id.id, amount, context=context),2)
        return res

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        reads = self.read(cr, uid, ids, ['number'], context=context)
        res = []
        for record in reads:
            name = record['number']
            res.append((record['id'], name))
        return res

#        return [(r['id'], (str("%.2f" % r['amount']) or '')) for r in self.read(cr, uid, ids, ['amount'], context, load='_classic_write')]

    def onchange_journal2(self, cr, uid, ids, partner_id, journal_id, ttype, context=None):
        """price
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        default = {
            'value':{},
        }

        if not journal_id:
            return default

        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_id and partner_pool.browse(cr, uid, partner_id, context=context) or False
        account_id = False
        tr_type = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner and partner.property_account_receivable.id or False
            tr_type = 'sale'
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner and partner.property_account_payable.id or False
            tr_type = 'purchase'
        else:
            if not journal.default_credit_account_id or not journal.default_debit_account_id:
                raise osv.except_osv(_('Error !'), _('Please define default credit/debit accounts on the journal "%s" !') % (journal.name))
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
            tr_type = 'receipt'
        if not account_id:
            if not journal.default_credit_account_id or not journal.default_debit_account_id:
                raise osv.except_osv(_('Error !'), _('Please define default credit/debit accounts on the journal "%s" !') % (journal.name))
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
        default['value']['account_id'] = account_id
        default['value']['type'] = ttype or tr_type

        return default

    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        if context is None:
            context = {}
        res = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
        ctx = context.copy()
        ctx.update({'date': date})
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        res['value'].update({'amount': amount})
        for key in vals.keys():
            res[key].update(vals[key])
        return res

    def onchange_partner_id2(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        if not partner_id:
            return {}
#        if not journal_id:
#            return {'value': {'journal_id': journal_id}}
        partner_pool = self.pool.get('res.partner')
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        journal_id = partner.journal_id and partner.journal_id.id or journal_id
        if not journal_id:
            return {}
#        default['value']['journal_id'] = journal_id
        res = self.recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
#        if not journal_id:
#            return res
        vals = self.recompute_payment_rate(cr, uid, ids, res, currency_id, date, ttype, journal_id, amount, context=context)
        for key in vals.keys():
            res[key].update(vals[key])
        return res

    def action_refresh(self, cr, uid, ids, context=None):
        return True

    def _prepare_voucher_line(self, cr, uid, account_move_line, type, checked, voucher, context):
        account_voucher_line_obj = self.pool.get('account.voucher.line')
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        product_product_obj = self.pool.get('product.product')
        obj_currency_rate = self.pool.get('res.currency.rate')
        for aml in account_move_line:
            company_currency = aml.journal_id.company_id.currency_id.id
            currency_id = aml.currency_id.id or company_currency
            ctx = {}
            ctx.update({'date': aml.date})
            ctx2 = {}
            ctx2.update({'date': aml.cur_date or aml.date})
            total_amount = 0
            amount_org = 0.0
            amount_invoice = 0.0
            amount_inv_unreconciled = 0.0
            amount_original = 0.0
            amount_unreconciled = 0.0
            gain_loss = 0.0
            line_currency_id = aml.currency_id and aml.currency_id.id or company_currency
            rate_inv = currency_pool.browse(cr, uid, line_currency_id, context=ctx2).rate
            rate_now = currency_pool.browse(cr, uid, line_currency_id, context=ctx).rate
            rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
            rate_payment = currency_pool.browse(cr, uid, currency_id, context=ctx).rate
            if aml.currency_id:
                amount_org = abs(aml.amount_currency)
                amount_invoice = product_product_obj.round_p(cr, uid, abs(aml.amount_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
                amount_inv_unreconciled = product_product_obj.round_p(cr, uid, abs(aml.amount_residual_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
                if aml.currency_id.id == currency_id:
                    amount_original = abs(aml.amount_currency)
                    amount_unreconciled = abs(aml.amount_residual_currency)
                else:
                    amount_original = product_product_obj.round_p(cr, uid, abs(aml.amount_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
                    amount_unreconciled = product_product_obj.round_p(cr, uid, abs(aml.amount_residual_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
            else:
                amount_org = abs(aml.debit - aml.credit)
                if company_currency == currency_id:
                    amount_invoice = abs(aml.debit - aml.credit)
                    amount_original = abs(aml.debit - aml.credit)
                    amount_inv_unreconciled = abs(aml.amount_residual)
                    amount_unreconciled = abs(aml.amount_residual)
                else:
                    amount_invoice = currency_pool.compute(cr, uid, company_currency, currency_id, abs(aml.debit - aml.credit), context=ctx)
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, abs(aml.debit - aml.credit), context=ctx)
                    amount_inv_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(aml.amount_residual), context=ctx)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(aml.amount_residual), context=ctx)
            gain_loss = amount_inv_unreconciled - amount_unreconciled
            line_currency_id = aml.currency_id and aml.currency_id.id or company_currency
            rs = {
                'name':aml.move_id.name,
                'type': type,
                'move_line_id':aml.id,
                'account_id':aml.account_id.id,
                'amount_org': amount_org,
                'amount_invoice': amount_invoice,
                'amount_original': amount_original,
                'amount': 0.0,
                'date_original':aml.date,
                'date_due':aml.date_maturity,
                'due_date':aml.due_date,
                'invoice_no':aml.invoice_no,
                'amount_inv_unreconciled': amount_inv_unreconciled,
                'amount_unreconciled': amount_unreconciled,
                'gain_loss': gain_loss,
                'currency_id': line_currency_id,
                'balance_amount': amount_unreconciled,
                'voucher_id': voucher.id,
            }
    
            if amount_inv_unreconciled != 0:
                rs['inv_amount'] = amount_inv_unreconciled / amount_unreconciled * rs['amount']
                rs['gain_loss_amount'] = rs['inv_amount'] - rs['amount']
    #            product_product_obj.round_p(cr, uid, rs['amount_unreconciled'], 'Account')
            if product_product_obj.round_p(cr, uid, rs['amount_unreconciled'], 'Account') == product_product_obj.round_p(cr, uid, rs['amount'], 'Account'):
                rs['reconcile'] = True
            avl = account_voucher_line_obj.create(cr, uid, rs, context)
            avl_id = account_voucher_line_obj.browse(cr, uid, avl, context=None)
            if checked:
                account_voucher_line_obj.write(cr, uid, [avl_id.id], {'amount': avl_id.amount_unreconciled,
                                                                      'reconcile': True})
                total_amount += avl_id.amount_unreconciled
        return total_amount

    def action_compute(self, cr, uid, ids, context=None):
        account_voucher_line_obj = self.pool.get('account.voucher.line')
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        product_product_obj = self.pool.get('product.product')
        obj_currency_rate = self.pool.get('res.currency.rate')

        for voucher in self.browse(cr, uid, ids):
            line_ids = ids and account_voucher_line_obj.search(cr, uid, [('voucher_id', '=', voucher.id)]) or False
            if line_ids:
                account_voucher_line_obj.unlink(cr, uid, line_ids)
            if voucher.account_move_line_ids:
                total_amount = self._prepare_voucher_line(cr, uid, voucher.account_move_line_ids, 'cr', voucher.auto_fill_credit, voucher, context)
            if voucher.other_move_line_db_ids:
                total_amount = self._prepare_voucher_line(cr, uid, voucher.other_move_line_db_ids, 'cr', voucher.auto_fill_other_credit, voucher, context)
            if voucher.move_line_cr_ids:
                total_amount = self._prepare_voucher_line(cr, uid, voucher.move_line_cr_ids, 'dr', voucher.auto_fill_debit, voucher, context)
            if voucher.other_move_line_cr_ids:
                total_amount = self._prepare_voucher_line(cr, uid, voucher.other_move_line_cr_ids, 'dr', voucher.auto_fill_other_credit, voucher, context)
        return True
#            



    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context = {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
        product_product_obj = self.pool.get('product.product')
        obj_currency_rate = self.pool.get('res.currency.rate')
        #set default values
        default = {
            'value': {'line_ids': [] ,'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default


        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'

        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'


        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

#        raise osv.except_osv(_('Error'), _(str(default) + '---' + str(ids)))
        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
#        data_name = []
#        for line in account_move_lines:
#            if line.credit and line.reconcile_partial_id and line.is_depo != True and ttype == 'receipt':
#                continue
#            if line.debit and line.reconcile_partial_id and line.is_depo == True and ttype == 'receipt':
#                continue
#            if line.debit and line.reconcile_partial_id and line.is_depo != True and ttype == 'payment':
#                continue
#            if line.credit and line.reconcile_partial_id and line.is_depo == True and ttype == 'payment':
#                continue
#            data_name.append(line.move_id and line.move_id.name or 'xx')
#        raise osv.except_osv(_('Error'), _(str(data_name)))
        for line in account_move_lines:
#            if line.move_id.name == 'RCNX0020/13':
#
#                if line.credit and line.reconcile_partial_id and line.is_depo == True and ttype == 'receipt':
#                    raise osv.except_osv(_('Error'), _(str('1')))
#                if line.debit and line.reconcile_partial_id and line.is_depo == True and ttype == 'receipt':
#                    raise osv.except_osv(_('Error'), _(str('2')))
#                if line.debit and line.reconcile_partial_id and line.is_depo != True and ttype == 'payment':
#                    raise osv.except_osv(_('Error'), _(str('3')))
#                if line.credit and line.reconcile_partial_id and line.is_depo == True and ttype == 'payment':
#                    raise osv.except_osv(_('Error'), _(str('4')))
            if line.credit and line.reconcile_partial_id and line.is_depo != True and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and line.is_depo == True and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and line.is_depo != True and ttype == 'payment':
                continue
            if line.credit and line.reconcile_partial_id and line.is_depo == True and ttype == 'payment':
                continue
#            if str(line.id) not in ('2516', '2589'):
#                raise osv.except_osv(_('Error'), _(str(line.id) + '---' + str(ids)))

            if invoice_id:

                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit and line.amount_residual or 0.0
                total_debit += line.debit and line.amount_residual or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_residual_currency or 0.0
                total_debit += line.debit and line.amount_residual_currency or 0.0
            else:
                amount_unreconciled = 0.00
                if line.currency_id:
                    amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id or company_currency, company_currency, abs(line.amount_residual_currency), context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_unreconciled), context=context_multi_currency)
                else:
                    amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id or company_currency, company_currency, abs(line.amount_residual), context=context_multi_currency)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_unreconciled), context=context_multi_currency)

#                raise osv.except_osv(_('Errorxx'), _(str(amount_original) + '---' + str('xxx')))

                total_credit += line.credit and amount_unreconciled or 0.0
                total_debit += line.debit and amount_unreconciled or 0.0
        total_credit = 0.0
        total_debit = 0.0
#        raise osv.except_osv(_('Error'), _(str(total_credit) + '---' + str(total_debit)))

        #voucher line creation

        for line in account_move_lines:
            if line.credit and line.reconcile_partial_id and line.is_depo != True and ttype == 'receipt':
                if line.is_refund != True:
                    continue
            if line.debit and line.reconcile_partial_id and line.is_refund == True and ttype == 'receipt':
                continue
            if line.debit and line.reconcile_partial_id and line.is_depo == True and ttype == 'receipt':
                continue

            if line.debit and line.reconcile_partial_id and line.is_depo != True and ttype == 'payment':
                 if line.is_refund != True:
                    continue
            if line.credit and line.reconcile_partial_id and line.is_refund == True and ttype == 'payment':
                continue
            if line.credit and line.reconcile_partial_id and line.is_depo == True and ttype == 'payment':
                continue
            ctx = {}
            ctx.update({'date': date})
            ctx2 = {}
            ctx2.update({'date': line.cur_date or line.date})
#                raise osv.except_osv(_('Error'), _(str(abs(line.amount_residual_currency)) + '---' + str(line.amount_residual)))

#convert to home currency
#            raise osv.except_osv(_('Error'), _(str(line.currency_id.id) + '---' + str(currency_id)))
            amount_org = 0.0
            amount_invoice = 0.0
            amount_inv_unreconciled = 0.0
            amount_original = 0.0
            amount_unreconciled = 0.0
            gain_loss = 0.0
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rate_inv = currency_pool.browse(cr, uid, line_currency_id, context=ctx2).rate
            rate_now = currency_pool.browse(cr, uid, line_currency_id, context=ctx).rate
            rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
            rate_payment = currency_pool.browse(cr, uid, currency_id, context=ctx).rate
            if line.currency_id:
                amount_org = abs(line.amount_currency)
                amount_invoice = product_product_obj.round_p(cr, uid, abs(line.amount_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
                amount_inv_unreconciled = product_product_obj.round_p(cr, uid, abs(line.amount_residual_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
#                amount_invoice = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_currency), context=ctx2)
#                amount_inv_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_residual_currency), context=ctx2)
#                amount_invoice = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_invoice), context=ctx)
#                amount_inv_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_inv_unreconciled), context=ctx)
                if line.currency_id.id == currency_id:
                    amount_original = abs(line.amount_currency)
                    amount_unreconciled = abs(line.amount_residual_currency)
                else:
                    amount_original = product_product_obj.round_p(cr, uid, abs(line.amount_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
                    amount_unreconciled = product_product_obj.round_p(cr, uid, abs(line.amount_residual_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
                    #amount_original = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_currency), context=ctx)
#                    amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_residual_currency), context=ctx)
                    #amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_original), context=ctx)
#                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_unreconciled), context=ctx)
            else:
                amount_org = abs(line.debit - line.credit)
                if company_currency == currency_id:
                    amount_invoice = abs(line.debit - line.credit)
                    amount_original = abs(line.debit - line.credit)
                    amount_inv_unreconciled = abs(line.amount_residual)
                    amount_unreconciled = abs(line.amount_residual)
                else:
                    amount_invoice = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.debit - line.credit), context=ctx)
                    amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.debit - line.credit), context=ctx)
                    amount_inv_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=ctx)
                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=ctx)
#            raise osv.except_osv(_('Error'), _(str(amount_invoice) + '---' + str(line.amount_currency)))

#convert to payment Currency


            gain_loss = amount_inv_unreconciled - amount_unreconciled
            line_currency_id = line.currency_id and line.currency_id.id or company_currency

            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_org': amount_org,
                'amount_invoice': amount_invoice,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(price, amount_unreconciled) or 0.0,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'due_date':line.due_date,
                'invoice_no':line.invoice_no,
                'amount_inv_unreconciled': amount_inv_unreconciled,
                'amount_unreconciled': amount_unreconciled,
                'gain_loss': gain_loss,
                'currency_id': line_currency_id,
                'balance_amount': amount_unreconciled,
            }

#            raise osv.except_osv(_('Error'), _(str(rs)))
            #split voucher amount by most old first, but only for lines in the same currency
#            raise osv.except_osv(_('Error'), _(str(currency_id) + '---' + str(line_currency_id)))
#            raise osv.except_osv(_('Error'), _(str(total_debit) + '---' + str(total_credit)))

  
            if not move_line_found:
#                if currency_id == line_currency_id:
                if line.credit:
                    amount = min(amount_unreconciled, abs(total_debit))
                    rs['amount'] = amount
                    total_debit -= amount
                else:
                    amount = min(amount_unreconciled, abs(total_credit))
                    rs['amount'] = amount
                    total_credit -= amount
#            raise osv.except_osv(_('Error'), _(str(rs) + '---' + str(total_debit)))

            if amount_inv_unreconciled != 0:
                rs['inv_amount'] = amount_inv_unreconciled / amount_unreconciled * rs['amount']
                rs['gain_loss_amount'] = rs['inv_amount'] - rs['amount']
#            product_product_obj.round_p(cr, uid, rs['amount_unreconciled'], 'Account')
            if product_product_obj.round_p(cr, uid, rs['amount_unreconciled'], 'Account') == product_product_obj.round_p(cr, uid, rs['amount'], 'Account'):
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price)
            default['value']['journal_id'] = journal_id
        return default

    def _get_debit_gain_loss_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            credit = 0.0
            for l in voucher.line_cr_ids:
                credit += l.amount
            credit_round = float_round(credit, 2)
            res[voucher.id] = credit_round - credit
        return res

    def _get_debit_total_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            credit = 0.0
            for l in voucher.line_cr_ids:
                credit += l.amount
            res[voucher.id] = voucher.debit_gain_loss_amount + credit
        return res

    def _get_debit_total_amount_simple(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            credit = 0.0
            for l in voucher.simple_line_cr_ids:
                credit += l.amount
            res[voucher.id] = voucher.debit_gain_loss_amount + credit
        return res

    def _get_credit_gain_loss_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            debit = 0.0
            for l in voucher.line_dr_ids:
                debit += l.amount
            debit_round = float_round(debit, 2)
            res[voucher.id] = debit_round - debit
        return res

    def _get_credit_total_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            debit = 0.0
            for l in voucher.line_dr_ids:
                debit += l.amount
            res[voucher.id] = voucher.credit_gain_loss_amount + debit
        return res

    def _get_credit_total_amount_simple(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            debit = 0.0
            for l in voucher.simple_line_dr_ids:
                debit += l.amount
            res[voucher.id] = debit
        return res


    def _get_rounding_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type in ('purchase', 'payment'):
                res[voucher.id] = voucher.credit_gain_loss_amount - voucher.debit_gain_loss_amount
            else:
                res[voucher.id] = voucher.debit_gain_loss_amount - voucher.credit_gain_loss_amount
        return res


    def _get_pay_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type in ('purchase', 'payment'):
                res[voucher.id] = (voucher.credit_total_amount + voucher.credit_total_amount_simple) - (voucher.debit_total_amount + voucher.debit_total_amount_simple)
            else:
                res[voucher.id] = (voucher.debit_total_amount + voucher.debit_total_amount_simple) - (voucher.credit_total_amount + voucher.credit_total_amount_simple)
        return res


    def _get_grand_total(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
#            raise osv.except_osv(_('No Gain Lost Account Found!'),_(str(voucher.amount) + '---' +  str(voucher.total_payment_amount)))
            if voucher.type in ('purchase', 'payment'):
                res[voucher.id] =  voucher.amount + voucher.bank_charges_amount
            else:
                res[voucher.id] =  voucher.amount - voucher.bank_charges_amount
#            raise osv.except_osv(_('No Gain Lost Account Found!'),_(str( voucher.amount - voucher.total_payment_amount)))

        return res

    def _get_writeoff_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            res[voucher.id] =  float_round(voucher.amount - voucher.total_payment_amount,2)
        return res

    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        res_currency_rate_obj = self.pool.get("res.currency.rate")
        tot_line = line_total
        rec_lst_ids = []
        rec_ids = []
        voucher_brw = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        ctx = context.copy()
        ctx.update({'date': voucher_brw.date})

        for line in voucher_brw.line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.amount:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            amount = self._convert_amount(cr, uid, line.untax_amount or line.inv_amount, voucher_brw.id, context=ctx)
        
            #Recheck later
            if line.reconcile:
                amount = line.move_line_id.amount_residual
            currency_rate_difference = 0.0

            move_line = {
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher_brw.date,
                'cur_date' : line.move_line_id.cur_date,
                'is_depo' : line.move_line_id.is_depo,
                'is_refund' : line.move_line_id.is_refund,
            }
            if amount < 0:
                amount = -amount
#                if line.type == 'dr':
#                    line.type = 'cr'
#                else:
#                    line.type = 'dr'

            if (line.type=='dr'):

                tot_line += amount
                
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount
#                raise osv.except_osv(_('No Gain Lost Account Found!'),_(str(tot_line) + 'xxx' + str(amount)))

            if voucher_brw.tax_id and voucher_brw.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher_brw.tax_id.id,
                })

            if move_line.get('account_tax_id', False):
                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                if not (tax_data.base_code_id and tax_data.tax_code_id):
                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            exrate = 1.00
            
            amount_currency = False
            if line.move_line_id:
                voucher_currency = voucher_brw.currency_id and voucher_brw.currency_id.id or voucher_brw.journal_id.company_id.currency_id.id
                
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency. 
                    cur_id = line.move_line_id.currency_id.id or False
                    cur_date = line.move_line_id.cur_date or False
                    if cur_id and cur_date:
                        res_currency_rate_ids = res_currency_rate_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                        if res_currency_rate_ids:
                            exrate = res_currency_rate_obj.browse(cr, uid, res_currency_rate_ids[0], context=None).rate
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        
                        amount_currency = sign * (line.amount)
                    else:
                        # otherwise we use the rates of the system (giving the voucher date in the context)
                        ctx2 = context.copy()
                        ctx2.update({'date': line.move_line_id.cur_date})
                        
                        if line.reconcile:
                            sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                            amount_currency = sign * line.move_line_id.amount_residual_currency
                        else:
                            amount_currency = float_round(currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx2),2)
#                if line.amount == line.amount_unreconciled and line.move_line_id.currency_id.id == voucher_currency:
#                    foreign_currency_diff = line.move_line_id.amount_residual_currency + amount_currency
            move_line['exrate'] = exrate
            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)

            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher_brw.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

#            raise osv.except_osv(_('No Gain Lost Account Found!'),_(str(rec_ids)))

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': -1 * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)

            gain_lost_acc = voucher_brw.company_id and voucher_brw.company_id.property_currency_gain_loss and voucher_brw.company_id.property_currency_gain_loss.id or False 
            if not gain_lost_acc:
                raise osv.except_osv(_('No Gain Lost Account Found!'),_("You have to configure gain/loss account on company profile!"))

            inv_amountx = self._convert_amount(cr, uid, line.inv_amount, voucher_brw.id, context=ctx)
            if line.reconcile:
                inv_amountx = line.move_line_id.amount_residual
            amountx = self._convert_amount(cr, uid, line.amount, voucher_brw.id, context=ctx)
#            print line.inv_amount
#            print line.amount
#            print inv_amountx
#            print amountx
#            raise osv.except_osv(_('Error'), _(str('t')))
            
            gain_lost_amount = abs(inv_amountx - amountx)
#            raise osv.except_osv(_('No Gain Lost Account Found!'),_(str(gain_lost_amount)))
            if gain_lost_amount > 0:
                if (line.type=='dr'):
                    if inv_amountx - amountx < 0:
                        move_line1 = {
                        'journal_id': voucher_brw.journal_id.id,
                        'period_id': voucher_brw.period_id.id,
                        'name': line.name or '/',
                        'account_id': gain_lost_acc,
                        'move_id': move_id,
                        'partner_id': voucher_brw.partner_id.id,
                        'currency_id': False,
                        'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                        'quantity': 1,
                        'credit': 0.0,
                        'debit': gain_lost_amount,
                        'date': voucher_brw.date,
                        'amount_currency': 0.0,
                        'cur_date' : voucher_brw.date,
                        'exrate': 1,
                        }
                        new_id = move_line_obj.create(cr, uid, move_line1, context)
                        tot_line += gain_lost_amount

                    else:
                        move_line1 = {
                        'journal_id': voucher_brw.journal_id.id,
                        'period_id': voucher_brw.period_id.id,
                        'name': line.name or '/',
                        'account_id': gain_lost_acc,
                        'move_id': move_id,
                        'partner_id': voucher_brw.partner_id.id,
                        'currency_id': False,
                        'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                        'quantity': 1,
                        'credit': gain_lost_amount,
                        'debit': 0.0,
                        'date': voucher_brw.date,
                        'amount_currency': 0.0,
                        'cur_date' : voucher_brw.date,
                        'exrate': 1,
                        }
                        new_id = move_line_obj.create(cr, uid, move_line1, context)
                        tot_line -= gain_lost_amount
                else:
                    if inv_amountx - amountx < 0:
                        move_line1 = {
                        'journal_id': voucher_brw.journal_id.id,
                        'period_id': voucher_brw.period_id.id,
                        'name': line.name or '/',
                        'account_id': gain_lost_acc,
                        'move_id': move_id,
                        'partner_id': voucher_brw.partner_id.id,
                        'currency_id': False,
                        'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                        'quantity': 1,
                        'credit': gain_lost_amount,
                        'debit': 0.0,
                        'date': voucher_brw.date,
                        'amount_currency': 0.0,
                        'cur_date' : voucher_brw.date,
                        'exrate': 1,
                        }
                        new_id = move_line_obj.create(cr, uid, move_line1, context)
                        tot_line -= gain_lost_amount
                    else:
                        move_line1 = {
                        'journal_id': voucher_brw.journal_id.id,
                        'period_id': voucher_brw.period_id.id,
                        'name': line.name or '/',
                        'account_id': gain_lost_acc,
                        'move_id': move_id,
                        'partner_id': voucher_brw.partner_id.id,
                        'currency_id': False,
                        'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                        'quantity': 1,
                        'credit': 0.0,
                        'debit': gain_lost_amount,
                        'date': voucher_brw.date,
                        'amount_currency': 0.0,
                        'cur_date' : voucher_brw.date,
                        'exrate': 1,
                        
                        }
                        new_id = move_line_obj.create(cr, uid, move_line1, context)
                        tot_line += gain_lost_amount
#            raise osv.except_osv(_('Error'), _(str('gain_lost_amount v2')))
            if line.move_line_id.id:
                if rec_ids:
                    rec_lst_ids.append(rec_ids)
#        raise osv.except_osv(_('Error'), _('xcsd'))

        return (tot_line, rec_lst_ids)

    def bank_charge_account_create(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        move_line_pool = self.pool.get('account.move.line')
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        debit = voucher_brw.bank_charges_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0

        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        bank_charge_acc =  voucher_brw.journal_id and voucher_brw.journal_id.property_bank_charges and voucher_brw.journal_id.property_bank_charges.id or False
        if not bank_charge_acc:
            raise osv.except_osv(_('No Bank Charges Account Found!'),_("You have to configure Bank Charges account on related journal!"))
        move_line1 = {
                'name': 'bank-charges ' + (voucher_brw.name or ''),
                'debit': debit,
                'credit': credit,
                'account_id': bank_charge_acc,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * voucher_brw.bank_charges_amount or 0.0,
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due,
                'cur_date': voucher_brw.date or False,
                'exrate': voucher_brw.ex_rate,
            }
        move_line_pool.create(cr, uid, move_line1, context)
        move_line2 = {
                'name': 'bank-charges ' + (voucher_brw.name or ''),
                'debit': credit,
                'credit': debit,
                'account_id': voucher_brw.account_id.id,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and -1 * sign * voucher_brw.bank_charges_amount or 0.0,
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due,
                'cur_date': voucher_brw.date or False,
                'exrate': voucher_brw.ex_rate,
            }
        move_line_pool.create(cr, uid, move_line2, context)
        return True


    def gain_loss_create(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        move_line_pool = self.pool.get('account.move.line')
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt


        if voucher_brw.type == 'receipt':
            credit = voucher_brw.rounding_gain_loss_in_comp_currency
            if debit < 0: credit = -debit; debit = 0.0
            if credit < 0: debit = -credit; credit = 0.0
        elif voucher_brw.type == 'payment':
            debit = voucher_brw.rounding_gain_loss_in_comp_currency
            if debit < 0: credit = -debit; debit = 0.0
            if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        gain_lost_acc = voucher_brw.company_id and voucher_brw.company_id.property_currency_gain_loss and voucher_brw.company_id.property_currency_gain_loss.id or False 
        if not gain_lost_acc:
            raise osv.except_osv(_('No Gain Lost Account Found!'),_("You have to configure gain/loss account on company profile!"))

        move_line1 = {
                'name': voucher_brw.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': gain_lost_acc,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * voucher_brw.rounding_gain_loss or 0.0,
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due,
                'cur_date': company_currency <> current_currency and voucher_brw.date or False
            }
        move_line_pool.create(cr, uid, move_line1, context)
        return True

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher_brw.type in ('purchase', 'payment'):
            credit = voucher_brw.paid_amount_in_company_currency
        elif voucher_brw.type in ('sale', 'receipt'):
            debit = voucher_brw.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
#        print voucher_brw.paid_amount_in_company_currency
#        print debit
#        print credit
#        print 'xx'
        move_line = {
                'name': voucher_brw.name or voucher_brw.reference or '/',
                'debit': float_round(debit,2),
                'credit': float_round(credit,2),
                'account_id': voucher_brw.account_id.id,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * voucher_brw.amount or 0.0,
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due,
                'cur_date' : voucher_brw.date,
                'exrate' : voucher_brw.ex_rate,
            }

        return move_line

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}

        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.writeoff_amount < 0:
                raise osv.except_osv(_('Error'), _('cannot process if the Different Amount In Negatif Value'))
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher

            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, context), context)
            

            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            
            if voucher.bank_charges_amount != 0:
                self.bank_charge_account_create(cr,uid,voucher.id, move_id, company_currency, current_currency, context)
#            raise osv.except_osv(_('Error'), _(str('t')))
            line_total = move_line_brw.debit - move_line_brw.credit

            rec_list_ids = []

            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)

            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            line_total = self.voucher_simple_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
#            print line_total
#            raise osv.except_osv(_('Error'), _(str('t')))
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)



            if ml_writeoff:

                move_line_pool.create(cr, uid, ml_writeoff, context)
            # We post the voucher.

            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })

            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})

            # We automatically reconcile the account move lines.

            
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True


    def voucher_simple_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        res_currency_rate_obj = self.pool.get("res.currency.rate")
        tot_line = line_total
        rec_ids = []
        voucher_brw = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context)
        ctx = context.copy()
        ctx.update({'date': voucher_brw.date})

        for line in voucher_brw.simple_line_ids:
            #create one move line per voucher line where amount is not 0.0
            if not line.amount:
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            amount = self._convert_amount(cr, uid, line.amount, voucher_brw.id, context=ctx)

            #Recheck later

            move_line = {
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher_brw.partner_id and voucher_brw.partner_id.id or False,
                'currency_id': (company_currency <> line.currency_id.id and line.currency_id.id) or False,
                'analytic_account_id': False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher_brw.date,
                'cur_date' : voucher_brw.date,
                'is_depo' : False,
                'is_refund' : False,
            }

##########################
            if amount < 0:
                amount = -amount
#                if line.type == 'dr':
#                    line.type = 'cr'
#                else:
#                    line.type = 'dr'

            if (line.type=='dr'):

                tot_line += amount
                
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount
#                raise osv.except_osv(_('No Gain Lost Account Found!'),_(str(tot_line) + 'xxx' + str(amount)))

            foreign_currency_diff = 0.0
            exrate = 1.00
            
            amount_currency = False
            voucher_currency = voucher_brw.currency_id and voucher_brw.currency_id.id or voucher_brw.journal_id.company_id.currency_id.id
            if line.currency_id and line.currency_id.id != company_currency:
                cur_id = line.currency_id.id or False
                cur_date = voucher_brw.date or False
                if cur_id and cur_date:
                    res_currency_rate_ids = res_currency_rate_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                    if res_currency_rate_ids:
                        exrate = res_currency_rate_obj.browse(cr, uid, res_currency_rate_ids[0], context=None).rate

                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                amount_currency = sign * (line.amount)
            move_line['exrate'] = exrate
            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)

#################################3

        return (tot_line)



    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher_brw.currency_id or voucher_brw.journal_id.company_id.currency_id
        

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            
#            print diff
            if diff != 0 and voucher_brw.payment_option == 'none':
#                if voucher_brw.writeoff_amount == 0:
#                    gain_lost_acc = voucher_brw.company_id and voucher_brw.company_id.property_currency_gain_loss and voucher_brw.company_id.property_currency_gain_loss.id or False 
#                    if not gain_lost_acc:
#                        raise osv.except_osv(_('No Gain Lost Account Found!'),_("You have to configure gain/loss account on company profile!"))
#
#                    move_line = {
#                        'name': voucher_brw.number or 'gain/loss',
#                        'account_id': gain_lost_acc,
#                        'move_id': move_id,
#                        'partner_id': voucher_brw.partner_id.id,
#                        'date': voucher_brw.date,
#                        'credit': diff > 0 and diff or 0.0,
#                        'debit': diff < 0 and -diff or 0.0,
#                        'amount_currency': False,
#                        'currency_id': False,
#                        'analytic_account_id': voucher_brw.analytic_id and voucher_brw.analytic_id.id or False,
#                        'cur_date': voucher_brw.date or False,
#                        'is_depo': False,
#                        'exrate': 1,
#                    }
#                    return move_line
#                else:
                raise osv.except_osv(_('Error'), _("cannot process, please select the payment difference other than 'none'"))
                    
            account_id = False
            write_off_name = ''
            is_depo = False
            account_id = voucher_brw.writeoff_acc_id.id
            acco_currency = voucher_brw.writeoff_acc_id and voucher_brw.writeoff_acc_id.currency_id and voucher_brw.writeoff_acc_id.currency_id.id or \
                             voucher_brw.journal_id.company_id.currency_id.id or False
            if current_currency_obj.id != acco_currency:
                raise osv.except_osv(_('Error'), _("pls select other write off account, the selected account currency, doesn't match with current payment currency."))
            if voucher_brw.payment_option == 'with_writeoff':
                write_off_name = 'other - ' + (voucher_brw.comment or '')
            elif voucher_brw.payment_option == 'without_writeoff':
                is_depo = True
                write_off_name = 'deposit'
            move_line = {
                'name': write_off_name,
                'account_id': account_id,
                'move_id': move_id,
                'partner_id': voucher_brw.partner_id.id,
                'date': voucher_brw.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and voucher_brw.writeoff_amount or False,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': voucher_brw.analytic_id and voucher_brw.analytic_id.id or False,
                'cur_date': voucher_brw.date or False,
                'is_depo': is_depo,
                'exrate': voucher_brw.ex_rate
            }
#        raise osv.except_osv(_('Error'), _(str(move_line) + '---' + str('')))
        return move_line

    def _bank_charges_in_company_currency(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            company_currency = voucher.company_id.currency_id
            voucher_currency = voucher.journal_id.currency or company_currency
            if voucher_currency.id == company_currency.id:
                res[voucher.id] = voucher.bank_charges_amount
            else:
                ctx = {'date':voucher.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[voucher.id] =  float_round(voucher.bank_charges_amount / voucher_rate * company_rate,2)

        return res


    def _total_in_home_currency(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            company_currency = voucher.company_id.currency_id
            voucher_currency = voucher.journal_id.currency or company_currency
            if voucher_currency.id == company_currency.id:
                res[voucher.id] = voucher.amount
            else:
                ctx = {'date':voucher.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[voucher.id] =  float_round(voucher.amount / voucher_rate * company_rate,2)

        return res

    def _rounding_gain_loss_in_company_currency(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            company_currency = voucher.company_id.currency_id
            voucher_currency = voucher.journal_id.currency or company_currency
            if voucher_currency.id == company_currency.id:
                res[voucher.id] = voucher.rounding_gain_loss
            else:
                ctx = {'date':voucher.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[voucher.id] =  float_round(voucher.rounding_gain_loss / voucher_rate * company_rate,2)

#            if voucher.currency_id:
#                ctx = context.copy()
#                ctx.update({'date': voucher.date})
#                voucher_rate = self.browse(cr, uid, voucher.id, context=ctx).currency_id.rate
#                if voucher.company_id.currency_id.id == voucher.payment_rate_currency_id.id:
#                    company_currency_rate =  voucher.payment_rate
#                else:
#                    company_currency_rate = voucher.company_id.currency_id.rate
#            res[voucher.id] =  voucher.rounding_gain_loss / voucher_rate * company_currency_rate
        return res

    def _writeoff_amount_home(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for voucher in self.browse(cr, uid, ids, context=context):
            company_currency = voucher.company_id.currency_id
            voucher_currency = voucher.journal_id.currency or company_currency
            if voucher_currency.id == company_currency.id:
                res[voucher.id] = voucher.writeoff_amount
            else:
                ctx = {'date':voucher.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[voucher.id] =  float_round(voucher.writeoff_amount / voucher_rate * company_rate,2)

        return res

    def onchange_pay_option(self, cr, uid, ids, payment_option, type, partner_id, context=None):
        if context is None:
            context = {}
        res = {}
        if (not payment_option) or (not partner_id):
            return res
        
        if payment_option == 'none':
            res['value']= {'writeoff_acc_id': False}

        if payment_option == 'without_writeoff':
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            if type == 'payment':
                res['value']= {'writeoff_acc_id': partner and partner.property_account_payable and partner.property_account_payable.id or False}
                res['domain'] = {'writeoff_acc_id': [('type','=','payable')]}
            elif type == 'receipt':
                res['value']= {'writeoff_acc_id': partner and partner.property_account_receivable and partner.property_account_receivable.id or False}
                res['domain'] = {'writeoff_acc_id': [('type','=','receivable')]}
        if payment_option == 'with_writeoff':
            res['value']= {'writeoff_acc_id': False}
            res['domain'] = {'writeoff_acc_id': [('type','=','other')]}
        return res

    def _rate(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        res_currency_rate_obj = self.pool.get("res.currency.rate")

        for obj in self.browse(cr, uid, ids, context=context):
            current_currency = self._get_current_currency(cr, uid, obj.id, context)
            cur_date = obj.date or False
            if current_currency and cur_date:
                res_currency_rate_ids = res_currency_rate_obj.search(cr, uid, [('currency_id', '=', current_currency), ('name', '<=', cur_date)], order='name DESC', limit=1)
                if res_currency_rate_ids:
                    res[obj.id] = res_currency_rate_obj.browse(cr, uid, res_currency_rate_ids[0], context=context).rate
                else:
                    res[obj.id] = 0
            else:
                res[obj.id] = 0

        return res

    def _paid_amount_in_company_currency(self, cr, uid, ids, name, args, context=None):
#        if not ids: return {}
#        res = {}
#        voucher_rate = company_currency_rate = 1.0
#        for voucher in self.browse(cr, uid, ids, context=context):
#            if voucher.currency_id:
#                ctx = context.copy()
#                ctx.update({'date': voucher.date})
#                voucher_rate = self.browse(cr, uid, voucher.id, context=ctx).currency_id.rate
#
#                company_currency_rate = voucher.company_id.currency_id.rate
##            print voucher.amount
##            print company_currency_rate
##            print voucher_rate
##            print self.browse(cr, uid, voucher.id, context=ctx).currency_id.name
##            print voucher.company_id.currency_id.rate
##            print voucher.company_id.currency_id.id
##            print voucher.payment_rate_currency_id.id
##            print "voucher_amount"
#            res[voucher.id] =  voucher.amount / voucher_rate * company_currency_rate

        if not ids: return {}
        res = {}
        voucher_rate = company_currency_rate = 1.0
        currency_pool = self.pool.get('res.currency')
        for voucher in self.browse(cr, uid, ids, context=context):
            company_currency = voucher.company_id.currency_id
            voucher_currency = voucher.journal_id.currency or company_currency
            if voucher_currency.id == company_currency.id:
                res[voucher.id] = voucher.amount
            else:

                ctx = {'date':voucher.date}
                total = 0.0
                total_cur = 0.00
                other_total = 0.00

                debit = 0.0
                credit = 0.0
                debit_cur = 0.00
                credit_cur = 0.00
                for l in voucher.line_dr_ids:
                    amount = self._convert_amount(cr, uid, l.amount, voucher.id, context=ctx)
                    amount_currency = l.amount
                    debit += amount
                    debit_cur += amount_currency
                for l in voucher.line_cr_ids:
                    amount = self._convert_amount(cr, uid, l.amount, voucher.id, context=ctx)
                    amount_currency = l.amount
                    #Recheck later
                    amount = self._convert_amount(cr, uid, l.amount, voucher.id, context=ctx)

                    credit += amount
                    credit_cur += amount_currency
                if voucher.type in ('sale', 'receipt'):
                    total = credit - debit
                    total_cur = credit_cur - debit_cur
                else:
                    total = debit - credit
                    total_cur = debit_cur - credit_cur
                
                if voucher.amount - total_cur > 0:
                    amount_count = voucher.amount - total_cur

                    voucher_rate = company_currency_rate = 1.0
                    if voucher.currency_id:
                        voucher_rate = self.browse(cr, uid, voucher.id, context=ctx).currency_id.rate
                        company_currency_rate = voucher.company_id.currency_id.rate
                        other_total =  amount_count / voucher_rate * company_currency_rate
                res[voucher.id] = currency_pool.compute(cr, uid, company_currency.id, company_currency.id, total + other_total, round=True, context=None)

        return res

    def _get_simplified(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('simplified', False)

    _columns = {
        'credit_total_amount_simple'       : fields.function(_get_credit_total_amount_simple, digits_compute=dp.get_precision('Account'), string='Credit Total Amount Simple', type='float', readonly=True),
        'debit_total_amount_simple'        : fields.function(_get_debit_total_amount_simple, digits_compute=dp.get_precision('Account'), string='Debit Total Amount Simple', type='float', readonly=True),
        'simple_line_ids':fields.one2many('account.voucher.line.simple','voucher_id','Voucher Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'simple_line_cr_ids':fields.one2many('account.voucher.line.simple','voucher_id','Credits',
            domain=[('type','=','cr')], context={'default_type':'cr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'simple_line_dr_ids':fields.one2many('account.voucher.line.simple','voucher_id','Debits',
            domain=[('type','=','dr')], context={'default_type':'dr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'simplified': fields.boolean('Simplified'),
        'ex_rate': fields.function(_rate, type='float', digits=(12,6), string='Currency Rate'),
        'auto_fill_debit': fields.boolean('Auto Fill Debit', readonly=True, states={'draft':[('readonly',False)]}, help="Tick if you want to auto full fill for all selected invoices."),
        'auto_fill_credit': fields.boolean('Auto Fill Credit', readonly=True, states={'draft':[('readonly',False)]}, help="Tick if you want to auto full fill for all selected invoices."),
        'auto_fill_other_credit': fields.boolean('Other Fill Credit', readonly=True, states={'draft':[('readonly',False)]}, help="Tick if you want to auto full fill for all selected invoices."),
        'other_move_line_db_ids'    :fields.many2many('account.move.line', 'voucher_move_line__db_other_rel', 'voucher_id', 'line_id', 'Other Move Line Debit'),
        'other_move_line_cr_ids'    :fields.many2many('account.move.line', 'voucher_move_line_cr_other_rel', 'voucher_id', 'line_id', 'Other Move Line Credit'),
        'move_line_cr_ids'          :fields.many2many('account.move.line', 'voucher_move_line_cr_rel', 'voucher_id', 'line_id', 'Move Line Credit'),
        'account_move_line_ids'     :fields.many2many('account.move.line', 'voucher_move_line_rel', 'voucher_id', 'line_id', 'Move Line Debit'),
        'cheque_no'                 : fields.char('Cheque No', size=64, readonly=True, states={'draft':[('readonly',False)]}, help="Transaction Cheque No."),
        'bank_draft_no'             : fields.char('Bank Draft No', size=64, readonly=True, states={'draft':[('readonly',False)]}, help="Transaction Bank Draft No."),
        'payment_option'            :fields.selection([
                                                       ('none', 'None'),
                                                       ('without_writeoff', 'Deposit Amount'),
                                                       ('with_writeoff', 'Reconcile Payment Balance')
                                                       ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s) or use as deposit amount."),
        'bank_charges_amount'       : fields.float('Bank Charges', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
        'debit_gain_loss_amount'    : fields.function(_get_debit_gain_loss_amount, digits_compute=dp.get_precision('Account'), string='Debit Rounding Gain/Loss Amount', type='float', readonly=True),
        'debit_total_amount'        : fields.function(_get_debit_total_amount, digits_compute=dp.get_precision('Account'), string='Debit Total Amount', type='float', readonly=True),
        'credit_gain_loss_amount'   : fields.function(_get_credit_gain_loss_amount, digits_compute=dp.get_precision('Account'), string='Credit Rounding Gain/Loss Amount', type='float', readonly=True),
        'credit_total_amount'       : fields.function(_get_credit_total_amount, digits_compute=dp.get_precision('Account'), string='Credit Total Amount', type='float', readonly=True),
        'rouding_amount'            : fields.function(_get_rounding_amount, digits_compute=dp.get_precision('Account'), string='Total Rounding Gain/Loss Amount', type='float', readonly=True),
        'total_payment_amount'      : fields.function(_get_pay_amount, digits_compute=dp.get_precision('Account'), string='Total Receipt Amount', type='float', readonly=True),
        'writeoff_amount'           : fields.function(_get_writeoff_amount, digits_compute=dp.get_precision('Account'), string='Difference Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
        'bank_charges_in_company_currency': fields.function(_bank_charges_in_company_currency, digits_compute=dp.get_precision('Account'), string='Bank Charges in Company Currency', type='float', readonly=True),
        'total_in_home_currency': fields.function(_total_in_home_currency, digits_compute=dp.get_precision('Account'), string='Total In Home Currency', type='float', readonly=True),
        'grand_total'               :fields.function(_get_grand_total, digits_compute=dp.get_precision('Account'), string='Grand Total', type='float', readonly=True),
        'rounding_gain_loss_in_comp_currency': fields.function(_rounding_gain_loss_in_company_currency, string='Rounding Gain Loss in Company Currency', type='float', readonly=True),
        'writeoff_amount_home': fields.function(_writeoff_amount_home, digits_compute=dp.get_precision('Account'), string='Difference Amount Home', type='float', readonly=True),
        'paid_amount_in_company_currency': fields.function(_paid_amount_in_company_currency, string='Paid Amount in Company Currency', type='float', readonly=True),
    }

    _defaults = {
        'simplified':_get_simplified,
        'payment_option': 'none',
        'pre_line': 1,
    }

account_voucher()

class account_voucher_line_simple(osv.osv):
    _name = 'account.voucher.line.simple'
    _description = 'Voucher Lines'

    def _currency_id(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a voucher line. It's either the currency of the 
        associated move line (if any) or the currency of the voucher or the company currency.
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.voucher_id.currency_id and line.voucher_id.currency_id.id or line.voucher_id.company_id.currency_id.id
        return res


    _columns = {
        'voucher_id':fields.many2one('account.voucher', 'Voucher', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'account_id':fields.many2one('account.account','Account', required=True),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Dr/Cr'),
        'company_id': fields.related('voucher_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
        'currency_id': fields.function(_currency_id, string='Currency', type='many2one', relation='res.currency', readonly=True),
    }

account_voucher_line_simple()



class account_voucher_line(osv.osv):
    _inherit = 'account.voucher.line'
    _description = 'Voucher Lines'

    def onchange_amount2(self, cr, uid, ids, amount, amount_unreconciled, amount_inv_unreconciled, context=None):
        vals = {}

        if amount < 0:
            amount = 0
        if amount > amount_unreconciled:
            amount = amount_unreconciled
        inv_amount = amount_inv_unreconciled / amount_unreconciled * amount

        vals['reconcile'] = (amount == amount_unreconciled)
        vals['inv_amount'] = inv_amount
        vals['gain_loss_amount'] = inv_amount - amount
        vals['amount'] = amount
        vals['balance_amount'] = amount_unreconciled - amount

        return {'value': vals}

    def onchange_move_line_id2(self, cr, user, ids, move_line_id, date, journal_id, context=None):
        """
        Returns a dict that contains new values and context

        @param move_line_id: latest value from user input for field move_line_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        res = {}
        move_line_pool = self.pool.get('account.move.line')
        journal_pool = self.pool.get('account.journal')
        product_product_obj = self.pool.get('product.product')
        currency_pool = self.pool.get('res.currency')
         
        journal = journal_id and journal_pool.browse(cr, user, journal_id, context=context) or False

        currency_id = journal and journal.currency.id or journal.company_id.currency_id.id

        if move_line_id:
            move_line = move_line_pool.browse(cr, user, move_line_id, context=context)
            if move_line.credit:
                ttype = 'dr'
            else:
                ttype = 'cr'

            ctx = {}
            ctx.update({'date': date})
            ctx2 = {}
            ctx2.update({'date': move_line.cur_date or move_line.date})

            amount_org = 0.0
            amount_invoice = 0.0
            amount_inv_unreconciled = 0.0
            amount_original = 0.0
            amount_unreconciled = 0.0
            gain_loss = 0.0
            line_currency_id = move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id
            company_currency = move_line.company_id.currency_id.id
            rate_inv = currency_pool.browse(cr, user, line_currency_id, context=ctx2).rate
            rate_now = currency_pool.browse(cr, user, line_currency_id, context=ctx).rate
            rate_home = currency_pool.browse(cr, user, company_currency, context=ctx).rate
            rate_payment = currency_pool.browse(cr, user, currency_id, context=ctx).rate
            if move_line.currency_id:
                amount_org = abs(move_line.amount_currency)
                amount_invoice = product_product_obj.round_p(cr, user, abs(move_line.amount_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
                amount_inv_unreconciled = product_product_obj.round_p(cr, user, abs(move_line.amount_residual_currency) / (rate_inv/rate_home) / (rate_home/rate_payment), 'Account')
#                amount_invoice = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_currency), context=ctx2)
#                amount_inv_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_residual_currency), context=ctx2)
#                amount_invoice = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_invoice), context=ctx)
#                amount_inv_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_inv_unreconciled), context=ctx)
                if move_line.currency_id.id == currency_id:
                    amount_original = abs(move_line.amount_currency)
                    amount_unreconciled = abs(move_line.amount_residual_currency)
                else:
                    amount_original = product_product_obj.round_p(cr, user, abs(move_line.amount_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
                    amount_unreconciled = product_product_obj.round_p(cr, user, abs(move_line.amount_residual_currency) / (rate_now/rate_home) / (rate_home/rate_payment), 'Account')
                    #amount_original = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_currency), context=ctx)
#                    amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id.id, company_currency, abs(line.amount_residual_currency), context=ctx)
                    #amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_original), context=ctx)
#                    amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(amount_unreconciled), context=ctx)
            else:
#                raise osv.except_osv(_('Error'), _(str(journal_id) + '---' + str(currency_id)))
                amount_org = abs(move_line.debit - move_line.credit)
                if company_currency == currency_id:
                    amount_invoice = abs(move_line.debit - move_line.credit)
                    amount_original = abs(move_line.debit - move_line.credit)
                    amount_inv_unreconciled = abs(move_line.amount_residual)
                    amount_unreconciled = abs(move_line.amount_residual)
                else:
                    amount_invoice = currency_pool.compute(cr, user, company_currency, currency_id, abs(move_line.debit - move_line.credit), context=ctx)
                    amount_original = currency_pool.compute(cr, user, company_currency, currency_id, abs(move_line.debit - move_line.credit), context=ctx)
                    amount_inv_unreconciled = currency_pool.compute(cr, user, company_currency, currency_id, abs(move_line.amount_residual), context=ctx)
                    amount_unreconciled = currency_pool.compute(cr, user, company_currency, currency_id, abs(move_line.amount_residual), context=ctx)
#            raise osv.except_osv(_('Error'), _(str(amount_invoice) + '---' + str(line.amount_currency)))
#            raise osv.except_osv(_('Error'), _(str(amount_unreconciled) + '---' + str(journal_id)))

#convert to payment Currency


            gain_loss = amount_inv_unreconciled - amount_unreconciled



            res.update({
                'account_id': move_line.account_id.id,
                'type': ttype,
                'currency_id': move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id,
                'name':move_line.move_id.name,
                'account_id':move_line.account_id.id,
                'date_original':move_line.date,
                'date_due':move_line.date_maturity,
                'amount_org': amount_org,
                'amount_invoice': amount_invoice,
                'amount_original': amount_original,
                'amount_inv_unreconciled': amount_inv_unreconciled,
                'amount_unreconciled': amount_unreconciled,
                'gain_loss': gain_loss,
                'balance_amount': amount_unreconciled,
                'amount': 0.00,
            })

        return {
            'value':res,
        }

    def _compute_balance2(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        product_product_obj = self.pool.get('product.product')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            amount_invoice = 0.00
            amount_inv_unreconciled = 0.00
            amount_original = 0.00
            amount_unreconciled = 0.00
            inv_amount = 0.0
            current_amount = 0.0
            ctx = context.copy()
            ctx.update({'date': line.voucher_id.date})
            ctx2 = context.copy()
            ctx2.update({'date': line.move_line_id and line.move_line_id.cur_date or line.move_line_id.date})

            res = {}
            company_currency = line.voucher_id.journal_id.company_id.currency_id.id
            voucher_currency = line.voucher_id.currency_id and line.voucher_id.currency_id.id or company_currency
            move_line = line.move_line_id or False
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            if not move_line:
                res['amount_org'] = 0.0
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
                res['amount_invoice'] = 0.0
                res['amount_inv_unreconciled'] = 0.0
                res['gain_loss'] = 0.0
                res['inv_amount'] = 0.0
                res['gain_loss_amount'] = 0.0
            elif move_line.currency_id:
                rate_inv = move_line.exrate
                rate_now = currency_pool.browse(cr, uid, line_currency_id, context=ctx).rate
                rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
                rate_payment = currency_pool.browse(cr, uid, voucher_currency, context=ctx).rate
                amount_invoice = float_round(abs(move_line.amount_currency) / (rate_inv/rate_home) / (rate_home/rate_payment),2)
                
                if move_line.currency_id.id == voucher_currency:
                    amount_original = abs(move_line.amount_currency)
                    amount_unreconciled = abs(move_line.amount_residual_currency)
                else:
                    amount_original = float_round(abs(move_line.amount_currency) / (rate_now/rate_home) / (rate_home/rate_payment),2)
                    amount_unreconciled = float_round(abs(move_line.amount_residual_currency) / (rate_now/rate_home) / (rate_home/rate_payment),2)
                res['amount_org'] = abs(move_line.amount_currency)
                res['amount_original'] = amount_original
                res['amount_unreconciled'] = amount_unreconciled
                res['amount_invoice'] = amount_invoice
                if voucher_currency == company_currency:
                    amount_inv_unreconciled = abs(move_line.amount_residual)
                else:
                    # add fix 0.01 decimal with
                    if voucher_currency == move_line.currency_id.id:
                        amount_inv_unreconciled = abs(move_line.amount_residual_currency)
                    else:
                        amount_inv_unreconciled = float_round(abs(move_line.amount_residual) * (rate_payment/rate_home),2)
                    #End
                #hastag checking
#                if line.reconcile:
#                    inv_amount = amount_inv_unreconciled
#                else:
                #end
                current_amount = line.amount * (rate_home/ rate_payment) * (rate_now/ rate_home)
                inv_amount = float_round(product_product_obj.round_p(cr, uid, (rate_payment/ rate_home) / (rate_inv/rate_home) * current_amount, 'Account'),2)
                res['amount_inv_unreconciled'] = amount_inv_unreconciled
                res['gain_loss'] = amount_inv_unreconciled - amount_unreconciled

                res['inv_amount'] = inv_amount
                res['gain_loss_amount'] = inv_amount - line.amount
            else:
                if company_currency == voucher_currency:
                    amount_invoice = abs(move_line.debit - move_line.credit)
                    amount_inv_unreconciled = abs(move_line.amount_residual)
                    amount_original = abs(move_line.debit - move_line.credit)
                    amount_unreconciled = abs(move_line.amount_residual)
                    if line.reconcile:
                        inv_amount = amount_inv_unreconciled
                    else:
                        inv_amount = line.amount
                else:
                    amount_original = float_round(currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.debit - move_line.credit), context=ctx),2)
                    amount_unreconciled = float_round(currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx),2)
                    amount_invoice = float_round(currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.debit - move_line.credit), context=ctx),2)
                    amount_inv_unreconciled = float_round(currency_pool.compute(cr, uid, company_currency, voucher_currency, abs(move_line.amount_residual), context=ctx),2)
                    rate_inv = move_line.exrate
                    rate_now = currency_pool.browse(cr, uid, line_currency_id, context=ctx).rate
                    rate_home = currency_pool.browse(cr, uid, company_currency, context=ctx).rate
                    rate_payment = currency_pool.browse(cr, uid, voucher_currency, context=ctx).rate
                    current_amount = line.amount * (rate_home/ rate_payment) * (rate_now/ rate_home)
                    if line.reconcile:
                        inv_amount = amount_inv_unreconciled
                    else:
                        
#                        print '_compute_balance2'
#                        print rate_payment
#                        print rate_home
#                        print rate_inv
#                        print move_line.id
#                        print current_amount
                        inv_amount = float_round(product_product_obj.round_p(cr, uid, (rate_payment/ rate_home) / (rate_inv/rate_home) * current_amount, 'Account'),2)

                res['amount_org'] = abs(move_line.debit - move_line.credit)
                res['amount_original'] = amount_original
                res['amount_unreconciled'] = amount_unreconciled
                res['amount_invoice'] = amount_invoice
                res['amount_inv_unreconciled'] = amount_inv_unreconciled
                res['gain_loss'] = amount_inv_unreconciled - amount_unreconciled
                res['inv_amount'] = inv_amount
                res['gain_loss_amount'] = inv_amount - line.amount
            rs_data[line.id] = res
        return rs_data

    def _qty_balance_amount(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
#            cr.execute("select amount_unreconciled from account_voucher_line where id=" + str(obj.id))
#            res = cr.fetchone()
#            raise osv.except_osv(_('Warning !'), _(str(res[0]) + '---'))
            res[obj.id] = obj.amount_unreconciled - obj.amount
        return res
#amount_org, 

    def _amount_home(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        voucher_rate = company_currency_rate = 1.0
        for line in self.browse(cr, uid, ids, context=context):
            company_currency = line.voucher_id and line.voucher_id.company_id and line.voucher_id.company_id.currency_id or False
            voucher_currency = line.voucher_id and line.voucher_id.journal_id and line.voucher_id.journal_id.currency or company_currency or False
            if voucher_currency.id == company_currency.id:
                res[line.id] = line.amount
            else:
                ctx = {'date':line.voucher_id.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[line.id] =  float_round(line.amount / voucher_rate * company_rate,2)
        return res

    def _amount_inv_home(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            company_currency = line.voucher_id and line.voucher_id.company_id and line.voucher_id.company_id.currency_id or False
            voucher_currency = line.voucher_id and line.voucher_id.journal_id and line.voucher_id.journal_id.currency or company_currency or False
            if voucher_currency.id == company_currency.id:
                res[line.id] = line.amount
            else:
                ctx = {'date':line.move_line_id and line.move_line_id.cur_date or line.move_line_id.date}
                voucher_rate = self.pool.get('res.currency').browse(cr, uid, voucher_currency.id, context=ctx).rate
                company_rate = self.pool.get('res.currency').browse(cr, uid, company_currency.id, context=ctx).rate
                res[line.id] =  float_round(line.amount / voucher_rate * company_rate,2)
        return res

    _columns = {
        'invoice_no': fields.related('move_line_id','invoice_no', type='char', size=64, string='Supplier Invoice No'),
        'due_date': fields.related('move_line_id','due_date', string='Due date', type='date'),
        'amount_org': fields.function(_compute_balance2, multi='dc', type='float', string='Original Amount', digits_compute=dp.get_precision('Account')),
        'amount_original': fields.function(_compute_balance2, multi='dc', type='float', string='Original Amount', store=True, digits_compute=dp.get_precision('Account')),
        'amount_unreconciled': fields.function(_compute_balance2, multi='dc', type='float', string='Open Balance', store=True, digits_compute=dp.get_precision('Account')),
        'amount_invoice': fields.function(_compute_balance2, multi='dc', type='float', string='Invoice Amount', store=True, digits_compute=dp.get_precision('Account')),
        'amount_inv_unreconciled': fields.function(_compute_balance2, multi='dc', type='float', string='Inv Open Balance', store=True, digits_compute=dp.get_precision('Account')),
        'gain_loss': fields.function(_compute_balance2, multi='dc', type='float', string='Gain/Loss', store=True, digits_compute=dp.get_precision('Account')),
        'inv_amount': fields.function(_compute_balance2, multi='dc', type='float', string='Inv Amount', digits_compute=dp.get_precision('Account'), store=True),
        'gain_loss_amount': fields.function(_compute_balance2, multi='dc', type='float', string='Gain/Loss Amount', digits_compute=dp.get_precision('Account'), store=True),
        'balance_amount': fields.function(_qty_balance_amount, type='float', string='Balance Amount', digits_compute=dp.get_precision('Account')),
        'amount_home': fields.function(_amount_home, digits_compute=dp.get_precision('Account'), string='Amount Home', type='float', readonly=True),
        'amount_inv_home': fields.function(_amount_inv_home, digits_compute=dp.get_precision('Account'), string='Amount Inv Home', type='float', readonly=True),
    }

account_voucher_line()

class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _description = 'Journal Items'

    def reconcile_partial(self, cr, uid, ids, type='auto', context=None, writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
        move_rec_obj = self.pool.get('account.move.reconcile')
        merges = []
        unmerge = []
        total = 0.0
        merges_rec = []
        company_list = []
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning !'), _('To reconcile the entries company should be the same for all entries'))
            company_list.append(line.company_id.id)
#        raise osv.except_osv(_('Error'), _(str(ids)))
        for line in self.browse(cr, uid, ids, context=context):
            if line.account_id.currency_id:
                currency_id = line.account_id.currency_id
            else:
                currency_id = line.company_id.currency_id
            if line.reconcile_id:
                raise osv.except_osv(_('Warning'), _('Already Reconciled!'))
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    if not line2.reconcile_id:
                        if line2.id not in merges:
                            merges.append(line2.id)
                        total += (line2.debit or 0.0) - (line2.credit or 0.0)
                merges_rec.append(line.reconcile_partial_id.id)
            else:
                unmerge.append(line.id)
                total += (line.debit or 0.0) - (line.credit or 0.0)
        if self.pool.get('res.currency').is_zero(cr, uid, currency_id, total):
            res = self.reconcile(cr, uid, merges+unmerge, context=context, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id)
            return res
        
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_partial_ids': map(lambda x: (4,x,False), merges+unmerge)
        })
        
        move_rec_obj.reconcile_partial_check(cr, uid, [r_id] + merges_rec, context=context)
        return True

    def _amount_residual(self, cr, uid, ids, field_names, args, context=None):
        """
           This function returns the residual amount on a receivable or payable account.move.line.
           By default, it returns an amount in the currency of this journal entry (maybe different
           of the company currency), but if you pass 'residual_in_company_currency' = True in the
           context then the returned amount will be in company currency.
        """
        res = {}
        if context is None:
            context = {}
        cur_obj = self.pool.get('res.currency')
        acc_move_recon_obj = self.pool.get('account.move.reconcile')
        for move_line in self.browse(cr, uid, ids, context=context):
            res[move_line.id] = {
                'amount_original':0.0,
                'amount_residual': 0.0,
                'amount_residual_currency': 0.0,
                'amount_res': 0.0,
            }

            if move_line.reconcile_id:
                continue
            if not move_line.account_id.type in ('payable', 'receivable'):
                #this function does not suport to be used on move lines not related to payable or receivable accounts
                continue

            if move_line.currency_id:
                move_line_total = move_line.amount_currency
                sign = move_line.amount_currency < 0 and -1 or 1
            else:
                move_line_total = move_line.debit - move_line.credit
                sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
            amount_original = move_line_total
            line_total_in_company_currency =  move_line.debit - move_line.credit
            context_unreconciled = context.copy()
            if move_line.reconcile_partial_id:
                acc_move_recon_id = acc_move_recon_obj.browse(cr, uid, move_line.reconcile_partial_id.id, context=None)

                for payment_line in acc_move_recon_id.line_partial_ids:
                    if payment_line.id == move_line.id:
                        continue
                    if payment_line.currency_id and move_line.currency_id and payment_line.currency_id.id == move_line.currency_id.id:
                            move_line_total += payment_line.amount_currency
                    else:
                        if move_line.currency_id:
                            context_unreconciled.update({'date': payment_line.date})
                            amount_in_foreign_currency = float_round(cur_obj.compute(cr, uid, move_line.company_id.currency_id.id, move_line.currency_id.id, (payment_line.debit - payment_line.credit), round=False, context=context_unreconciled),2)
                            move_line_total += amount_in_foreign_currency
                        else:
                            move_line_total += (payment_line.debit - payment_line.credit)
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)

            result = move_line_total
#            res[move_line.id]['amount_residual_currency'] =  sign * (move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result)
            res[move_line.id]['amount_original'] = sign * float_round((move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, amount_original) or amount_original),2)

            res[move_line.id]['amount_residual'] = sign * line_total_in_company_currency
            ctx = {'date': move_line.cur_date or move_line.date}
            
            res[move_line.id]['amount_residual_currency'] = sign * (move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result)
            if move_line.currency_id:
                move_line_res = abs((move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result))
            else:
                move_line_res = abs(line_total_in_company_currency)

            res[move_line.id]['amount_res'] = move_line_res
        return res

    def _currency(self, cursor, user, ids, name, args, context=None):
        res = {}
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        default_currency = res_users_obj.browse(cursor, user,
                user, context=context).company_id.currency_id
        for statement in self.browse(cursor, user, ids, context=context):
            currency = statement.currency_id
            if not currency:
                currency = default_currency
            res[statement.id] = currency.id
        currency_names = {}
        for currency_id, currency_name in res_currency_obj.name_get(cursor,
                user, [x for x in res.values()], context=context):
            currency_names[currency_id] = currency_name
        for statement_id in res.keys():
            currency_id = res[statement_id]
            res[statement_id] = (currency_id, currency_names[currency_id])
        return res

    _columns = {
        'amount_residual_currency': fields.function(_amount_residual, string='Residual Amount', multi="residual", help="The residual amount on a receivable or payable of a journal entry expressed in its currency (maybe different of the company currency)."),
        'amount_original': fields.function(_amount_residual, string='Amount Original', multi="residual", help="The original amount on a receivable or payable of a journal entry."),
        'amount_res': fields.function(_amount_residual, string='Amount Res', multi="residual", help="The residual amount on a receivable or payable of a journal entry."),
        'currency': fields.function(_currency, string='Currency',
            type='many2one', relation='res.currency'),
        'cur_date': fields.date('cur_date', required=True, states={'posted':[('readonly',True)]}, select=True),
        'is_depo': fields.boolean('Deposit Value'),
        'due_date': fields.related('invoice','due_date', string='Due date', type='date'),
        'invoice_no': fields.related('invoice','invoice_no', type='char', size=64, string='Supplier Invoice No'),
        'move_name': fields.related('move_id', 'name', string='Move Name', type='char', size=64),
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        user_company_currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        if context.get('type') and context.get('status'):
            if context.get('type') == 'payment':
                account_type = 'payable'
            else:
                account_type = 'receivable'

            if context.get('status') == 'debit':
                status = ('debit', '>', 0)
            else:
                status = ('credit', '>', 0)
            if context.get('multi_partner'):
                partner_id = context.get('multi_partner')
                partner_data = self.pool.get('res.partner').browse(cr, uid, partner_id)
                parent_partner = False
                prt1_ids = []
                if partner_data.parent_id:
                    parent_partner = True
                    parent_id = partner_data.parent_id.id
                    cr.execute('select id from res_partner where parent_id = %d'% parent_id)
                    res1 = cr.fetchall()
                    for r in res1:
                        prt1_ids.append(r[0])
            else:
                partner_id = False
                parent_partner = False

            move_line_pool = self.pool.get('account.move.line')
            if parent_partner:
##                move_ids = move_line_pool.search(cr, uid, [status, ('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id','in',prt1_ids)], context=context)
#                move_ids = move_line_pool.search(cr, uid, [], context=context)
                account_move_lines = move_line_pool.browse(cr, uid, move_line_pool.search(cr, uid, [status,('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id','in',prt1_ids)], context=None), context=context)
            else:
#                
##                move_ids = move_line_pool.search(cr, uid, [status, ('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', context.get('multi_partner'))], context=context)
#                move_ids = move_line_pool.search(cr, uid, [], context=context)
                if partner_id:
                    account_move_lines = move_line_pool.browse(cr, uid, move_line_pool.search(cr, uid, [status, ('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=None), context=context) 
                else:
                    account_move_lines = move_line_pool.browse(cr, uid, move_line_pool.search(cr, uid, [status, ('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False)], context=None), context=context)

            move_line_ids = []
            for line in account_move_lines:
                if line.credit and line.reconcile_partial_id and line.is_depo != True and context.get('type') == 'receipt':
                    if line.is_refund != True:
                        continue
                if line.debit and line.reconcile_partial_id and line.is_refund == True and context.get('type') == 'receipt':
                    continue
                if line.debit and line.reconcile_partial_id and line.is_depo == True and context.get('type') == 'receipt':
                    continue

                if line.debit and line.reconcile_partial_id and line.is_depo != True and context.get('type') == 'payment':
                     if line.is_refund != True:
                        continue
                if line.credit and line.reconcile_partial_id and line.is_refund == True and context.get('type') == 'payment':
                    continue
                if line.credit and line.reconcile_partial_id and line.is_depo == True and context.get('type') == 'payment':
                    continue
                move_line_ids.append(line.id)
            args.append(('id','in',move_line_ids))
#            args.append(('id','=',1184))
#            partner_data = self.pool.get('res.partner').browse(cr, uid, context.get('multi_partner'))
#            parent_partner = False
#            prt1_ids = []
#            if partner_data.parent_id:
#                parent_partner = True
#                parent_id = partner_data.parent_id.id
#                cr.execute('select id from res_partner where parent_id = %d'% parent_id)
#                res1 = cr.fetchall()
#                for r in res1:
#                    prt1_ids.append(r[0])
#
#            if context.get('status') == 'debit':
#                args.extend([('debit', '>', 0),('is_depo', '<>', True)])
#            else:
#                args.extend([('credit', '>', 0),('is_depo', '=', True)])
#            if parent_partner:
#                args.extend([('state','=','valid'), ('account_id.type', '=', account_type),('reconcile_id','=', False),('partner_id','in',prt1_ids)])
#            else:
#                args.extend([('state','=','valid'), ('account_id.type', '=', account_type),('reconcile_id','=', False),('partner_id','=',context.get('multi_partner'))])
        return super(account_move_line, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

    def searchxx(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        user_company_currency_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id
        if context.get('voucher_type') and context.get('voucher_partner_id'):
            partner_data = self.pool.get('res.partner').browse(cr, uid, context.get('voucher_partner_id'), context)
            parent_partner = False
            prt1_ids = []
            if partner_data.parent_id:
                parent_partner = True
                parent_id = partner_data.parent_id.id
                cr.execute('select id from res_partner where parent_id = %d'% parent_id)
                res1 = cr.fetchall()
                for r in res1:
                    prt1_ids.append(r[0])
            if parent_partner:
                args.append(('partner_id','in',prt1_ids))
            else:
                args.append(('partner_id','=',context.get('voucher_partner_id')))

            if user_company_currency_id == context.get('currency_id'):
                args.append(('currency_id','=',False))
            else:
                args.append(('currency_id','=',context.get('currency_id')))
        
            args.append(('reconcile_id', '=', False))
            if context.get('deposit'):
                if context.get('voucher_type') in ('purchase', 'payment'):
                    args.append(('account_id','=',partner_data.property_account_supplier_deposit.id))
                    args.append(('debit', '>' , 0))
                else:
                    args.append(('account_id','=',partner_data.property_account_deposit.id))
                    args.append(('credit', '>' , 0))
            else:
                args.append(('account_id','in',[partner_data.property_account_receivable.id,partner_data.property_account_payable.id]))
                if context.get('voucher_type') in ('purchase', 'payment'):
                    args.append(('debit', '>' , 0))
                else:
                    args.append(('credit', '>' , 0))
            #------------- below code added by sunil --------------------        
            if context.get('inv_knockoff'):
                args.append(('journal_id.type', 'in', ('sale','purchase','situation')))
            #-------------
            context.pop('voucher_partner_id')
            context.pop('voucher_type')
        if context.get('multi_partner'):
            partner_data = self.pool.get('res.partner').browse(cr, uid, context.get('multi_partner'))
            parent_partner = False
            prt1_ids = []
            if partner_data.parent_id:
                parent_partner = True
                parent_id = partner_data.parent_id.id
                cr.execute('select id from res_partner where parent_id = %d'% parent_id)
                res1 = cr.fetchall()
                for r in res1:
                    prt1_ids.append(r[0])

            account_type = 'receivable'
#            if context.get('multi_type') == 'payment':
#                account_type = 'payable'
#                args.append(('credit', '>', 0))
#            else:
#                args.append(('debit', '>', 0))
            #args.extend([('state','=','valid'), ('account_id.type', 'in', ('receivable','payable')),('reconcile_id','=', False),('partner_id','=',context.get('multi_partner'))])

            if parent_partner:
                args.extend([('state','=','valid'), ('account_id.type', 'in', ('receivable','payable')),('reconcile_id','=', False),('partner_id','in',prt1_ids)])
            else:
                args.extend([('state','=','valid'), ('account_id.type', 'in', ('receivable','payable')),('reconcile_id','=', False),('partner_id','=',context.get('multi_partner'))])
        return super(account_move_line, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

#    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
#        if context is None:
#            context = {}
#        if context and context.get('next_partner_only', False):
#            if not context.get('partner_id', False):
#                partner = self.get_next_partner_only(cr, uid, offset, context)
#            else:
#                partner = context.get('partner_id', False)
#            if not partner:
#                return []
#            args.append(('partner_id', '=', partner[0]))
#        return super(
account_move_line()

class res_company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'property_currency_gain_loss': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            view_load=True,
            string ='Currency Gain Loss Account',
            method=True),
    }

res_company()

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'property_bank_charges': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            view_load=True,
            string ='Bank Charges Account',
            method=True)
    }

account_journal()

class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _credit_debit_get(self, cr, uid, ids, field_names, arg, context=None):
        query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
        cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE a.type IN ('receivable','payable')
                      AND l.partner_id IN %s
                      AND l.reconcile_id IS NULL
                      AND (l.is_depo is NULL or l.is_depo = False)
                      AND """ + query + """
                      GROUP BY l.partner_id, a.type
                      """,
                   (tuple(ids),))
        maps = {'receivable':'credit', 'payable':'debit' }
        res = {}
#        tes = []
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0)
        for pid,type,val in cr.fetchall():
#            if is_depo is None: is_depo=False
#            tes.append(str(type) + str(is_depo))
            if val is None: val=0
#            res[pid][maps[type]] = (type=='receivable') and val or -val
            res[pid][maps[type]] = (type=='receivable') and val or -val

        cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE a.type IN ('receivable','payable')
                      AND l.partner_id IN %s
                      AND l.reconcile_id IS NULL
                      AND l.is_depo = True
                      AND """ + query + """
                      GROUP BY l.partner_id, a.type
                      """,
                   (tuple(ids),))
        maps2 = {'receivable':'depo_credit', 'payable':'depo_debit' }
#        raise osv.except_osv(_('Test AP or AR!'),_(str(res)))
#        raise osv.except_osv(_('Test AP or AR!'),_(tes))
        for pid2,type2,val2 in cr.fetchall():
#            if is_depo is None: is_depo=False
#            tes.append(str(type) + str(is_depo))
            if val2 is None: val2=0
#            res[pid][maps[type]] = (type=='receivable') and val or -val
#            raise osv.except_osv(_('Test AP or AR!'),_(str(val2) + '--' + str(type2)))
            res[pid2][maps2[type2]] = (type2=='payable') and val2 or -val2
        return res

    def _credit_debit_depo_get(self, cr, uid, ids, field_names, arg, context=None):
#        query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
#        cr.execute("""SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
#                      FROM account_move_line l
#                      LEFT JOIN account_account a ON (l.account_id=a.id)
#                      WHERE a.type IN ('receivable','payable')
#                      AND l.partner_id IN %s
#                      AND l.reconcile_id IS NULL
#                      AND l.is_depo = True
#                      AND """ + query + """
#                      GROUP BY l.partner_id, a.type
#                      """,
#                   (tuple(ids),))
#        maps = {'receivable':'depo_credit', 'payable':'depo_debit' }
#        res = {}
#        for id in ids:
#            res[id] = {}.fromkeys(field_names, 0)
#        for pid,type,val in cr.fetchall():
#            if val is None: val=0
#            res[pid][maps[type]] = (type=='receivable') and val or -val
#        raise osv.except_osv(_('Test AP or AR!'),_(str(res)))
#        for id in ids:
#            res[id] = {}.fromkeys(field_names, 0)
        return res

    def _asset_difference_search(self, cr, uid, obj, name, type, args, context=None):
        if not args:
            return []
        having_values = tuple(map(itemgetter(2), args))
        where = ' AND '.join(
            map(lambda x: '(SUM(debit-credit) %(operator)s %%s)' % {
                                'operator':x[1]},args))
        query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
        cr.execute(('SELECT partner_id FROM account_move_line l '\
                    'WHERE account_id IN '\
                        '(SELECT id FROM account_account '\
                        'WHERE type=%s AND active) '\
                    'AND reconcile_id IS NULL '\
                    'AND (is_depo is NULL or is_depo = False) '\
                    'AND '+query+' '\
                    'AND partner_id IS NOT NULL '\
                    'GROUP BY partner_id HAVING '+where),
                   (type,) + having_values)
        res = cr.fetchall()
        if not res:
            return [('id','=','0')]
        return [('id','in',map(itemgetter(0), res))]

    def _asset_difference_depo_search(self, cr, uid, obj, name, type, args, context=None):
        if not args:
            return []
        having_values = tuple(map(itemgetter(2), args))
        where = ' AND '.join(
            map(lambda x: '(SUM(debit-credit) %(operator)s %%s)' % {
                                'operator':x[1]},args))
        query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
        cr.execute(('SELECT partner_id FROM account_move_line l '\
                    'WHERE account_id IN '\
                        '(SELECT id FROM account_account '\
                        'WHERE type=%s AND active) '\
                    'AND reconcile_id IS NULL '\
                    'AND is_depo = True '\
                    'AND '+query+' '\
                    'AND partner_id IS NOT NULL '\
                    'GROUP BY partner_id HAVING '+where),
                   (type,) + having_values)
        res = cr.fetchall()
        if not res:
            return [('id','=','0')]
        return [('id','in',map(itemgetter(0), res))]

    def _credit_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_search(cr, uid, obj, name, 'receivable', args, context=context)

    def _credit_depo_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_depo_search(cr, uid, obj, name, 'receivable', args, context=context)

    def _debit_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_search(cr, uid, obj, name, 'payable', args, context=context)

    def _debit_depo_search(self, cr, uid, obj, name, args, context=None):
        return self._asset_difference_depo_search(cr, uid, obj, name, 'payable', args, context=context)

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Payment Journal'),
        'credit': fields.function(_credit_debit_get,
            fnct_search=_credit_search, string='Total Receivable', multi='dc', help="Total amount this customer owes you."),
        'debit': fields.function(_credit_debit_get, fnct_search=_debit_search, string='Total Payable', multi='dc', help="Total amount you have to pay to this supplier."),
        'depo_credit': fields.function(_credit_debit_get,
            fnct_search=_credit_depo_search, string='Total Customer Deposit', multi='dc', help="Total amount this customer deposit."),
        'depo_debit': fields.function(_credit_debit_get, fnct_search=_debit_depo_search, string='Total Supplier Deposit', multi='dc', help="Total amount this supplier deposit."),
    }
res_partner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

