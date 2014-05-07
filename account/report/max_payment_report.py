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

class max_payment_report(report_sxw.rml_parse):
    _name = 'max.payment.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        account_journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        qry_jour = ''
        val_jour = []
        
        report_type = data['form']['report_type']
        partner_ids = False
        journal_ids = False
        if report_type == 'receivable':
            data_search = data['form']['cust_search_vals']
            qry_supp = 'customer = True'
            val_part.append(('customer', '=', True))

        elif report_type == 'payable':
            data_search = data['form']['supplier_search_vals']

            if data['form']['supp_selection'] == 'all':
                qry_supp = 'supplier = True'
                val_part.append(('supplier', '=', True))
            elif data['form']['supp_selection'] == 'supplier':
                qry_supp = 'supplier = True and sundry = False'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', False))
            elif data['form']['supp_selection'] == 'sundry':
                qry_supp = 'supplier = True and sundry = True'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', True))
        
        partner_default_from = data['form']['partner_default_from'] and data['form']['partner_default_from'][0] or False
        partner_default_to = data['form']['partner_default_to'] and data['form']['partner_default_to'][0] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False
        
        if data_search == 'code':
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref:
                    data_found = True
                    val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref:
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).ref))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    self.cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))
                #print val_part
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        elif data_search == 'name':
            if data['form']['filter_selection'] == 'all_vall':
                self.partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(self.cr, self.uid, partner_default_from) and res_partner_obj.browse(self.cr, self.uid, partner_default_from).name:
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(self.cr, self.uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(self.cr, self.uid, partner_default_to) and res_partner_obj.browse(self.cr, self.uid, partner_default_to).name:
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(self.cr, self.uid, partner_default_to).name))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    self.cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                if data_found:
                    partner_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        self.partner_ids = partner_ids
        
        #Period
        period_default_from = data['form']['period_default_from'] and data['form']['period_default_from'][0] or False
        period_default_from = period_default_from and period_obj.browse(self.cr, self.uid, period_default_from) or False
        period_default_to = data['form']['period_default_to'] and data['form']['period_default_to'][0] or False
        period_default_to = period_default_to and period_obj.browse(self.cr, self.uid, period_default_to) or False

        period_input_from = data['form']['period_input_from'] or False
        period_input_to = data['form']['period_input_to'] or False

        if data['form']['date_selection'] == 'none_sel':
            self.period_ids = False
            self.date_from = False
            self.date_to = False
        elif data['form']['date_selection'] == 'period_sel':
            val_period = []
            if data['form']['period_filter_selection'] == 'def':
                if period_default_from and period_default_from.date_start:
                    val_period.append(('date_start', '>=', period_default_from.date_start))
                if period_default_to and period_default_to.date_start:
                    val_period.append(('date_start', '<=', period_default_to.date_start))
        #        period_criteria_search.append(('special', '=', False))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
                if period_input_from:
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '>=', qry['code']))
                if period_input_to:
                    self.cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_to) + "%' " \
                                    "order by code limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '<=', qry['code']))
                self.period_ids = period_obj.search(self.cr, self.uid, val_period)
            self.date_from = False
            self.date_to = False
        else:
            self.period_ids = False
            self.date_from = data['form']['date_from']
            self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#journal
        qry_jour = "type in ('bank', 'cash')"
        val_jour.append(('type', 'in', ('bank', 'cash')))

        journal_default_from = data['form']['journal_default_from'] and data['form']['journal_default_from'][0] or False
        journal_default_to = data['form']['journal_default_to'] and data['form']['journal_default_to'][0] or False
        journal_input_from = data['form']['journal_input_from'] or False
        journal_input_to = data['form']['journal_input_to'] or False

        if data['form']['journal_selection'] == 'all_vall':
            journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')

        if data['form']['journal_selection'] == 'name':
            data_found = False
            if journal_default_from and account_journal_obj.browse(self.cr, self.uid, journal_default_from) and account_journal_obj.browse(self.cr, self.uid, journal_default_from).name:
                data_found = True
                val_jour.append(('name', '>=', account_journal_obj.browse(self.cr, self.uid, journal_default_from).name))
            if journal_default_to and account_journal_obj.browse(self.cr, self.uid, journal_default_to) and account_journal_obj.browse(self.cr, self.uid, journal_default_to).name:
                data_found = True
                val_jour.append(('name', '<=', account_journal_obj.browse(self.cr, self.uid, journal_default_to).name))
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'input':
            data_found = False
            if journal_input_from:
                self.cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_jour.append(('name', '>=', qry['name']))
            if journal_input_to:
                self.cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_jour.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'selection':
            if data['form']['journal_ids']:
                journal_ids = data['form']['journal_ids']
        self.journal_ids = journal_ids

        self.report_type = data['form']['report_type']

        #print self.period_ids
        return super(max_payment_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(max_payment_report, self).__init__(cr, uid, name, context=context)
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
            'get_header_title': self._get_header,
            'payment_count' : self._payment_count,
            'footer_credit_note_home' : self._footer_credit_note_home,
            'footer_cheque_home' : self._footer_cheque_home,
            'footer_alloc_inv_home' : self._footer_alloc_inv_home,
            'footer_bank_charges_home' : self._footer_bank_charges_home,
            'footer_gain_loss_home' : self._footer_gain_loss_home,
            'footer_deposit_home' : self._footer_deposit_home,
            })
        
    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Posted Payment Check List Report'
        elif self.report_type == 'receivable':
            header = 'Posted Receipt Check List Report'
        return header
    
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

    

    def _get_lines(self):
        results = []
        # partner
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')

