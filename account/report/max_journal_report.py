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

class max_journal_report(report_sxw.rml_parse):
    _name = 'max.journal.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        number = 0
        val_part = []

        report_type = data['form']['report_type']
        partner_ids = False
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

        self.report_type = data['form']['report_type']
        self.partner_ids = partner_ids
        #print self.period_ids
        
        return super(max_journal_report, self).set_context(objects, data, new_ids, report_type=report_type)



#    def __init__(self, cr, uid, name, context=None):
#        super(purchase_journal_by_supplier_report, self).__init__(cr, uid, name, context=context)
#        
#        self.pre_tax_home = 0.00
#        self.sales_tax_home = 0.00
#        self.after_tax_home = 0.00
#        self.localcontext.update({
#            'time': time,
#            'locale': locale,
#            'get_lines': self._get_lines,
#            'get_total_invoice': self._get_total_invoice,
#            'get_total_refund': self._get_total_refund,
#            'get_code_from': self._get_code_from,
#            'get_code_to': self._get_code_to,
#            'get_inv_from': self._get_inv_from,
#            'get_inv_to': self._get_inv_to,
#            'total_pre_tax_home' : self._total_pre_tax_home,
#            'total_sales_tax_home' : self._total_sales_tax_home,
#            'total_after_tax_home' : self._total_after_tax_home,
#            })

    def __init__(self, cr, uid, name, context=None):
        super(max_journal_report, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_header_title': self._get_header,
            })

    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Purchase Journal Report'
        elif self.report_type == 'receivable':
            header = 'Sale Journal Report'
        return header

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        aml_obj     = self.pool.get('account.move.line')
        partner_obj     = self.pool.get('res.partner')

        results         = []
        results1        = []
        type = self.report_type
        qry_type = ''
        if type == 'payable':
            qry_type = "and l.type in ('in_invoice', 'in_refund') "
        elif type == 'receivable':
            qry_type = "and l.type in ('out_invoice', 'out_refund') "
        period_ids = self.period_ids or False
        date_from = self.date_from
        date_to = self.date_to
        partner_ids = self.partner_ids or False
        #print partner_ids
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
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        qry_period_ids = date_start_max_period and period_obj.search(cr, uid, [('date_start', '<=', date_start_max_period)]) or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "

        date_from_qry = date_from and "And l.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date_invoice <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_invoice AS l " \
                "WHERE l.partner_id IS NOT NULL " \
                "AND l.state IN ('open', 'paid') " \
                + qry_type \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "
        period_qry2 = (qry_period_ids and ((len(qry_period_ids) == 1 and "and aml.period_id = " + str(qry_period_ids[0]) + " ") or "and aml.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND and aml.period_id IN (0) "
        date_from_qry2 = date_from and "And aml.date >= '" + str(date_from) + "' " or " "
        date_to_qry2 = date_to and "And aml.date <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT id, name, ref " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                results1.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    })
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['part_name']) or []

        return results1
    
    
