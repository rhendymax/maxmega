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
        self.date_from          = data['form']['date_from']
        self.date_to            = data['form']['date_to']
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
        res = ''
        if type == 'zone_from': res = self.zone_from or '-'
        if type == 'zone_to': res = self.zone_to or '-'
        if type == 'date_from': res = self.date_from or '-'
        if type == 'date_to': res = self.date_to or '-'
        return res
            
    def get_lines(self):
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        zone_from   = self.zone_from
        zone_to     = self.zone_to
        date_from   = self.date_from
        date_to     = self.date_to
        filter      = ["ai.state = 'open'", "aj.type = 'sale'"]
        result      = []
        
        if zone_from:
            filter.append("rpa.city >= '%s'" % zone_from)
        if zone_to:
            filter.append("rpa.city <= '%s'" % zone_to)
        if date_from:
            filter.append("ai.date_invoice >= '%s'" % date_from)
        if date_to:
            filter.append("ai.date_invoice <= '%s'" % date_to)
            
        filter = " AND ".join(map(str, filter))
        filter = filter and "WHERE " + str(filter) or ''
        
        cr.execute('SELECT ai.id ' \
                   'FROM account_invoice AS ai ' \
                   'LEFT JOIN res_partner_address AS rpa ON rpa.id = ai.address_invoice_id ' \
                   'LEFT JOIN account_journal AS aj ON aj.id = ai.journal_id ' \
                   '%s ' \
                   'ORDER BY rpa.city ASC' % filter)
                   
        for r in cr.fetchall():
            result.append(invoice_obj.browse(cr, uid, r[0]))
            
        return result 
    
report_sxw.report_sxw('report.sale.journal.zone_landscape', 'account.invoice',
    'addons/max_report/report/sale_journal_zone_report.rml', parser=report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