#        if self.filter_selection == 'supp_code':
#            val_part = []
#            code_from = self.partner_code_from
#            code_to = self.partner_code_to
#            if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#                val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#            if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#                val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#            val_part.append(('supplier', '=', True))
#            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#        elif self.filter_selection == 'supp_code_input':
#            val_part = []
#            val_part.append(('supplier', '=', True))
#            supp_from = self.supplier_code_from
#            if supp_from:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_from) + "%' " \
#                                "order by ref limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '>=', qry['ref']))
#            supp_to = self.supplier_code_to
#            if supp_to:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_to) + "%' " \
#                                "order by ref desc limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '<=', qry['ref']))
#            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#
#        elif self.filter_selection == 'selection_code':
#            if self.partner_ids_selection:
#                part_ids = self.partner_ids_selection
#
#        val_voucher = []
#        account_voucher_obj = self.pool.get('account.voucher')
#        val_voucher.append(('date', '>=', date_from))
#        val_voucher.append(('date', '<=', date_to))
#        val_voucher.append(('type', '=', 'payment'))
#        val_voucher.append(('state', '=', 'posted'))
#        val_voucher.append(('partner_id', 'in', part_ids))
#        if self.journal_ids_selection:
#            val_voucher.append(('journal_id', 'in', self.journal_ids_selection))
        type = self.report_type
        qry_type = ''
        if type == 'payable':
            qry_type = "and l.type in ('payment') "
        elif type == 'receivable':
            qry_type = "and l.type in ('receipt') "
        partner_ids = self.partner_ids or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "

        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "
        
        period_ids = self.period_ids or False
        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)

        if not min_period:
            min_period = period_obj.search(cr, uid, [], order='date_start', limit=1)
        min_period = period_obj.browse(cr, uid, min_period[0])

        max_period = False
        if period_ids:
            max_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start Desc', limit=1)
        elif date_to:
            max_period = period_obj.search(cr, uid, [('date_start', '<=', date_to)], order='date_start Desc', limit=1)

        if not max_period:
            max_period = period_obj.search(cr, uid, [], order='date_start Desc', limit=1)
        max_period = period_obj.browse(cr, uid, max_period[0])
        date_start_min_period = min_period and min_period.date_start or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        val_period = []
        if date_start_min_period:
            val_period.append(('date_start', '>=', date_start_min_period))
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))
        qry_period_ids = period_obj.search(cr, uid, val_period)
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "
        journal_ids = self.journal_ids or False
        journal_qry = (journal_ids and ((len(journal_ids) == 1 and "AND l.journal_id = " + str(journal_ids[0]) + " ") or "AND l.journal_id IN " + str(tuple(journal_ids)) + " ")) or "AND l.journal_id IN (0) "


        cr.execute(
                "SELECT l.id as voucher_id " \
                "FROM account_voucher AS l " \
                "WHERE l.partner_id IS NOT NULL " \
                "AND l.state IN ('posted') " \
                + qry_type \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry \
                + journal_qry + \
                "order by l.date")
        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                inv = voucher_obj.browse(self.cr, self.uid, t['voucher_id'])
                res = {}
                lines_ids = []
                amount_all = 0.00
                amount_home_all = 0.00
                gain_loss_all = 0.00
                credit_inv_amt_credit = 0.00
                credit_inv_home_credit = 0.00
    
                alloc_inv_amt_debit = 0.00
                alloc_inv_home_debit = 0.00
    
                for lines in inv.line_dr_ids:
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
                for lines in inv.line_cr_ids:
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
                res['voucher_no'] = inv.number
                res['supp_ref'] = inv.partner_id and inv.partner_id.ref or ''
                res['supp_name'] = inv.partner_id and inv.partner_id.name or ''
                res['ex_glan'] = inv.company_id and inv.company_id.property_currency_gain_loss and  inv.company_id.property_currency_gain_loss.code or ''
                res['cheque_no'] = inv.cheque_no or ''
                res['curr_name'] = inv.journal_id and inv.journal_id.currency and inv.journal_id.currency.name or inv.company_id and inv.company_id.currency_id and inv.company_id.currency_id.name or ''
                res['cheque_date'] = inv.date or False
                res['bank_glan'] = inv.journal_id and inv.journal_id.property_bank_charges and inv.journal_id.property_bank_charges.code or ''
                ctx = {'date':inv.date}
                res['cur_exrate'] = self.pool.get('res.currency').browse(self.cr, self.uid, inv.journal_id and inv.journal_id.currency and inv.journal_id.currency.id or inv.company_id and inv.company_id.currency_id and inv.company_id.currency_id.id, context=ctx).rate or 0.00
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
                res['bank_draft'] = inv.bank_draft_no or ''
                res['bank_chrgs'] = inv.bank_charges_amount or 0.00
                res['bank_chrgs_home'] = inv.bank_charges_in_company_currency or 0.00
                self.footer_bank_charges_home += inv.bank_charges_in_company_currency or 0.00
                res['deposit_amt'] = inv.writeoff_amount or 0.00
                res['deposit_amt_home'] = inv.writeoff_amount_home or 0.00
                self.footer_deposit_home += inv.writeoff_amount_home or 0.00
                res['lines'] = lines_ids
                results.append(res)
