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

class report(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        self.date_from          = data['form']['date_from']
        self.date_to            = data['form']['date_to']
        self.bank_id_from       = data['form']['bank_code_from'] and data['form']['bank_code_from'][0] or False
        self.bank_id_to         = data['form']['bank_code_to'] and data['form']['bank_code_to'][0] or False
        self.voucher_ids        = []
        self.amount_home        = 0
        self.charges_home       = 0
        return super(report, self).set_context(objects, data, ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
            'locale': locale,
            'to_upper': self.to_upper,
            'format_date': self.format_date,
            'get_filter': self.get_filter,
            'get_lines': self.get_lines,
            'get_amount': self.get_amount,
            'get_total': self.get_total,
        })

    def to_upper(self, s):
        return s.upper()
    
    def format_date(self, date):
        try:
            date_format = datetime.strftime(datetime.strptime(date,'%Y-%m-%d'),'%d-%b-%y')
        except:
            return ''
        return date_format
            
    def get_filter(self, type):
        journal_obj = self.pool.get('account.journal')
        res = ''
        if type == 'date_from': res = self.date_from or '-'
        if type == 'date_to': res = self.date_to or '-'
        if type == 'bank_from': res = self.bank_id_from and journal_obj.browse(self.cr, self.uid, self.bank_id_from).name or '-'
        if type == 'bank_to': res = self.bank_id_to and journal_obj.browse(self.cr, self.uid, self.bank_id_to).name or '-'
        return res
            
    def get_lines(self):
        cr          = self.cr
        uid         = self.uid
        voucher_obj = self.pool.get('account.voucher')
        journal_obj = self.pool.get('account.journal')
        date_from   = self.date_from
        date_to     = self.date_to
        code_from   = self.bank_id_from and journal_obj.browse(cr, uid, self.bank_id_from).name or False
        code_to     = self.bank_id_to and journal_obj.browse(cr, uid, self.bank_id_to).name or False
        filter      = ["av.state = 'posted'", "av.payment_option = 'without_writeoff'"]
        grouped     = {}
        result      = []
        
        if date_from:
            filter.append("av.date >= '%s'" % date_from)
        if date_to:
            filter.append("av.date <= '%s'" % date_to)
        if code_from:
            filter.append("aj.name >= '%s'" % code_from)
        if code_to:
            filter.append("aj.name <= '%s'" % code_to)
            
        filter = " AND ".join(map(str, filter))
        filter = filter and "WHERE " + str(filter) or ''
        
        cr.execute('SELECT aj.id, av.id ' \
                   'FROM account_voucher AS av ' \
                   'LEFT JOIN account_journal AS aj ON aj.id = av.journal_id ' \
                   '%s ' \
                   'ORDER BY aj.name, av.number ASC' % filter)
                   
        for r in cr.fetchall():
            if r[0] not in grouped:
                grouped.update({r[0] : [r[1]]})
            else:
                grouped[r[0]].append(r[1])
            # store to self.invoice_ids
            self.voucher_ids.append(r[1])
                
        for item in grouped.items():
            journal = journal_obj.browse(cr, uid, item[0])
            vouchers = []
            for voucher in voucher_obj.browse(cr, uid, item[1]):
                if voucher.writeoff_amount != 0:
                    vouchers.append(voucher)
            if vouchers:
                res = {
                    'journal' : journal,
                    'vouchers' : vouchers,
                }
                result.append(res)
            
        # calculate total
        for voucher in voucher_obj.browse(cr, uid, self.voucher_ids):
            self.amount_home += self.get_amount(voucher) * voucher.ex_rate
            self.charges_home += voucher.bank_charges_amount * voucher.ex_rate
        return result
    
    def get_amount(self, voucher):
        res = voucher.writeoff_amount or 0
        if voucher.type == "payment":
            res *= -1
        return res
    
    def get_total(self, type):
        res = 0
        if type == 'amount_home': res = self.amount_home or 0
        if type == 'charges_home': res = self.charges_home or 0
        return res
    
report_sxw.report_sxw('report.deposit.bank_landscape', 'account.voucher',
    'addons/max_report/report/deposit_bank_report.rml', parser=report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