#    def _total_pre_tax_home(self):
#        return self.pre_tax_home
#
#    def _total_sales_tax_home(self):
#        return self.sales_tax_home
#
#    def _total_after_tax_home(self):
#        return self.after_tax_home
#
#    def _get_code_from(self):
#        return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
#    
#    def _get_code_to(self):
#        return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
#    
#    def _get_inv_from(self):
#        return self.inv_from and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_from).number or False
#    
#    def _get_inv_to(self):
#        return self.inv_to and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_to).number or False
#
#    def _get_total_invoice(self):
#        results = []
#        val_part = []
#        val_inv = []
#        date_from = self.date_from
#        date_to =  self.date_to + ' ' + '23:59:59'
#        code_from = self.partner_code_from
#        code_to = self.partner_code_to
#        inv_from = self.inv_from
#        inv_to = self.inv_to
#        account_invoice_obj = self.pool.get('account.invoice')
#        res_partner_obj = self.pool.get('res.partner')
#        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
#            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
#        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
#            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
#
#        curr_ids = []
#        curr_ids_name = {}
#        curr_ids_amount_untaxed = {}
#        curr_ids_amount_amount_taxed = {}
#        curr_ids_amount_amount_total = {}
#        curr_ids_amount_untaxed_home = {}
#        curr_ids_amount_amount_taxed_home = {}
#        curr_ids_amount_amount_total_home = {}
#        val_part.append(('supplier', '=', True))
#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#        if part_ids:
#            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
#            val_inv.append(('date_invoice', '>=', date_from))
#            val_inv.append(('date_invoice', '<=', date_to))
#            val_inv.append(('type', 'in', ['in_invoice']))
#            val_inv.append(('state', 'in', ['open','paid']))
#            for part in partner_ids:
#                val_inv2 = list(val_inv)
#                val_inv2.append(('partner_id', '=', part.id))
#                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
#                if inv_ids:
#                    line_ids = []
#                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
#                        if inv_id.currency_id.id not in curr_ids:
#                            curr_ids.append(inv_id.currency_id.id)
#                            curr_ids_name[inv_id.currency_id.id] = inv_id.currency_id.name
#                            curr_ids_amount_untaxed[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_taxed[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_total[inv_id.currency_id.id] = 0
#                            curr_ids_amount_untaxed_home[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_total_home[inv_id.currency_id.id] = 0
#                        #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
#                        curr_ids_amount_untaxed[inv_id.currency_id.id] += inv_id.amount_untaxed
#                        curr_ids_amount_amount_taxed[inv_id.currency_id.id] += inv_id.amount_tax
#                        curr_ids_amount_amount_total[inv_id.currency_id.id] += inv_id.amount_total
#                        curr_ids_amount_untaxed_home[inv_id.currency_id.id] += inv_id.amount_untaxed_home
#                        curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] += inv_id.amount_tax_home
#                        curr_ids_amount_amount_total_home[inv_id.currency_id.id] += inv_id.amount_total_home
#            if curr_ids:
#                for curr in curr_ids:
#                    res = {}
#                    res['cur_name'] = curr_ids_name[curr]
#                    res['amount_untaxed'] = curr_ids_amount_untaxed[curr]
#                    res['amount_taxed'] = curr_ids_amount_amount_taxed[curr]
#                    res['amount_total'] = curr_ids_amount_amount_total[curr]
#                    res['amount_untaxed_home'] = curr_ids_amount_untaxed_home[curr]
#                    res['amount_taxed_home'] = curr_ids_amount_amount_taxed_home[curr]
#                    res['amount_total_home'] = curr_ids_amount_amount_total_home[curr]
#                    self.pre_tax_home += (curr_ids_amount_untaxed_home[curr] or 0)
#                    self.sales_tax_home += (curr_ids_amount_amount_taxed_home[curr] or 0)
#                    self.after_tax_home += (curr_ids_amount_amount_total_home[curr] or 0)
#                    results.append(res)
#        return results
#
#    def _get_total_refund(self):
#        results = []
#        val_part = []
#        val_inv = []
#        date_from = self.date_from
#        date_to =  self.date_to + ' ' + '23:59:59'
#        code_from = self.partner_code_from
#        code_to = self.partner_code_to
#        inv_from = self.inv_from
#        inv_to = self.inv_to
#        account_invoice_obj = self.pool.get('account.invoice')
#        res_partner_obj = self.pool.get('res.partner')
#        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
#            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
#        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
#            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
#
#        curr_ids = []
#        curr_ids_name = {}
#        curr_ids_amount_untaxed = {}
#        curr_ids_amount_amount_taxed = {}
#        curr_ids_amount_amount_total = {}
#        curr_ids_amount_untaxed_home = {}
#        curr_ids_amount_amount_taxed_home = {}
#        curr_ids_amount_amount_total_home = {}
#        val_part.append(('supplier', '=', True))
#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#        if part_ids:
#            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
#            val_inv.append(('date_invoice', '>=', date_from))
#            val_inv.append(('date_invoice', '<=', date_to))
#            val_inv.append(('type', 'in', ['in_refund']))
#            val_inv.append(('state', 'in', ['open','paid']))
#            for part in partner_ids:
#                val_inv2 = list(val_inv)
#                val_inv2.append(('partner_id', '=', part.id))
#                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
#                if inv_ids:
#                    line_ids = []
#                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
#                        if inv_id.currency_id.id not in curr_ids:
#                            curr_ids.append(inv_id.currency_id.id)
#                            curr_ids_name[inv_id.currency_id.id] = inv_id.currency_id.name
#                            curr_ids_amount_untaxed[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_taxed[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_total[inv_id.currency_id.id] = 0
#                            curr_ids_amount_untaxed_home[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] = 0
#                            curr_ids_amount_amount_total_home[inv_id.currency_id.id] = 0
#                        #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
#                        curr_ids_amount_untaxed[inv_id.currency_id.id] += inv_id.amount_untaxed
#                        curr_ids_amount_amount_taxed[inv_id.currency_id.id] += inv_id.amount_tax
#                        curr_ids_amount_amount_total[inv_id.currency_id.id] += inv_id.amount_total
#                        curr_ids_amount_untaxed_home[inv_id.currency_id.id] += inv_id.amount_untaxed_home
#                        curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] += inv_id.amount_tax_home
#                        curr_ids_amount_amount_total_home[inv_id.currency_id.id] += inv_id.amount_total_home
#            if curr_ids:
#                for curr in curr_ids:
#                    res = {}
#                    res['cur_name'] = curr_ids_name[curr]
#                    res['amount_untaxed'] = curr_ids_amount_untaxed[curr]
#                    res['amount_taxed'] = curr_ids_amount_amount_taxed[curr]
#                    res['amount_total'] = curr_ids_amount_amount_total[curr]
#                    res['amount_untaxed_home'] = curr_ids_amount_untaxed_home[curr]
#                    res['amount_taxed_home'] = curr_ids_amount_amount_taxed_home[curr]
#                    res['amount_total_home'] = curr_ids_amount_amount_total_home[curr]
#                    self.pre_tax_home -= (curr_ids_amount_untaxed_home[curr] or 0)
#                    self.sales_tax_home -= (curr_ids_amount_amount_taxed_home[curr] or 0)
#                    self.after_tax_home -= (curr_ids_amount_amount_total_home[curr] or 0)
#                    results.append(res)
#         #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
#        return results
#
#    def _get_lines(self):
#        results = []
#        val_part = []
#        val_inv = []
#        date_from = self.date_from
#        date_to =  self.date_to + ' ' + '23:59:59'
#        code_from = self.partner_code_from
#        code_to = self.partner_code_to
#        inv_from = self.inv_from
#        inv_to = self.inv_to
#        account_invoice_obj = self.pool.get('account.invoice')
#        res_partner_obj = self.pool.get('res.partner')
#
#        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
#            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
#        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
#            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
#        val_part.append(('supplier', '=', True))
#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#        if part_ids:
#            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
#            val_inv.append(('date_invoice', '>=', date_from))
#            val_inv.append(('date_invoice', '<=', date_to))
#            val_inv.append(('type', 'in', ['in_invoice','in_refund']))
#            val_inv.append(('state', 'in', ['open','paid']))
#            for part in partner_ids:
#                val_inv2 = list(val_inv)
#                val_inv2.append(('partner_id', '=', part.id))
#                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
#                if inv_ids:
#                    line_ids = []
#                    res = {}
#                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
#                        line_ids.append(inv_id)
#                    res['ref'] = part.ref
#                    res['name'] = part.name
#                    res['lines'] = line_ids
#                    results.append(res)
#        return results

report_sxw.report_sxw('report.max.journal.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/max_journal_report.rml', parser=max_journal_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
