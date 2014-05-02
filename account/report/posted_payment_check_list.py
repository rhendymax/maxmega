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

class posted_payment_check_list(report_sxw.rml_parse):
    _name = 'posted.payment.check.list'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.partner_code_from = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
        self.partner_code_to = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
        self.filter_selection = data['form']['filter_selection']
        self.supplier_code_from = data['form']['supplier_code_from'] or False
        self.supplier_code_to = data['form']['supplier_code_to'] or False
        self.partner_ids_selection = data['form']['partner_ids'] or False
        self.journal_ids_selection = data['form']['journal_ids'] or False
        return super(posted_payment_check_list, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(posted_payment_check_list, self).__init__(cr, uid, name, context=context)
        self.payment_count = 0.00
        self.footer_credit_note_home = 0.00
        self.footer_cheque_home = 0.00
        self.footer_alloc_inv_home = 0.00
        self.footer_bank_charges_home = 0.00
        self.footer_gain_loss_home = 0.00
        self.footer_deposit_home = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_code_from': self._get_code_from,
            'get_code_to': self._get_code_to,
            'payment_count' : self._payment_count,
            'footer_credit_note_home' : self._footer_credit_note_home,
            'footer_cheque_home' : self._footer_cheque_home,
            'footer_alloc_inv_home' : self._footer_alloc_inv_home,
            'footer_bank_charges_home' : self._footer_bank_charges_home,
            'footer_gain_loss_home' : self._footer_gain_loss_home,
            'footer_deposit_home' : self._footer_deposit_home,
            })

    def _payment_count(self):
        return self.payment_count

    def _footer_credit_note_home(self):
        return self.footer_credit_note_home

    def _footer_cheque_home(self):
        return self.footer_cheque_home

    def _footer_alloc_inv_home(self):
        return self.footer_alloc_inv_home

    def _footer_bank_charges_home(self):
        return self.footer_bank_charges_home

    def _footer_gain_loss_home(self):
        return self.footer_gain_loss_home

    def _footer_deposit_home(self):
        return self.footer_deposit_home

    def _get_code_from(self):
        if self.filter_selection == 'supp_code':
            return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
        elif self.filter_selection == 'supp_code_input':
            return self.supplier_code_from or False
        else:
            return False

    def _get_code_to(self):
        if self.filter_selection == 'supp_code':
            return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
        elif self.filter_selection == 'supp_code_input':
            return self.supplier_code_to or False
        else:
            return False

    def _get_lines(self):
        results = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        # partner
        res_partner_obj = self.pool.get('res.partner')

        if self.filter_selection == 'supp_code':
            val_part = []
            code_from = self.partner_code_from
            code_to = self.partner_code_to
            if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
                val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
            if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
                val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
            val_part.append(('supplier', '=', True))
            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')

        elif self.filter_selection == 'supp_code_input':
            val_part = []
            val_part.append(('supplier', '=', True))
            supp_from = self.supplier_code_from
            if supp_from:
                self.cr.execute("select ref " \
                                "from res_partner "\
                                "where supplier = True and " \
                                "ref ilike '" + str(supp_from) + "%' " \
                                "order by ref limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    val_part.append(('ref', '>=', qry['ref']))
            supp_to = self.supplier_code_to
            if supp_to:
                self.cr.execute("select ref " \
                                "from res_partner "\
                                "where supplier = True and " \
                                "ref ilike '" + str(supp_to) + "%' " \
                                "order by ref desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    val_part.append(('ref', '<=', qry['ref']))
            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')


        elif self.filter_selection == 'selection_code':
            if self.partner_ids_selection:
                part_ids = self.partner_ids_selection

        val_voucher = []
        account_voucher_obj = self.pool.get('account.voucher')
        val_voucher.append(('date', '>=', date_from))
        val_voucher.append(('date', '<=', date_to))
        val_voucher.append(('type', '=', 'payment'))
        val_voucher.append(('state', '=', 'posted'))
        val_voucher.append(('partner_id', 'in', part_ids))
        if self.journal_ids_selection:
            val_voucher.append(('journal_id', 'in', self.journal_ids_selection))
        voucher_ids = account_voucher_obj.search(self.cr, self.uid, val_voucher, order='date ASC')


        for voucher_id in account_voucher_obj.browse(self.cr, self.uid, voucher_ids):
            res = {}
            lines_ids = []
            amount_all = 0.00
            amount_home_all = 0.00
            gain_loss_all = 0.00
            credit_inv_amt_credit = 0.00
            credit_inv_home_credit = 0.00

            alloc_inv_amt_debit = 0.00
            alloc_inv_home_debit = 0.00

            for lines in voucher_id.line_dr_ids:
                if lines.amount > 0:
                    amount_all += lines.amount
                    alloc_inv_amt_debit += lines.amount
                    amount_home = lines.amount_home or 0.00
                    amount_home_all += amount_home
                    amount_inv_home = lines.amount_inv_home or 0.00
                    alloc_inv_home_debit += amount_inv_home
                    gain_loss = (amount_inv_home - amount_home) or 0.00
                    gain_loss_all += gain_loss
                    lines_ids.append({
                        'voucher_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
                        'date' : lines.move_line_id and lines.move_line_id.date or False,
                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
                        'alloc_inv_amt' : lines.amount or 0.00,
                        'cheque_home' : lines.amount_home or 0.00,
                        'alloc_inv_home': amount_inv_home,
                        'gain_loss': gain_loss,
                        })
            for lines in voucher_id.line_cr_ids:
                if lines.amount > 0:
                    sign = -1
                    amount_all -= lines.amount
                    credit_inv_amt_credit += (sign * lines.amount)

                    amount_home = lines.amount_home or 0.00
                    amount_home_all -= amount_home
                    amount_inv_home = lines.amount_inv_home or 0.00
                    credit_inv_home_credit += (sign * amount_inv_home)
                    gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
                    gain_loss_all -= gain_loss
                    lines_ids.append({
                        'credit_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
                        'date' : lines.move_line_id and lines.move_line_id.date or False,
                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
                        'credit_inv_amt' : (sign * lines.amount) or 0.00,
                        'cheque_home' : (sign * lines.amount_home) or 0.00,
                        'credit_inv_home': (sign * amount_inv_home),
                        'gain_loss': gain_loss,
                        })
            self.payment_count += 1
            res['voucher_no'] = voucher_id.number
            res['supp_ref'] = voucher_id.partner_id and voucher_id.partner_id.ref or ''
            res['supp_name'] = voucher_id.partner_id and voucher_id.partner_id.name or ''
            res['ex_glan'] = voucher_id.company_id and voucher_id.company_id.property_currency_gain_loss and  voucher_id.company_id.property_currency_gain_loss.code or ''
            res['cheque_no'] = voucher_id.cheque_no or ''
            res['curr_name'] = voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.name or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.name or ''
            res['cheque_date'] = voucher_id.date or False
            res['bank_glan'] = voucher_id.journal_id and voucher_id.journal_id.property_bank_charges and voucher_id.journal_id.property_bank_charges.code or ''
            ctx = {'date':voucher_id.date}
            res['cur_exrate'] = self.pool.get('res.currency').browse(self.cr, self.uid, voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.id or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.id, context=ctx).rate or 0.00
            res['cheq_amount'] = amount_all
            res['cheq_amount_home'] = amount_home_all
            self.footer_cheque_home += amount_home_all
            res['gain_loss'] = gain_loss_all
            self.footer_gain_loss_home += gain_loss_all
            res['credit_inv_amt'] = credit_inv_amt_credit
            res['credit_inv_home'] = credit_inv_home_credit
            self.footer_credit_note_home += credit_inv_home_credit
            res['alloc_inv_amt'] = alloc_inv_amt_debit
            res['alloc_inv_home'] = alloc_inv_home_debit
            self.footer_alloc_inv_home += alloc_inv_home_debit
            res['bank_draft'] = voucher_id.bank_draft_no or ''
            res['bank_chrgs'] = voucher_id.bank_charges_amount or 0.00
            res['bank_chrgs_home'] = voucher_id.bank_charges_in_company_currency or 0.00
            self.footer_bank_charges_home += voucher_id.bank_charges_in_company_currency or 0.00
            res['deposit_amt'] = voucher_id.writeoff_amount or 0.00
            res['deposit_amt_home'] = voucher_id.writeoff_amount_home or 0.00
            self.footer_deposit_home += voucher_id.writeoff_amount_home or 0.00
            res['lines'] = lines_ids
            results.append(res)
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(results,'xxx'))
        return results 
    
report_sxw.report_sxw('report.posted.payment.check.list_landscape', 'account.voucher',
    'addons/max_custom_report/account/report/posted_payment_check_list.rml', parser=posted_payment_check_list, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
