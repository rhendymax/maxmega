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

#from pickle import append
import time
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from report import report_sxw
import locale
from mx import DateTime as dt
locale.setlocale(locale.LC_ALL, '')
from tools import float_round, float_is_zero, float_compare

class max_aging_report(report_sxw.rml_parse):
    _name = 'max.aging.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        self.date_to = data['form']['date_to'] 
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

        self.report_type = data['form']['report_type']
        self.partner_ids = partner_ids

        #print self.period_ids
        return super(max_aging_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(max_aging_report, self).__init__(cr, uid, name, context=context)
        self.report_total = 0.00
        self.balance_by_cur = {}
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_header_title': self._get_header,
            'get_balance_by_cur': self._get_balance_by_cur,
            })

    def _get_balance_by_cur(self):
        result = []
        currency_obj    = self.pool.get('res.currency')
        for item in self.balance_by_cur.items():
            result.append({
                'cur_name' : currency_obj.browse(self.cr, self.uid, item[0]).name,
                'total_inv' : item[1]['inv_amt'],
                'total_home' : item[1]['home_amt'],
                'amt1' : item[1]['amt1'],
                'amt2' : item[1]['amt2'],
                'amt3' : item[1]['amt3'],
                'amt4' : item[1]['amt4'],
                'home_amt1' : item[1]['home_amt1'],
                'home_amt2' : item[1]['home_amt2'],
                'home_amt3' : item[1]['home_amt3'],
                'home_amt4' : item[1]['home_amt4'],
            })
        result = result and sorted(result, key=lambda val_res: val_res['cur_name']) or []
        return result

    def _get_header(self):
        if self.report_type == 'payable':
            header = 'Account Payable Aging Report'
        elif self.report_type == 'receivable':
            header = 'Account Receivable Aging Report'
        return header

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj     = self.pool.get('account.invoice')
        aml_obj     = self.pool.get('account.move.line')
        partner_obj     = self.pool.get('res.partner')
        partner_add_obj     = self.pool.get('res.partner.address')
        sale_payment_term_obj     = self.pool.get('sale.payment.term')
        
        
        results         = []
        results1        = []
        sign = -1
        type = self.report_type

        if type == 'payable':
            sign = -1
        elif type == 'receivable':
            sign = 1
        date_to = self.date_to
        partner_ids = self.partner_ids or False
        #print partner_ids

        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND aml.partner_id = " + str(partner_ids[0]) + " ") or "AND aml.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND aml.partner_id IN (0) "
        cr.execute(
                "select DISTINCT aml.partner_id " \
                "from account_move_line aml " \
                "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
                "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
                "left join res_users rs on rs.id = ai.user_id where aml.partner_id IS NOT NULL " \
                "and am.state IN ('draft', 'posted')  " \
                "and aa.type = '" + type + "' " \
                "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id), " \
                "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id), 0 " \
                ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                "And aml.date  <= '" +str(date_to) + "' "\
                + partner_qry)

