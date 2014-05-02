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

class sales_journal_by_customer_report(report_sxw.rml_parse):
    _name = 'sales.journal.by.customer.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.partner_code_from = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
        self.partner_code_to = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
        self.inv_from = data['form']['inv_from'] and data['form']['inv_from'][0] or False
        self.inv_to = data['form']['inv_to'] and data['form']['inv_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(sales_journal_by_customer_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(sales_journal_by_customer_report, self).__init__(cr, uid, name, context=context)
        
        self.pre_tax_home = 0.00
        self.sales_tax_home = 0.00
        self.after_tax_home = 0.00
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_total_invoice': self._get_total_invoice,
            'get_total_refund': self._get_total_refund,
            'get_code_from': self._get_code_from,
            'get_code_to': self._get_code_to,
            'get_inv_from': self._get_inv_from,
            'get_inv_to': self._get_inv_to,
            'total_pre_tax_home' : self._total_pre_tax_home,
            'total_sales_tax_home' : self._total_sales_tax_home,
            'total_after_tax_home' : self._total_after_tax_home,
            })

    def _total_pre_tax_home(self):
        return self.pre_tax_home

    def _total_sales_tax_home(self):
        return self.sales_tax_home

    def _total_after_tax_home(self):
        return self.after_tax_home

    def _get_code_from(self):
        return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
    
    def _get_code_to(self):
        return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
    
    def _get_inv_from(self):
        return self.inv_from and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_from).number or False
    
    def _get_inv_to(self):
        return self.inv_to and self.pool.get('account.invoice').browse(self.cr, self.uid, self.inv_to).number or False

    def _get_total_invoice(self):
        results = []
        val_part = []
        val_inv = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        code_from = self.partner_code_from
        code_to = self.partner_code_to
        inv_from = self.inv_from
        inv_to = self.inv_to
        account_invoice_obj = self.pool.get('account.invoice')
        res_partner_obj = self.pool.get('res.partner')
        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))

        curr_ids = []
        curr_ids_name = {}
        curr_ids_amount_untaxed = {}
        curr_ids_amount_amount_taxed = {}
        curr_ids_amount_amount_total = {}
        curr_ids_amount_untaxed_home = {}
        curr_ids_amount_amount_taxed_home = {}
        curr_ids_amount_amount_total_home = {}
        val_part.append(('customer', '=', True))
        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
        if part_ids:
            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
            val_inv.append(('date_invoice', '>=', date_from))
            val_inv.append(('date_invoice', '<=', date_to))
            val_inv.append(('type', 'in', ['out_invoice']))
            val_inv.append(('state', 'in', ['open','paid']))
            for part in partner_ids:
                val_inv2 = list(val_inv)
                val_inv2.append(('partner_id', '=', part.id))
                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
                if inv_ids:
                    line_ids = []
                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
                        if inv_id.currency_id.id not in curr_ids:
                            curr_ids.append(inv_id.currency_id.id)
                            curr_ids_name[inv_id.currency_id.id] = inv_id.currency_id.name
                            curr_ids_amount_untaxed[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_taxed[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_total[inv_id.currency_id.id] = 0
                            curr_ids_amount_untaxed_home[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_total_home[inv_id.currency_id.id] = 0
                        #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
                        curr_ids_amount_untaxed[inv_id.currency_id.id] += inv_id.amount_untaxed
                        curr_ids_amount_amount_taxed[inv_id.currency_id.id] += inv_id.amount_tax
                        curr_ids_amount_amount_total[inv_id.currency_id.id] += inv_id.amount_total
                        curr_ids_amount_untaxed_home[inv_id.currency_id.id] += inv_id.amount_untaxed_home
                        curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] += inv_id.amount_tax_home
                        curr_ids_amount_amount_total_home[inv_id.currency_id.id] += inv_id.amount_total_home
            if curr_ids:
                for curr in curr_ids:
                    res = {}
                    res['cur_name'] = curr_ids_name[curr]
                    res['amount_untaxed'] = curr_ids_amount_untaxed[curr]
                    res['amount_taxed'] = curr_ids_amount_amount_taxed[curr]
                    res['amount_total'] = curr_ids_amount_amount_total[curr]
                    res['amount_untaxed_home'] = curr_ids_amount_untaxed_home[curr]
                    res['amount_taxed_home'] = curr_ids_amount_amount_taxed_home[curr]
                    res['amount_total_home'] = curr_ids_amount_amount_total_home[curr]
                    self.pre_tax_home += (curr_ids_amount_untaxed_home[curr] or 0)
                    self.sales_tax_home += (curr_ids_amount_amount_taxed_home[curr] or 0)
                    self.after_tax_home += (curr_ids_amount_amount_total_home[curr] or 0)
                    results.append(res)
        return results

    def _get_total_refund(self):
        results = []
        val_part = []
        val_inv = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        code_from = self.partner_code_from
        code_to = self.partner_code_to
        inv_from = self.inv_from
        inv_to = self.inv_to
        account_invoice_obj = self.pool.get('account.invoice')
        res_partner_obj = self.pool.get('res.partner')
        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))

        curr_ids = []
        curr_ids_name = {}
        curr_ids_amount_untaxed = {}
        curr_ids_amount_amount_taxed = {}
        curr_ids_amount_amount_total = {}
        curr_ids_amount_untaxed_home = {}
        curr_ids_amount_amount_taxed_home = {}
        curr_ids_amount_amount_total_home = {}
        val_part.append(('customer', '=', True))
        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
        if part_ids:
            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
            val_inv.append(('date_invoice', '>=', date_from))
            val_inv.append(('date_invoice', '<=', date_to))
            val_inv.append(('type', 'in', ['out_refund']))
            val_inv.append(('state', 'in', ['open','paid']))
            for part in partner_ids:
                val_inv2 = list(val_inv)
                val_inv2.append(('partner_id', '=', part.id))
                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
                if inv_ids:
                    line_ids = []
                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
                        if inv_id.currency_id.id not in curr_ids:
                            curr_ids.append(inv_id.currency_id.id)
                            curr_ids_name[inv_id.currency_id.id] = inv_id.currency_id.name
                            curr_ids_amount_untaxed[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_taxed[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_total[inv_id.currency_id.id] = 0
                            curr_ids_amount_untaxed_home[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] = 0
                            curr_ids_amount_amount_total_home[inv_id.currency_id.id] = 0
                        #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
                        curr_ids_amount_untaxed[inv_id.currency_id.id] += inv_id.amount_untaxed
                        curr_ids_amount_amount_taxed[inv_id.currency_id.id] += inv_id.amount_tax
                        curr_ids_amount_amount_total[inv_id.currency_id.id] += inv_id.amount_total
                        curr_ids_amount_untaxed_home[inv_id.currency_id.id] += inv_id.amount_untaxed_home
                        curr_ids_amount_amount_taxed_home[inv_id.currency_id.id] += inv_id.amount_tax_home
                        curr_ids_amount_amount_total_home[inv_id.currency_id.id] += inv_id.amount_total_home
            if curr_ids:
                for curr in curr_ids:
                    res = {}
                    res['cur_name'] = curr_ids_name[curr]
                    res['amount_untaxed'] = curr_ids_amount_untaxed[curr]
                    res['amount_taxed'] = curr_ids_amount_amount_taxed[curr]
                    res['amount_total'] = curr_ids_amount_amount_total[curr]
                    res['amount_untaxed_home'] = curr_ids_amount_untaxed_home[curr]
                    res['amount_taxed_home'] = curr_ids_amount_amount_taxed_home[curr]
                    res['amount_total_home'] = curr_ids_amount_amount_total_home[curr]
                    self.pre_tax_home -= (curr_ids_amount_untaxed_home[curr] or 0)
                    self.sales_tax_home -= (curr_ids_amount_amount_taxed_home[curr] or 0)
                    self.after_tax_home -= (curr_ids_amount_amount_total_home[curr] or 0)
                    results.append(res)
         #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(inv_id.currency_id.id,curr_ids_amount_untaxed[inv_id.currency_id.id]))
        return results

    def _get_lines(self):
        results = []
        val_part = []
        val_inv = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        code_from = self.partner_code_from
        code_to = self.partner_code_to
        inv_from = self.inv_from
        inv_to = self.inv_to
        account_invoice_obj = self.pool.get('account.invoice')
        res_partner_obj = self.pool.get('res.partner')

        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
        if inv_from and account_invoice_obj.browse(self.cr, self.uid, inv_from) and account_invoice_obj.browse(self.cr, self.uid, inv_from).number:
            val_inv.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, inv_from).number))
        if inv_to and account_invoice_obj.browse(self.cr, self.uid, inv_to) and account_invoice_obj.browse(self.cr, self.uid, inv_to).number:
            val_inv.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, inv_to).number))
        val_part.append(('customer', '=', True))
        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
        if part_ids:
            partner_ids = res_partner_obj.browse(self.cr, self.uid, part_ids)
            val_inv.append(('date_invoice', '>=', date_from))
            val_inv.append(('date_invoice', '<=', date_to))
            val_inv.append(('type', 'in', ['out_invoice','out_refund']))
            val_inv.append(('state', 'in', ['open','paid']))
            for part in partner_ids:
                val_inv2 = list(val_inv)
                val_inv2.append(('partner_id', '=', part.id))
                inv_ids = account_invoice_obj.search(self.cr, self.uid, val_inv2, order='date_invoice ASC')
                if inv_ids:
                    line_ids = []
                    res = {}
                    for inv_id in account_invoice_obj.browse(self.cr, self.uid, inv_ids):
                        line_ids.append(inv_id)
                    res['ref'] = part.ref
                    res['name'] = part.name
                    res['lines'] = line_ids
                    results.append(res)
        return results

report_sxw.report_sxw('report.sales.journal.by.customer.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/sales_journal_by_customer_report.rml', parser=sales_journal_by_customer_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
