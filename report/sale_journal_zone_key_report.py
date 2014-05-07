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
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        number = 0
        val_part = []

        report_type = data['form']['report_type']
        partner_ids = False

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

        self.partner_ids = partner_ids

#journal
        val_zone = []
        qry_zone = ""

        journal_default_from = data['form']['journal_default_from'] and data['form']['journal_default_from'][0] or False
        journal_default_to = data['form']['journal_default_to'] and data['form']['journal_default_to'][0] or False
        journal_input_from = data['form']['journal_input_from'] or False
        journal_input_to = data['form']['journal_input_to'] or False

        if data['form']['journal_selection'] == 'all_vall':
            journal_ids = account_journal_obj.search(self.cr, self.uid, val_jour, order='name ASC')
            print 'journal_ids'
            print journal_ids
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
        #print self.period_ids
        
        return super(report, self).set_context(objects, data, new_ids, report_type=report_type)


#    def set_context(self, objects, data, ids, report_type=None):
#        self.zone_from          = data['form']['zone_from']
#        self.zone_to            = data['form']['zone_to']
#        self.partner_id_from    = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
#        self.partner_id_to      = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
#        self.date_from          = data['form']['date_from']
#        self.date_to            = data['form']['date_to']
#        self.invoice_ids        = []
#        self.untaxed_home       = 0
#        self.tax_home           = 0
#        self.total_home         = 0
#        return super(report, self).set_context(objects, data, ids, report_type=report_type)

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