#        cr.execute(
#                "SELECT DISTINCT l.partner_id " \
#                "FROM account_move_line AS l, account_account AS account, " \
#                " account_move AS am, account_journal as aj " \
#                "WHERE l.partner_id IS NOT NULL " \
#                    "AND l.account_id = account.id " \
#                    "AND am.id = l.move_id " \
#                    "and am.journal_id = aj.id " \
#                    "AND am.state IN ('draft', 'posted') " \
#                    "And account.type = 'payable' " \
#                    "And l.date  <= '" +str(date_to) + "' "\
#                    "And not (l.debit > 0 and l.is_depo = False and aj.type in ('cash', 'bank')) " \
#                    + partner_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name, ref, credit_limit " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()

        if qry:
            for s in qry:
                partner = partner_obj.browse(self.cr, self.uid, s['id'])
                cur_name = 'False'
                if type == 'payable':
                    cur_name = partner.property_product_pricelist_purchase.currency_id.name
                    cur_id = partner.property_product_pricelist_purchase.currency_id.id
                elif type == 'receivable':
                    cur_name = partner.property_product_pricelist.currency_id.name
                    cur_id = partner.property_product_pricelist.currency_id.id
                addr = partner_obj.address_get(cr, uid, [s['id']], ['delivery', 'invoice', 'contact'])
                addr = addr and addr['invoice'] and partner_add_obj.browse(self.cr, self.uid, addr['invoice']) or False

                cr.execute(
                        "select sp.id as picking_id, ai.sale_term_id as term_id, aml.id as aml_id, am.name as inv_name, aml.date as inv_date, ai.ref_no as inv_ref, rs.name as sales_name, aml.debit - aml.credit as home_amt, " \
                        "abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) THEN amount_currency ELSE aml.debit - aml.credit END) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) " \
                        "as inv_amt, " \
                        "abs(coalesce ( " \
                        "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                        "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), " \
                        "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid_home, " \
                        "abs(coalesce ( " \
                        "(select sum(CASE WHEN (aml4.currency_id is not null) and (aml4.cur_date is not null) THEN amount_currency ELSE aml4.debit - aml4.credit END) from account_move_line aml4 where aml4.reconcile_partial_id = aml.reconcile_partial_id and aml4.id != aml.id and aml4.date  <= '" +str(date_to) + "'), " \
                        "(select sum(CASE WHEN (aml5.currency_id is not null) and (aml5.cur_date is not null) THEN amount_currency ELSE aml5.debit - aml5.credit END) from account_move_line aml5 where aml5.reconcile_id = aml.reconcile_id and aml5.id != aml.id and aml5.date  <= '" +str(date_to) + "'), " \
                        "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid " \
                        "from account_move_line aml " \
                        "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
                        "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
                        "left join res_users rs on rs.id = ai.user_id left join stock_picking sp on ai.picking_id = sp.id where aml.partner_id IS NOT NULL " \
                        "and am.state IN ('draft', 'posted')  " \
                        "and aa.type = '" + type + "' " \
                        "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                        "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                        "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id), " \
                        "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id), 0 " \
                        ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                        "And aml.date  <= '" +str(date_to) + "' "\
                        "and aml.partner_id = " + str(s['id']) + " order by aml.date")
                qry3 = cr.dictfetchall()
                val = []
                total_amt1 = total_amt2= total_amt3 = total_amt4 = total_home_amt1 = total_home_amt2 = total_home_amt3 = total_home_amt4 = 0
                if qry3:
                    for t in qry3:
                        due_date = False
                        sale_term_id = t['term_id'] and sale_payment_term_obj.browse(self.cr, self.uid, t['term_id']) or False
                        daysremaining = 0
                        if sale_term_id:
                            partner_grace = partner and partner.grace or 0
                            sale_grace = sale_term_id.grace or 0
                            gracedays = partner_grace > 0 and partner_grace or sale_grace
                            termdays = sale_term_id.days
                            Date = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                            due_date = Date + timedelta(days=(termdays + gracedays))
                        #print EndDate
                        due_date = due_date and due_date.strftime('%Y-%m-%d') or False
                        d = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                        delta = datetime.strptime(date_to, '%Y-%m-%d') - d
                        daysremaining = delta.days
                        cust_po_no = ''
                        if type == 'receivable':
                                if t['picking_id']:
                                    cr.execute(
                                            "select so.client_order_ref as cust_po_no from sale_order_picking_rel sopr " \
                                            "left join sale_order so on sopr.order_id = so.id left join stock_picking sp on sopr.picking_id = sp.id " \
                                            "where sopr.picking_id = " + t['picking_id'] + " " \
                                            "order by so.date_order limit 1")
                                    qry4 = cr.dictfetchall()
                                    if qry4:
                                        for u in qry4:
                                            cust_po_no = u['cust_po_no']
                        remain_amt = (t['inv_amt'] * sign) - (t['paid'] * sign)
                        remain_home_amt = (t['home_amt'] * sign) - (t['paid_home'] * sign)
                        total_amt1 += daysremaining < 31 and remain_amt or 0.00
                        total_amt2 += (daysremaining > 30 and daysremaining < 61 and remain_amt) or 0.00
                        total_amt3 += (daysremaining > 60 and daysremaining < 91 and remain_amt) or 0.00
                        total_amt4 += daysremaining > 90 and remain_amt or 0.00
                        total_home_amt1 += daysremaining < 31 and remain_home_amt or 0.00
                        total_home_amt2 += (daysremaining > 30 and daysremaining < 61 and remain_home_amt) or 0.00
                        total_home_amt3 += (daysremaining > 60 and daysremaining < 91 and remain_home_amt) or 0.00
                        total_home_amt4 += daysremaining > 90 and remain_home_amt or 0.00
                        val.append({
                            'invoice_name' : t['inv_name'],
                            'sales_person': t['sales_name'],
                            'invoice_date' : t['inv_date'],
                            'due_date' : due_date,
                            'ref_no' : t['inv_ref'],
                            'cust_po_no' : cust_po_no,
                            'orig_amt' : (t['inv_amt'] * sign),
                            'home_orig_amt' : (t['home_amt'] * sign),
                            'paid_amt' : (t['paid'] * sign),
                            'home_paid_amt' : (t['paid_home'] * sign),
                            'amt1':  daysremaining < 31 and remain_amt or 0.00,
                            'home_amt1': daysremaining < 31 and remain_home_amt or 0.00,
                            'amt2': (daysremaining > 30 and daysremaining < 61 and remain_amt) or 0.00,
                            'home_amt2': (daysremaining > 30 and daysremaining < 61 and remain_home_amt) or 0.00,
                            'amt3': (daysremaining > 60 and daysremaining < 91 and remain_amt) or 0.00,
                            'home_amt3': (daysremaining > 60 and daysremaining < 91 and remain_home_amt) or 0.00,
                            'amt4': daysremaining > 90 and remain_amt or 0.00,
                            'home_amt4': daysremaining > 90 and remain_home_amt or 0.00,
                            })
                val = val and sorted(val, key=lambda val_res: val_res['invoice_date']) or []
                results1.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    'cur_name': cur_name,
                    'contact_phone' : addr and addr.phone,
                    'contact_person' : addr and addr.name,
                    'credit_limit' : s['credit_limit'],
                    'total_inv' : (total_amt1 + total_amt2 + total_amt3 + total_amt4),
                    'total_home' : (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4),
                    'total_amt1' : total_amt1,
                    'total_home_amt1' : total_home_amt1,
                    'total_amt2' : total_amt2,
                    'total_home_amt2' : total_home_amt2,
                    'total_amt3' : total_amt3,
                    'total_home_amt3' : total_home_amt3,
                    'total_amt4' : total_amt4,
                    'total_home_amt4' : total_home_amt4,
                    'val_ids': val,
                    })

                if cur_id not in self.balance_by_cur:
                    self.balance_by_cur.update({cur_id : {
                             'inv_amt' : (total_amt1 + total_amt2 + total_amt3 + total_amt4),
                             'home_amt' : (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4),
                             'amt1' : total_amt1,
                             'amt2' : total_amt2,
                             'amt3' : total_amt3,
                             'amt4' : total_amt4,
                             'home_amt1' : total_home_amt1,
                             'home_amt2' : total_home_amt2,
                             'home_amt3' : total_home_amt3,
                             'home_amt4' : total_home_amt4,
                             }
                            })
                else:
                    res_currency_grouping = self.balance_by_cur[cur_id].copy()
                    res_currency_grouping['inv_amt'] += (total_amt1 + total_amt2 + total_amt3 + total_amt4)
                    res_currency_grouping['home_amt'] += (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4)
                    res_currency_grouping['amt1'] += total_amt1
                    res_currency_grouping['amt2'] += total_amt2
                    res_currency_grouping['amt3'] += total_amt3
                    res_currency_grouping['amt4'] += total_amt4
                    res_currency_grouping['home_amt1'] += total_home_amt1
                    res_currency_grouping['home_amt2'] += total_home_amt2
                    res_currency_grouping['home_amt3'] += total_home_amt3
                    res_currency_grouping['home_amt4'] += total_home_amt4
                    self.balance_by_cur[cur_id] = res_currency_grouping
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['part_name']) or []
        return results1

report_sxw.report_sxw('report.max.aging.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/max_aging_report.rml', parser=max_aging_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
