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
from tools import float_round, float_is_zero, float_compare
locale.setlocale(locale.LC_ALL, '')

class sales_tax_report(report_sxw.rml_parse):
    _name = 'sales.tax.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        acc_tax_obj = self.pool.get('account.tax')
        period_obj = self.pool.get('account.period')
        self.fiscal_year = data['form']['fiscal_year']
        qry_supp = ''
        val_part = []
        val_tax = []
        qry_tax = ''
        partner_ids = False
        tax_ids = False

        data_search = data['form']['cust_search_vals']
        qry_supp = 'customer = True'
        val_part.append(('customer', '=', True))

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

        self.partner_ids = partner_ids

        val_tax.append(('type_tax_use', '=', 'sale'))
        qry_tax = 'type_tax_use = "sale"'
        tax_default_from = data['form']['tax_from'] and data['form']['tax_from'][0] or False
        tax_default_to = data['form']['tax_to'] and data['form']['tax_to'][0] or False
        tax_input_from = data['form']['tax_input_from'] or False
        tax_input_to = data['form']['tax_input_to'] or False
        
        if data['form']['tax_selection'] == 'all_vall':
            tax_ids = acc_tax_obj.search(self.cr, self.uid, val_tax, order='name ASC')
        if data['form']['tax_selection'] == 'def':
            data_found = False
            if tax_default_from and acc_tax_obj.browse(self.cr, self.uid, tax_default_from) and acc_tax_obj.browse(self.cr, self.uid, tax_default_from).name:
                data_found = True
                val_tax.append(('name', '>=', acc_tax_obj.browse(self.cr, self.uid, tax_default_from).name))
            if tax_default_to and acc_tax_obj.browse(self.cr, self.uid, tax_default_to) and acc_tax_obj.browse(self.cr, self.uid, tax_default_to).name:
                data_found = True
                val_tax.append(('name', '<=', acc_tax_obj.browse(self.cr, self.uid, tax_default_to).name))
            if data_found:
                tax_ids = acc_tax_obj.search(self.cr, self.uid, val_tax, order='ref ASC')
        elif data['form']['tax_selection'] == 'input':
            data_found = False
            if tax_input_from:
                self.cr.execute("select name " \
                                "from account_tax "\
                                "where " + qry_tax + " and " \
                                "ref ilike '" + str(tax_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_tax.append(('name', '>=', qry['name']))
            if tax_input_to:
                self.cr.execute("select name " \
                                "from account_tax "\
                                "where " + qry_tax + " and " \
                                "ref ilike '" + str(tax_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_tax.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                tax_ids = acc_tax_obj.search(self.cr, self.uid, val_tax, order='ref ASC')
        elif data['form']['tax_selection'] == 'selection':
            if data['form']['taxes_ids']:
                tax_ids = data['form']['taxes_ids']

        self.taxes_ids = tax_ids


        return super(sales_tax_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(sales_tax_report, self).__init__(cr, uid, name, context=context)
        self.taxable_home = 0.00
        self.tax_home = 0.00
        self.balance_by_cur = {}
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_taxable_home': self._get_taxable_home,
            'get_tax_home': self._get_tax_home,
            'get_lines': self._get_lines,
            'get_balance_by_cur': self._get_balance_by_cur,
            })

    def _get_balance_by_cur(self):

        result = []
        currency_obj    = self.pool.get('res.currency')
        for item in self.balance_by_cur.items():
            result.append({
                'cur_name' : currency_obj.browse(self.cr, self.uid, item[0]).name,
                'taxable_amt' : item[1]['taxable_amt'],
                'taxable_home' : item[1]['taxable_home'],
                'tax_amt' : item[1]['tax_amt'],
                'tax_home' : item[1]['tax_home'],
            })
        result = result and sorted(result, key=lambda val_res: val_res['cur_name']) or []
        return result

    def _get_taxable_home(self):
        return self.taxable_home

    def _get_tax_home(self):
        return self.tax_home

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        aml_obj     = self.pool.get('account.move.line')
        partner_obj     = self.pool.get('res.partner')
        res_currency_rate2_obj = self.pool.get("res.currency.rate2")
        res_user_obj = self.pool.get("res.users")
            
        results         = []
        fiscal_year = self.fiscal_year

        period_ids = self.period_ids or False
        date_from = self.date_from
        date_to = self.date_to

        partner_ids = self.partner_ids or False
        taxes_ids = self.taxes_ids or False

        res_user = res_user_obj.browse(cr, uid, uid)
        home_currency_id = res_user and res_user.company_id and res_user.company_id.currency_tax_id and res_user.company_id.currency_tax_id.id or False

        #print partner_ids
        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)
        if fiscal_year:
            if min_period:
                if fiscal_year[0] != period_obj.browse(cr, uid, min_period[0]).fiscalyear_id.id:
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
                if fiscal_year[0] != period_obj.browse(cr, uid, max_period[0]).fiscalyear_id.id:
                    max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
            else:
                max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
        if not max_period:
            max_period = period_obj.search(cr, uid, [], order='date_start Desc', limit=1)
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period[0]).date_start or False
        qry_period_ids = date_start_max_period and period_obj.search(cr, uid, [('date_start', '<=', date_start_max_period)]) or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND ai.partner_id = " + str(partner_ids[0]) + " ") or "AND ai.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND ai.partner_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND ai.period_id = " + str(qry_period_ids[0]) + " ") or "AND ai.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND ai.period_id IN (0) "
        tax_qry = (taxes_ids and ((len(taxes_ids) == 1 and "AND ac_t.id = " + str(taxes_ids[0]) + " ") or "AND ac_t.id IN " + str(tuple(taxes_ids)) + " ")) or "AND ac_t.id IN (0) "
        date_from_qry = date_from and "And ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And ai.date_invoice <= '" + str(date_to) + "' " or " "
        cr.execute(
                "SELECT DISTINCT ac_t.id as sale_tax_id " \
                "from account_invoice_tax ait " \
                "left join account_invoice ai on ait.invoice_id = ai.id " \
                "left join account_tax ac_t on ait.base_code_id in (ac_t.base_code_id, ac_t.ref_base_code_id) " \
                "WHERE ai.partner_id IS NOT NULL " \
                    "and ai.type in ('out_invoice', 'out_refund') " \
                    "AND ai.state IN ('open', 'paid') " \
                    + partner_qry \
                    + tax_qry \
                    + date_from_qry \
                    + date_to_qry \
                    + period_qry)
        sale_tax_ids_vals = []
        qry2 = cr.dictfetchall()

        if qry2:
            for r in qry2:
                sale_tax_ids_vals.append(r['sale_tax_id'])

#        print sale_tax_ids_vals
#        raise osv.except_osv(_('Error !'), _('test'))
        sale_tax_ids_vals_qry = (len(sale_tax_ids_vals) > 0 and ((len(sale_tax_ids_vals) == 1 and "where id = " +  str(sale_tax_ids_vals[0]) + " ") or "where id IN " +  str(tuple(sale_tax_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name " \
                "FROM account_tax " \
                      + sale_tax_ids_vals_qry \
                      + " order by name")
        qry = cr.dictfetchall()
        if qry:
#            print qry
#            raise osv.except_osv(_('Error !'), _('test'))
            for s in qry:
                inv_val = []
                credit_val = []
                inv_tax_amt = inv_taxable_amt = inv_taxable_home = inv_tax_home = cred_taxable_home = cred_tax_home = cred_taxable_amt = cred_tax_amt = 0

                cr.execute(
                        "select ai.number as inv_name, ai.date_invoice as inv_date, rp.name as part_name, rc.name as cur_name, ac_t.amount as tax_percent, ai.currency_id as inv_curr, ait.base as taxable_amt, ait.amount as tax_amt, ai.id as inv_id " \
                        "from account_invoice_tax ait " \
                        "left join account_invoice ai on ait.invoice_id = ai.id " \
                        "left join res_currency rc on ai.currency_id = rc.id " \
                        "left join res_partner rp on ai.partner_id = rp.id " \
                        "left join account_tax ac_t on ac_t.base_code_id = ait.base_code_id " \
                        "WHERE ai.partner_id IS NOT NULL " \
                            "and ai.type in ('out_invoice') " \
                            "AND ai.state IN ('open', 'paid') " \
                            + tax_qry \
                            + date_from_qry \
                            + date_to_qry \
                            + period_qry + \
                            "and ac_t.id = " + str(s['id']) + " " \
                            "order by ai.number, ai.date_invoice, ait.sequence")
                qry_inv = cr.dictfetchall()
                
                if qry_inv:
                    for inv in qry_inv:
                        rate = taxable_home = tax_home = home_rate = 0
                        cur_date = inv['inv_date'] or False

                        if home_currency_id and cur_date:
                            res_currency_home_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', home_currency_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_home_ids:
                                home_rate = res_currency_rate2_obj.browse(cr, uid, res_currency_home_ids[0]).rate
                        cur_id = inv['inv_curr'] or False


                        if cur_id and cur_date:
                            res_currency_rate_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_rate_ids:
                                rate = res_currency_rate2_obj.browse(cr, uid, res_currency_rate_ids[0]).rate
                        taxable = inv['taxable_amt'] or 0
                        tax = inv['tax_amt'] or 0
                        if rate > 0 and taxable > 0:
                            taxable_home = round(taxable / home_rate * rate, 2)
                        if rate > 0 and tax > 0:
                            tax_home = round(tax / home_rate * rate, 2)
                        inv_taxable_home += taxable_home
                        inv_tax_home += tax_home
                        inv_val.append({
                            'number': inv['inv_name'],
                            'date': inv['inv_date'],
                            'part_name': inv['part_name'],
                            'cur_name': inv['cur_name'],
                            'rate': rate,
                            'taxable_amt': inv['taxable_amt'],
                            'taxable_home': taxable_home,
                            'tax_percent': inv['tax_percent'] and inv['tax_percent'] * 100 or 0,
                            'tax_amt': inv['tax_amt'],
                            'tax_home' : tax_home,
                            })
                        if cur_id not in self.balance_by_cur:
                            self.balance_by_cur.update({cur_id : {
                                'taxable_amt' : inv['taxable_amt'],
                                'taxable_home' : taxable_home,
                                'tax_amt': inv['tax_amt'],
                                'tax_home' : tax_home,
                                }
                                })
                        else:
                            res_currency_grouping = self.balance_by_cur[cur_id].copy()
                            res_currency_grouping['taxable_amt'] += inv['taxable_amt']
                            res_currency_grouping['taxable_home'] += taxable_home
                            res_currency_grouping['tax_amt'] += inv['tax_amt']
                            res_currency_grouping['tax_home'] += tax_home
            #                    res_currency_grouping['sup_tax'] += (inv_sup_tax - cred_sup_tax)
                            self.balance_by_cur[cur_id] = res_currency_grouping
                cr.execute(
                    "select ai.number as inv_name, ai.date_invoice as inv_date, rp.name as part_name, rc.name as cur_name, ac_t.amount as tax_percent, ai.currency_id as inv_curr, ait.base as taxable_amt, ait.amount as tax_amt, ai.id as inv_id " \
                    "from account_invoice_tax ait " \
                    "left join account_invoice ai on ait.invoice_id = ai.id " \
                    "left join res_currency rc on ai.currency_id = rc.id " \
                    "left join res_partner rp on ai.partner_id = rp.id " \
                    "left join account_tax ac_t on ac_t.ref_base_code_id = ait.base_code_id " \
                    "WHERE ai.partner_id IS NOT NULL " \
                        "and ai.type in ('out_refund') " \
                        "AND ai.state IN ('open', 'paid') " \
                        + tax_qry \
                        + date_from_qry \
                        + date_to_qry \
                        + period_qry + \
                        "and ac_t.id = " + str(s['id']) + " " \
                        "order by ai.number, ai.date_invoice, ait.sequence")
                qry_cred = cr.dictfetchall()
                if qry_cred:
                    for cred in qry_cred:
                        rate = taxable_home = tax_home = home_rate = 0
                        cur_date = cred['inv_date'] or False

                        if home_currency_id and cur_date:
                            res_currency_home_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', home_currency_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_home_ids:
                                home_rate = res_currency_rate2_obj.browse(cr, uid, res_currency_home_ids[0]).rate
                        cur_id = cred['inv_curr'] or False

                        if cur_id and cur_date:
                            res_currency_rate_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_rate_ids:
                                rate = res_currency_rate2_obj.browse(cr, uid, res_currency_rate_ids[0]).rate
                        taxable = cred['taxable_amt'] or 0
                        tax = cred['tax_amt'] or 0
                        if rate > 0 and taxable > 0:
                            taxable_home = round(taxable / home_rate * rate, 2)
                        if rate > 0 and tax > 0:
                            tax_home = round(tax / home_rate * rate, 2)
                        cred_taxable_home += taxable_home
                        cred_tax_home += tax_home
                        credit_val.append({
                            'number': cred['inv_name'],
                            'date': cred['inv_date'],
                            'part_name': cred['part_name'],
                            'cur_name': cred['cur_name'],
                            'rate': rate,
                            'taxable_amt': cred['taxable_amt'],
                            'taxable_home': taxable_home,
                            'tax_percent': cred['tax_percent'] and cred['tax_percent'] * 100 or 0,
                            'tax_amt': cred['tax_amt'],
                            'tax_home' : tax_home,
                            })
                        if cur_id not in self.balance_by_cur:
                            self.balance_by_cur.update({cur_id : {
                                'taxable_amt' : inv['taxable_amt'] * -1,
                                'taxable_home' : taxable_home * -1,
                                'tax_amt': inv['tax_amt'] * -1,
                                'tax_home' : tax_home * -1,
                                }
                                })
                        else:
                            res_currency_grouping = self.balance_by_cur[cur_id].copy()
                            res_currency_grouping['taxable_amt'] -= inv['taxable_amt']
                            res_currency_grouping['taxable_home'] -= taxable_home
                            res_currency_grouping['tax_amt'] -= inv['tax_amt']
                            res_currency_grouping['tax_home'] -= tax_home
                            self.balance_by_cur[cur_id] = res_currency_grouping
                self.taxable_home += (inv_taxable_home - cred_taxable_home)
                self.tax_home += (inv_tax_home - cred_tax_home)
                results.append({
                    'tax_name' : s['name'],
                    'invoice_vals' : inv_val,
                    'credit_vals' : credit_val,
                    'inv_taxable_home' : inv_taxable_home,
                    'inv_tax_home' : inv_tax_home,
                    'cred_taxable_home' : cred_taxable_home,
                    'cred_tax_home' : cred_tax_home,
                    'total_taxable_home' : inv_taxable_home - cred_taxable_home,
                    'total_tax_home' : inv_tax_home - cred_tax_home,
                    })
                
        results = results and sorted(results, key=lambda val_res: val_res['tax_name']) or []

        return results

#    def _get_period_from(self):
#        period_from = self.period_from and self.pool.get('account.period').browse(self.cr, self.uid,self.period_from).name or False
#        self.cr.execute("SELECT l.id as period_id, l.name as period " \
#               " FROM account_period l " \
#               " GROUP BY l.id, l.name, l.date_start, l.special order by l.date_start, l.special desc")
#        period_id_search = self.cr.dictfetchone()
#        cr_period_from = period_from or period_id_search and period_id_search['period']
#        return cr_period_from
#    
#    def _get_period_to(self):
#        period_to = self.period_to and self.pool.get('account.period').browse(self.cr, self.uid, self.period_to).name or False
#        self.cr.execute("SELECT l.id as period_id, l.name as period " \
#               " FROM account_period l " \
#               " GROUP BY l.id, l.name, l.date_start, l.special order by l.date_start desc, l.special desc")
#        period_id_search = self.cr.dictfetchone()
#        cr_period_to = period_to or period_id_search and period_id_search['period']
#        return cr_period_to
#
#    def _get_tax_from(self):
#        if self.field_selection == 'normal':
#            return self.sale_tax_from and self.pool.get('account.tax').browse(self.cr, self.uid,self.sale_tax_from).name or False
#        elif self.field_selection == 'input':
#            return self.sale_tax_input_from or False
#        else:
#            return False
#
#    def _get_tax_to(self):
#        if self.field_selection == 'normal':
#            return self.sale_tax_to and self.pool.get('account.tax').browse(self.cr, self.uid,self.sale_tax_to).name or False
#        elif self.field_selection == 'input':
#            return self.sale_tax_input_to or False
#        else:
#            return False
#
#    def map_tax(self, fposition_id, taxes):
#        if not taxes:
#            return []
#        if not fposition_id:
#            return taxes
#        result = []
#
#        for tax in fposition_id.tax_ids:
#            if tax.tax_src_id.id == taxes:
#                if tax.tax_dest_id:
#                    return tax.tax_dest_id.id
#        return taxes
#
#    def _get_lines(self, type):
##Valiable
#        results = []
#        fpos_obj = self.pool.get('account.fiscal.position')
#        partner_obj = self.pool.get('res.partner')
#        tax_obj = self.pool.get('account.tax')
#        cr = self.cr
#        uid = self.uid
#        
##Period
#        val_period = []
#        period_from = self.period_from
#        period_to = self.period_to
#        account_period_obj = self.pool.get('account.period')
#
#        if period_from and account_period_obj.browse(self.cr, self.uid, period_from) and account_period_obj.browse(self.cr, self.uid, period_from).date_start:
#            val_period.append(('date_start', '>=', account_period_obj.browse(self.cr, self.uid, period_from).date_start))
#        if period_to and account_period_obj.browse(self.cr, self.uid, period_to) and account_period_obj.browse(self.cr, self.uid, period_to).date_start:
#            val_period.append(('date_start', '<=', account_period_obj.browse(self.cr, self.uid, period_to).date_start))
#        period_ids = account_period_obj.search(self.cr, self.uid, val_period, order='date_start, special desc')
#        val_ss = ''
#        if period_ids:
#            for ss in period_ids:
#                if val_ss == '':
#                    val_ss += str(ss)
#                else:
#                    val_ss += (', ' + str(ss))
#
##sale_tax
#        if self.field_selection == 'normal':
#            val_tax = []
#            tax_from = self.sale_tax_from
#            tax_to = self.sale_tax_to
#            if tax_from and tax_obj.browse(self.cr, self.uid, tax_from) and tax_obj.browse(self.cr, self.uid, tax_from).name:
#                val_tax.append(('name', '>=', tax_obj.browse(self.cr, self.uid, tax_from).name))
#            if tax_to and tax_obj.browse(self.cr, self.uid, tax_to) and tax_obj.browse(self.cr, self.uid, tax_to).name:
#                val_tax.append(('name', '<=', tax_obj.browse(self.cr, self.uid, tax_to).name))
#            val_tax.append(('type_tax_use', '=', 'sale'))
#            tax_ids = tax_obj.search(self.cr, self.uid, val_tax, order='name ASC')
#
#        elif self.field_selection == 'input':
#            val_tax = []
#            val_tax.append(('type_tax_use', '=', 'sale'))
#            tax_from = self.sale_tax_input_from
#            if tax_from:
#                self.cr.execute("select name " \
#                                "from account_tax "\
#                                "where type_tax_use = 'sale' and " \
#                                "ref ilike '" + str(tax_from) + "%' " \
#                                "order by name limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_tax.append(('name', '>=', qry['name']))
#            tax_to = self.sale_tax_input_to
#            if tax_to:
#                self.cr.execute("select name " \
#                                "from account_tax "\
#                                "where type_tax_use = 'sale' and " \
#                                "ref ilike '" + str(tax_to) + "%' " \
#                                "order by name desc limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_tax.append(('name', '<=', qry['name']))
#            tax_ids = tax_obj.search(self.cr, self.uid, val_tax, order='ref ASC')
#
#        elif self.field_selection == 'selection':
#            if self.taxes_ids:
#                tax_ids = self.taxes_ids
#
###State
##        state = self.state
##        state_query = ''
##        if state:
##            state_query = "('" + str(state) + "')"
##        else:
##            state_query = "('open', 'paid')"
##
###Start
#        self.cr.execute("select ai.number as number, " \
#                        "rcom.tax_id as default_tax_id, " \
#                        "rp.id as part_id, " \
#                        "rp.name as part_name, " \
#                        "rc.name as curr_name, " \
#                        "ai.fiscal_position as fiscal_pos, " \
#                        "ai.amount_untaxed as untax, " \
#                        "ai.amount_untaxed_home as untax_home, " \
#                        "ai.amount_tax as tax, " \
#                        "ai.amount_tax_home as tax_home, " \
#                        "ai.date_invoice as date, " \
#                        "(select rate from res_currency_rate where currency_id = ai.currency_id and name < ai.cur_date order by name desc limit 1)  as rate " \
#                        "from account_invoice ai " \
#                        "left join res_company rcom on ai.company_id = rcom.id " \
#                        "left join res_partner rp on ai.partner_id = rp.id " \
#                        "left join res_currency rc on ai.currency_id = rc.id " \
#                        "WHERE ai.period_id in (" + val_ss + ") " \
#                        "and ai.state in ('open', 'paid') "\
#                        "and ai.type = '" + type + "' "\
#                        "order by ai.date_invoice")
#        qry = self.cr.dictfetchall()
#        if qry:
#            for r in qry:
#                res = {}
##                fpos = r['part_id'] and partner_obj.browse(cr, uid, r['part_id'], context=None) and \
##                    partner_obj.browse(cr, uid, r['part_id'], context=None).property_account_position or False
#                fpos = r['fiscal_pos'] and fpos_obj.browse(cr, uid, r['fiscal_pos'], context=None) or False
#                tax_id = self.map_tax(fpos, r['default_tax_id'])
#                
#                if tax_id in tax_ids:
#                    res['number'] = r['number']
#                    res['part_name'] = r['part_name']
#                    res['curr_name'] = r['curr_name']
#                    res['untax'] = r['untax']
#                    res['untax_home'] = r['untax_home']
#                    res['tax_percent'] = float_round((tax_obj.browse(self.cr, self.uid, tax_id) and tax_obj.browse(self.cr, self.uid, tax_id).amount or 0.00) * 100, 2)
#                    res['tax'] = r['tax']
#                    res['tax_home'] = r['tax_home']
#                    res['date'] = r['date']
#                    res['rate'] = r['rate']
#                    results.append(res)
#        return results

report_sxw.report_sxw('report.sales.tax.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/sales_tax_report.rml', parser=sales_tax_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
