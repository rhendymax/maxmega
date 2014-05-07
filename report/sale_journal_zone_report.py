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
#    def set_context(self, objects, data, ids, report_type=None):
#        self.zone_from          = data['form']['zone_from']
#        self.zone_to            = data['form']['zone_to']
#        self.date_from          = data['form']['date_from']
#        self.date_to            = data['form']['date_to']
#        return super(report, self).set_context(objects, data, ids, report_type=report_type)
#
#    def __init__(self, cr, uid, name, context=None):
#        super(report, self).__init__(cr, uid, name, context=context)
#        self.localcontext.update({
#            'time': time,
#            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
#            'locale': locale,
#            'to_upper': self.to_upper,
#            'format_date': self.format_date,
#            'get_filter': self.get_filter,
#            'get_lines': self.get_lines,
#        })

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        sales_zone_obj = self.pool.get('res.partner.sales.zone')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []

        partner_ids = False
        sales_zone_ids = False

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
        val_sales_zone = []
        sales_zone_default_from = data['form']['sales_zone_default_from'] and data['form']['sales_zone_default_from'][0] or False
        sales_zone_default_to = data['form']['sales_zone_default_to'] and data['form']['sales_zone_default_to'][0] or False
        sales_zone_input_from = data['form']['sales_zone_input_from'] or False
        sales_zone_input_to = data['form']['sales_zone_input_to'] or False

        if data['form']['sales_zone_selection'] == 'all_vall':
            sales_zone_ids = sales_zone_obj.search(self.cr, self.uid, val_sales_zone, order='name ASC')

        if data['form']['sales_zone_selection'] == 'name':
            data_found = False
            if sales_zone_default_from and sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_from) and sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_from).name:
                data_found = True
                val_sales_zone.append(('name', '>=', sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_from).name))
            if sales_zone_default_to and sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_to) and sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_to).name:
                data_found = True
                val_sales_zone.append(('name', '<=', sales_zone_obj.browse(self.cr, self.uid, sales_zone_default_to).name))
            if data_found:
                sales_zone_ids = sales_zone_obj.search(self.cr, self.uid, val_sales_zone, order='name ASC')
        elif data['form']['sales_zone_selection'] == 'input':
            data_found = False
            if sales_zone_input_from:
                self.cr.execute("select name " \
                                "from res_partner_sales_zone "\
                                "where " \
                                "name ilike '" + str(sales_zone_input_from) + "%' " \
                                "order by name limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sales_zone.append(('name', '>=', qry['name']))
            if sales_zone_input_to:
                self.cr.execute("select name " \
                                "from res_partner_sales_zone "\
                                "where " \
                                "name ilike '" + str(sales_zone_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = self.cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sales_zone.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                sales_zone_ids = sales_zone_obj.search(self.cr, self.uid, val_sales_zone, order='name ASC')
        elif data['form']['sales_zone_selection'] == 'selection':
            if data['form']['sales_zone_ids']:
                sales_zone_ids = data['form']['sales_zone_ids']
        self.sales_zone_ids = sales_zone_ids

        #print self.period_ids
        return super(report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
            super(report, self).__init__(cr, uid, name, context=context)
            self.localcontext.update({
                'time': time,
                'locale': locale,
                'get_lines': self._get_lines,
                })

    def _get_lines(self):
        cr              = self.cr
        uid             = self.uid
        period_obj      = self.pool.get('account.period')
        invoice_obj      = self.pool.get('account.invoice')
        results         = []

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

        date_start_min_period = min_period and min_period.date_start or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        val_period = []
        if date_start_min_period:
            val_period.append(('date_start', '>=', date_start_min_period))
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))

        qry_period_ids = period_obj.search(cr, uid, val_period)
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "

        sales_zone_ids = self.sales_zone_ids or False
        sales_zone_qry = (sales_zone_ids and ((len(sales_zone_ids) == 1 and "AND l.sales_zone_ids = " + str(sales_zone_ids[0]) + " ") or "AND l.sales_zone_id IN " + str(tuple(sales_zone_ids)) + " ")) or "AND l.sales_zone_ids IN (0) "

        cr.execute(
                "SELECT l.id as inv_id " \
                "FROM account_invoice AS l " \
                "left join res_partner_sales_zone sz on sz.id = l.sales_zone_id "
                "WHERE " \
                "l.state IN ('open', 'paid') " \
                "and l.type in ('out_invoice', 'out_refund') " \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry \
                + sales_zone_qry + \
                "order by sz.name, l.date_invoice")
        qry3 = cr.dictfetchall()
        if qry3:
            for t in qry3:
                sign = 1
                inv = invoice_obj.browse(self.cr, self.uid, t['inv_id'])
                if inv.type in ('in_refund', 'out_refund'):
                    sign = -1
                results.append(inv)
                results.append({
                                'sz_name' : (inv.sales_zone_id and inv.sales_zone_id.name) or '',
                                'cust_name' : (inv.partner_id and inv.partner_id.name) or '',
                                'amount_total' : ((inv.amount_total or 0) * sign),
                                'inv_date' : inv.date_invoice or False,
                                'inv_no' : inv.number or '',
                                'sales_name' : (inv.user_id and inv.user_id.name) or '',
                                })
        cr.execute(
                "SELECT l.id as inv_id " \
                "FROM account_invoice AS l " \
                "left join res_partner_sales_zone sz on sz.id = l.sales_zone_id "
                "WHERE l.sales_zone_id is null " \
                "and l.state IN ('open', 'paid') " \
                "and l.type in ('out_invoice', 'out_refund') " \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry + \
                "order by sz.name, l.date_invoice")
        qry4 = cr.dictfetchall()
        if qry4:
            for u in qry4:
                sign = 1
                inv2 = invoice_obj.browse(self.cr, self.uid, u['inv_id'])
                if inv2.type in ('in_refund', 'out_refund'):
                    sign = -1
#                results.append(inv2)
                results.append({
                                'sz_name' : (inv2.sales_zone_id and inv2.sales_zone_id.name) or '',
                                'cust_name' : (inv2.partner_id and inv2.partner_id.name) or '',
                                'amount_total' : ((inv2.amount_total or 0) * sign),
                                'inv_date' : inv2.date_invoice or False,
                                'inv_no' : inv2.number or '',
                                'sales_name' : (inv2.user_id and inv2.user_id.name) or '',
                                })
        results = results and sorted(results, key=lambda val_res: val_res['inv_date']) or []
        results = results and sorted(results, key=lambda val_res: val_res['sz_name']) or []
        return results

#    def to_upper(self, s):
#        return s.upper()
#    
#    def format_date(self, date):
#        try:
#            date_format = datetime.strftime(datetime.strptime(date,'%Y-%m-%d'),'%d-%b-%y')
#        except:
#            return ''
#        return date_format
#            
#    def get_filter(self, type):
#        res = ''
#        if type == 'zone_from': res = self.zone_from or '-'
#        if type == 'zone_to': res = self.zone_to or '-'
#        if type == 'date_from': res = self.date_from or '-'
#        if type == 'date_to': res = self.date_to or '-'
#        return res
            
#    def get_lines(self):
#        cr          = self.cr
#        uid         = self.uid
#        invoice_obj = self.pool.get('account.invoice')
#        zone_from   = self.zone_from
#        zone_to     = self.zone_to
#        date_from   = self.date_from
#        date_to     = self.date_to
#        filter      = ["ai.state = 'open'", "aj.type = 'sale'"]
#        result      = []
#
#        if zone_from:
#            filter.append("rpa.city >= '%s'" % zone_from)
#        if zone_to:
#            filter.append("rpa.city <= '%s'" % zone_to)
#        if date_from:
#            filter.append("ai.date_invoice >= '%s'" % date_from)
#        if date_to:
#            filter.append("ai.date_invoice <= '%s'" % date_to)
#            
#        filter = " AND ".join(map(str, filter))
#        filter = filter and "WHERE " + str(filter) or ''
#        
#        cr.execute('SELECT ai.id ' \
#                   'FROM account_invoice AS ai ' \
#                   'LEFT JOIN res_partner_address AS rpa ON rpa.id = ai.address_invoice_id ' \
#                   'LEFT JOIN account_journal AS aj ON aj.id = ai.journal_id ' \
#                   '%s ' \
#                   'ORDER BY rpa.city ASC' % filter)
#                   
#        for r in cr.fetchall():
#            result.append(invoice_obj.browse(cr, uid, r[0]))
#            
#        return result 
    
report_sxw.report_sxw('report.sale.journal.zone_landscape', 'account.invoice',
    'addons/max_report/report/sale_journal_zone_report.rml', parser=report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
