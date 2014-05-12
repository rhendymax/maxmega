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

import time
import locale
from report import report_sxw
from datetime import datetime
from mx import DateTime as dt
from mx.DateTime import RelativeDateTime as rdt

class statement(report_sxw.rml_parse):
    def set_context(self, objects, data, ids, report_type=None):
        period_id   = data['form']['period_id']
        self.period = self.pool.get('account.period').browse(self.cr, self.uid, period_id[0])
        return super(statement, self).set_context(objects, data, ids, report_type=report_type)
    
    def __init__(self, cr, uid, name, context=None):
        super(statement, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
            'to_upper': self.to_upper,
            'get_statement_date': self.get_statement_date,
            'format_date': self.format_date,
            'get_invoice': self.get_invoice,
            'get_type': self.get_type,
            'get_debit': self.get_debit,
            'get_credit': self.get_credit,
            'get_oth_invoice': self.get_oth_invoice,
        })

    def to_upper(self, s):
        return s.upper()

    def get_statement_date(self):
        return self.period.date_stop
    
    def format_date(self, date):
        try:
            date_format = datetime.strftime(datetime.strptime(date,'%Y-%m-%d'),'%d-%b-%y')
        except:
            return ''
        return date_format

    def get_invoice(self, partner):
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        invoice     = []
        
        invoice_ids = invoice_obj.search(cr, uid, [
                        ('partner_id','=',partner.id),
                        ('state','=','open'),
                        ('period_id','=',self.period.id),
                        ], order="date_invoice ASC")
        if invoice_ids:
            invoice = [inv for inv in invoice_obj.browse(cr, uid, invoice_ids)]
        return invoice

    def get_type(self, invoice):
        if invoice.type == 'in_invoice': return 'IN'
        if invoice.type == 'out_invoice': return 'IN'
        if invoice.type == 'in_refund': return 'IN'
        if invoice.type == 'out_refund': return 'IN'
        return 'IN'

    def get_debit(self, invoice):
        res = 0
        if invoice.type in ['out_invoice', 'in_refund']:
            res = invoice.residual
        return res

    def get_credit(self, invoice):
        res = 0
        if invoice.type in ['in_invoice', 'out_refund']:
            res = invoice.residual
        return res
    
    def get_oth_invoice(self, partner, seq):
        cr          = self.cr
        uid         = self.uid
        invoice_obj = self.pool.get('account.invoice')
        period_obj  = self.pool.get('account.period')
        res         = 0
        period_ids  = []
        
        oth_period_date = dt.strptime(self.period.date_start, '%Y-%m-%d') - rdt(months=seq)
        period_ids = period_obj.search(cr, uid, [('date_start','<=',oth_period_date),('special', '=', False)], order='date_start DESC')
        if period_ids and seq != 4:
            period_ids = [period_ids[0]]
        invoice_ids = invoice_obj.search(cr, uid, [
                        ('partner_id','=',partner.id),
                        ('state','=','open'),
                        ('period_id','in',period_ids),
                        ], order="date_invoice ASC")
        if invoice_ids:
            res = 0
            for inv in invoice_obj.browse(cr, uid, invoice_ids):
                if inv.type in ['out_invoice', 'in_refund']:
                    res += inv.residual
                elif inv.type in ['in_invoice', 'out_refund']:
                    res -= inv.residual
        return res

report_sxw.report_sxw('report.max.account.statement', 'res.partner', 'addons/max_report/report/account_statement.rml', parser=statement, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

