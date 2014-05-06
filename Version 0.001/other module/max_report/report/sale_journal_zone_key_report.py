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
        self.zone_from          = data['form']['zone_from']
        self.zone_to            = data['form']['zone_to']
        self.partner_id_from    = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
        self.partner_id_to      = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
        self.date_from          = data['form']['date_from']
        self.date_to            = data['form']['date_to']
        self.invoice_ids        = []
        self.untaxed_home       = 0
        self.tax_home           = 0
        self.total_home         = 0
        return super(report, self).set_context(objects, data, ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
            'locale': locale,
            'get_filter': self.get_filter,
            'get_lines': self.get_lines,
            'get_total_cur' : self.get_total_cur,
            'get_total_home' : self.get_total_home,
        })
            
    def get_filter(self, type):
        partner_obj = self.pool.get('res.partner')
        res = ''
        if type == 'zone_from': res = self.zone_from or '-'
        if type == 'zone_to': res = self.zone_to or '-'
        if type == 'cust_from': res = self.partner_id_from and partner_obj.browse(self.cr, self.uid, self.partner_id_from).ref or '-'
        if type == 'cust_to': res = self.partner_id_to and partner_obj.browse(self.cr, self.uid, self.partner_id_to).ref or '-'
        if type == 'date_from': res = self.date_from or '-'
        if type == 'date_to': res = self.date_to or '-'
        return res
            
    def get_lines(self):
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        partner_obj = self.pool.get('res.partner')
        zone_from   = self.zone_from
        zone_to     = self.zone_to
        code_from   = self.partner_id_from and partner_obj.browse(cr, uid, self.partner_id_from).ref or False
        code_to     = self.partner_id_to and partner_obj.browse(cr, uid, self.partner_id_to).ref or False
        date_from   = self.date_from
        date_to     = self.date_to
        filter      = ["ai.state = 'open'", "aj.type = 'sale'"]
        grouped     = {}
        result      = []
        
        if zone_from:
            filter.append("rpa.city >= '%s'" % zone_from)
        if zone_to:
            filter.append("rpa.city <= '%s'" % zone_to)
        if code_from:
            filter.append("rp.ref >= '%s'" % code_from)
        if code_to:
            filter.append("rp.ref <= '%s'" % code_to)
        if date_from:
            filter.append("ai.date_invoice >= '%s'" % date_from)
        if date_to:
            filter.append("ai.date_invoice <= '%s'" % date_to)
            
        filter = " AND ".join(map(str, filter))
        filter = filter and "WHERE " + str(filter) or ''
        
        cr.execute('SELECT rpa.city, ai.id ' \
                   'FROM account_invoice AS ai ' \
                   'LEFT JOIN res_partner AS rp ON rp.id = ai.partner_id ' \
                   'LEFT JOIN res_partner_address AS rpa ON rpa.id = ai.address_invoice_id ' \
                   'LEFT JOIN account_journal AS aj ON aj.id = ai.journal_id ' \
                   '%s ' \
                   'ORDER BY rpa.city, rp.ref ASC' % filter)
                   
        for r in cr.fetchall():
            if r[0] not in grouped:
                grouped.update({r[0] : [r[1]]})
            else:
                grouped[r[0]].append(r[1])
            # store to self.invoice_ids
            self.invoice_ids.append(r[1])
                
        for item in grouped.items():
            invoices = invoice_obj.browse(cr, uid, item[1])
            res = {
                'city' : item[0],
                'invoices' : invoices,
            }
            result.append(res)
        return result 
    
    def get_total_cur(self):
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        currency_obj= self.pool.get('res.currency')
        grouped     = {}
        result      = []
        
        for invoice in invoice_obj.browse(cr, uid, self.invoice_ids):
            if invoice.currency_id.id not in grouped:
                grouped.update({invoice.currency_id.id : [invoice.id]})
            else:
                grouped[invoice.currency_id.id].append(invoice.id)
        for item in grouped.items():
            cur         = currency_obj.browse(cr, uid, item[0])
            untaxed_cur = 0
            tax_cur     = 0
            total_cur   = 0
            untaxed_home= 0
            tax_home    = 0
            total_home  = 0
            
            for inv in invoice_obj.browse(cr, uid, item[1]):
                untaxed_cur += inv.amount_untaxed
                tax_cur     += inv.amount_tax
                total_cur   += inv.amount_total
                untaxed_home+= inv.amount_untaxed * inv.cur_rate
                tax_home    += inv.amount_tax * inv.cur_rate
                total_home  += inv.amount_total * inv.cur_rate
                
            #storing amount
            self.untaxed_home   += untaxed_home
            self.tax_home       += tax_home
            self.total_home     += total_home
            
            res = {
                'cur'           : cur.name,
                'untaxed_cur'   : untaxed_cur,
                'tax_cur'       : tax_cur,
                'total_cur'     : total_cur,
                'untaxed_home'  : untaxed_home,
                'tax_home'      : tax_home,
                'total_home'    : total_home,
            }
            result.append(res)
        return result
    
    def get_total_home(self, type):
        res = 0
        if type == 'untaxed_home': res = self.untaxed_home or 0
        if type == 'tax_home': res = self.tax_home or 0
        if type == 'total_home': res = self.total_home or 0
        return res
    
report_sxw.report_sxw('report.sale.journal.zone.key_landscape', 'account.invoice',
    'addons/max_report/report/sale_journal_zone_key_report.rml', parser=report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