#        print results
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %('', ''))
#        voucher_ids = account_voucher_obj.search(self.cr, self.uid, val_voucher, order='date ASC')
#
#
#        for voucher_id in account_voucher_obj.browse(self.cr, self.uid, voucher_ids):
#            res = {}
#            lines_ids = []
#            amount_all = 0.00
#            amount_home_all = 0.00
#            gain_loss_all = 0.00
#            credit_inv_amt_credit = 0.00
#            credit_inv_home_credit = 0.00
#
#            alloc_inv_amt_debit = 0.00
#            alloc_inv_home_debit = 0.00
#
#            for lines in voucher_id.line_dr_ids:
#                if lines.amount > 0:
#                    amount_all += lines.amount
#                    alloc_inv_amt_debit += lines.amount
#                    amount_home = lines.amount_home or 0.00
#                    amount_home_all += amount_home
#                    amount_inv_home = lines.amount_inv_home or 0.00
#                    alloc_inv_home_debit += amount_inv_home
#                    gain_loss = (amount_inv_home - amount_home) or 0.00
#                    gain_loss_all += gain_loss
#                    lines_ids.append({
#                        'voucher_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
#                        'date' : lines.move_line_id and lines.move_line_id.date or False,
#                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
#                        'alloc_inv_amt' : lines.amount or 0.00,
#                        'cheque_home' : lines.amount_home or 0.00,
#                        'alloc_inv_home': amount_inv_home,
#                        'gain_loss': gain_loss,
#                        })
#            for lines in voucher_id.line_cr_ids:
#                if lines.amount > 0:
#                    sign = -1
#                    amount_all -= lines.amount
#                    credit_inv_amt_credit += (sign * lines.amount)
#
#                    amount_home = lines.amount_home or 0.00
#                    amount_home_all -= amount_home
#                    amount_inv_home = lines.amount_inv_home or 0.00
#                    credit_inv_home_credit += (sign * amount_inv_home)
#                    gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
#                    gain_loss_all -= gain_loss
#                    lines_ids.append({
#                        'credit_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
#                        'date' : lines.move_line_id and lines.move_line_id.date or False,
#                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
#                        'credit_inv_amt' : (sign * lines.amount) or 0.00,
#                        'cheque_home' : (sign * lines.amount_home) or 0.00,
#                        'credit_inv_home': (sign * amount_inv_home),
#                        'gain_loss': gain_loss,
#                        })
#            self.payment_count += 1
#            res['voucher_no'] = voucher_id.number
#            res['supp_ref'] = voucher_id.partner_id and voucher_id.partner_id.ref or ''
#            res['supp_name'] = voucher_id.partner_id and voucher_id.partner_id.name or ''
#            res['ex_glan'] = voucher_id.company_id and voucher_id.company_id.property_currency_gain_loss and  voucher_id.company_id.property_currency_gain_loss.code or ''
#            res['cheque_no'] = voucher_id.cheque_no or ''
#            res['curr_name'] = voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.name or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.name or ''
#            res['cheque_date'] = voucher_id.date or False
#            res['bank_glan'] = voucher_id.journal_id and voucher_id.journal_id.property_bank_charges and voucher_id.journal_id.property_bank_charges.code or ''
#            ctx = {'date':voucher_id.date}
#            res['cur_exrate'] = self.pool.get('res.currency').browse(self.cr, self.uid, voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.id or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.id, context=ctx).rate or 0.00
#            res['cheq_amount'] = amount_all
#            res['cheq_amount_home'] = amount_home_all
#            self.footer_cheque_home += amount_home_all
#            res['gain_loss'] = gain_loss_all
#            self.footer_gain_loss_home += gain_loss_all
#            res['credit_inv_amt'] = credit_inv_amt_credit
#            res['credit_inv_home'] = credit_inv_home_credit
#            self.footer_credit_note_home += credit_inv_home_credit
#            res['alloc_inv_amt'] = alloc_inv_amt_debit
#            res['alloc_inv_home'] = alloc_inv_home_debit
#            self.footer_alloc_inv_home += alloc_inv_home_debit
#            res['bank_draft'] = voucher_id.bank_draft_no or ''
#            res['bank_chrgs'] = voucher_id.bank_charges_amount or 0.00
#            res['bank_chrgs_home'] = voucher_id.bank_charges_in_company_currency or 0.00
#            self.footer_bank_charges_home += voucher_id.bank_charges_in_company_currency or 0.00
#            res['deposit_amt'] = voucher_id.writeoff_amount or 0.00
#            res['deposit_amt_home'] = voucher_id.writeoff_amount_home or 0.00
#            self.footer_deposit_home += voucher_id.writeoff_amount_home or 0.00
#            res['lines'] = lines_ids
#            results.append(res)
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(results,'xxx'))
        return results


#    def __init__(self, cr, uid, name, context=None):
#        super(posted_payment_check_list, self).__init__(cr, uid, name, context=context)
#        self.payment_count = 0.00
#        self.footer_credit_note_home = 0.00
#        self.footer_cheque_home = 0.00
#        self.footer_alloc_inv_home = 0.00
#        self.footer_bank_charges_home = 0.00
#        self.footer_gain_loss_home = 0.00
#        self.footer_deposit_home = 0.00
#        self.localcontext.update({
#            'time': time,
#            'locale': locale,
#            'get_lines': self._get_lines,
#            'get_code_from': self._get_code_from,
#            'get_code_to': self._get_code_to,
#            'payment_count' : self._payment_count,
#            'footer_credit_note_home' : self._footer_credit_note_home,
#            'footer_cheque_home' : self._footer_cheque_home,
#            'footer_alloc_inv_home' : self._footer_alloc_inv_home,
#            'footer_bank_charges_home' : self._footer_bank_charges_home,
#            'footer_gain_loss_home' : self._footer_gain_loss_home,
#            'footer_deposit_home' : self._footer_deposit_home,
#            })
#
#    def _payment_count(self):
#        return self.payment_count
#
#    def _footer_credit_note_home(self):
#        return self.footer_credit_note_home
#
#    def _footer_cheque_home(self):
#        return self.footer_cheque_home
#
#    def _footer_alloc_inv_home(self):
#        return self.footer_alloc_inv_home
#
#    def _footer_bank_charges_home(self):
#        return self.footer_bank_charges_home
#
#    def _footer_gain_loss_home(self):
#        return self.footer_gain_loss_home
#
#    def _footer_deposit_home(self):
#        return self.footer_deposit_home
#
#    def _get_code_from(self):
#        if self.filter_selection == 'supp_code':
#            return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
#        elif self.filter_selection == 'supp_code_input':
#            return self.supplier_code_from or False
#        else:
#            return False
#
#    def _get_code_to(self):
#        if self.filter_selection == 'supp_code':
#            return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
#        elif self.filter_selection == 'supp_code_input':
#            return self.supplier_code_to or False
#        else:
#            return False
#
#    def _get_lines(self):
#        results = []
#        date_from = self.date_from
#        date_to =  self.date_to + ' ' + '23:59:59'
#        # partner
#        res_partner_obj = self.pool.get('res.partner')
#
#        if self.filter_selection == 'supp_code':
#            val_part = []
#            code_from = self.partner_code_from
#            code_to = self.partner_code_to
#            if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#                val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#            if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#                val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#            val_part.append(('supplier', '=', True))
#            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#        elif self.filter_selection == 'supp_code_input':
#            val_part = []
#            val_part.append(('supplier', '=', True))
#            supp_from = self.supplier_code_from
#            if supp_from:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_from) + "%' " \
#                                "order by ref limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '>=', qry['ref']))
#            supp_to = self.supplier_code_to
#            if supp_to:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_to) + "%' " \
#                                "order by ref desc limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '<=', qry['ref']))
#            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#
#        elif self.filter_selection == 'selection_code':
#            if self.partner_ids_selection:
#                part_ids = self.partner_ids_selection
#
#        val_voucher = []
#        account_voucher_obj = self.pool.get('account.voucher')
#        val_voucher.append(('date', '>=', date_from))
#        val_voucher.append(('date', '<=', date_to))
#        val_voucher.append(('type', '=', 'payment'))
#        val_voucher.append(('state', '=', 'posted'))
#        val_voucher.append(('partner_id', 'in', part_ids))
#        if self.journal_ids_selection:
#            val_voucher.append(('journal_id', 'in', self.journal_ids_selection))
#        voucher_ids = account_voucher_obj.search(self.cr, self.uid, val_voucher, order='date ASC')
#
#
#        for voucher_id in account_voucher_obj.browse(self.cr, self.uid, voucher_ids):
#            res = {}
#            lines_ids = []
#            amount_all = 0.00
#            amount_home_all = 0.00
#            gain_loss_all = 0.00
#            credit_inv_amt_credit = 0.00
#            credit_inv_home_credit = 0.00
#
#            alloc_inv_amt_debit = 0.00
#            alloc_inv_home_debit = 0.00
#
#            for lines in voucher_id.line_dr_ids:
#                if lines.amount > 0:
#                    amount_all += lines.amount
#                    alloc_inv_amt_debit += lines.amount
#                    amount_home = lines.amount_home or 0.00
#                    amount_home_all += amount_home
#                    amount_inv_home = lines.amount_inv_home or 0.00
#                    alloc_inv_home_debit += amount_inv_home
#                    gain_loss = (amount_inv_home - amount_home) or 0.00
#                    gain_loss_all += gain_loss
#                    lines_ids.append({
#                        'voucher_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
#                        'date' : lines.move_line_id and lines.move_line_id.date or False,
#                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
#                        'alloc_inv_amt' : lines.amount or 0.00,
#                        'cheque_home' : lines.amount_home or 0.00,
#                        'alloc_inv_home': amount_inv_home,
#                        'gain_loss': gain_loss,
#                        })
#            for lines in voucher_id.line_cr_ids:
#                if lines.amount > 0:
#                    sign = -1
#                    amount_all -= lines.amount
#                    credit_inv_amt_credit += (sign * lines.amount)
#
#                    amount_home = lines.amount_home or 0.00
#                    amount_home_all -= amount_home
#                    amount_inv_home = lines.amount_inv_home or 0.00
#                    credit_inv_home_credit += (sign * amount_inv_home)
#                    gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
#                    gain_loss_all -= gain_loss
#                    lines_ids.append({
#                        'credit_no' : lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '',
#                        'date' : lines.move_line_id and lines.move_line_id.date or False,
#                        'currency_date' : lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or False,
#                        'credit_inv_amt' : (sign * lines.amount) or 0.00,
#                        'cheque_home' : (sign * lines.amount_home) or 0.00,
#                        'credit_inv_home': (sign * amount_inv_home),
#                        'gain_loss': gain_loss,
#                        })
#            self.payment_count += 1
#            res['voucher_no'] = voucher_id.number
#            res['supp_ref'] = voucher_id.partner_id and voucher_id.partner_id.ref or ''
#            res['supp_name'] = voucher_id.partner_id and voucher_id.partner_id.name or ''
#            res['ex_glan'] = voucher_id.company_id and voucher_id.company_id.property_currency_gain_loss and  voucher_id.company_id.property_currency_gain_loss.code or ''
#            res['cheque_no'] = voucher_id.cheque_no or ''
#            res['curr_name'] = voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.name or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.name or ''
#            res['cheque_date'] = voucher_id.date or False
#            res['bank_glan'] = voucher_id.journal_id and voucher_id.journal_id.property_bank_charges and voucher_id.journal_id.property_bank_charges.code or ''
#            ctx = {'date':voucher_id.date}
#            res['cur_exrate'] = self.pool.get('res.currency').browse(self.cr, self.uid, voucher_id.journal_id and voucher_id.journal_id.currency and voucher_id.journal_id.currency.id or voucher_id.company_id and voucher_id.company_id.currency_id and voucher_id.company_id.currency_id.id, context=ctx).rate or 0.00
#            res['cheq_amount'] = amount_all
#            res['cheq_amount_home'] = amount_home_all
#            self.footer_cheque_home += amount_home_all
#            res['gain_loss'] = gain_loss_all
#            self.footer_gain_loss_home += gain_loss_all
#            res['credit_inv_amt'] = credit_inv_amt_credit
#            res['credit_inv_home'] = credit_inv_home_credit
#            self.footer_credit_note_home += credit_inv_home_credit
#            res['alloc_inv_amt'] = alloc_inv_amt_debit
#            res['alloc_inv_home'] = alloc_inv_home_debit
#            self.footer_alloc_inv_home += alloc_inv_home_debit
#            res['bank_draft'] = voucher_id.bank_draft_no or ''
#            res['bank_chrgs'] = voucher_id.bank_charges_amount or 0.00
#            res['bank_chrgs_home'] = voucher_id.bank_charges_in_company_currency or 0.00
#            self.footer_bank_charges_home += voucher_id.bank_charges_in_company_currency or 0.00
#            res['deposit_amt'] = voucher_id.writeoff_amount or 0.00
#            res['deposit_amt_home'] = voucher_id.writeoff_amount_home or 0.00
#            self.footer_deposit_home += voucher_id.writeoff_amount_home or 0.00
#            res['lines'] = lines_ids
#            results.append(res)
##        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(results,'xxx'))
#        return results 
    
report_sxw.report_sxw('report.max.payment.report_landscape', 'account.voucher',
    'addons/max_custom_report/account/report/max_payment_report.rml', parser=max_payment_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
