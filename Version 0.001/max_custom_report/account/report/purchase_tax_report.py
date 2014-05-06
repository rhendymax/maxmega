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

class purchase_tax_report(report_sxw.rml_parse):
    _name = 'purchase.tax.report'

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

        val_tax.append(('type_tax_use', '=', 'purchase'))
        qry_tax = 'type_tax_use = "purchase"'
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
#        res = {}
#        self.period_from = data['form']['period_from'] and data['form']['period_from'][0] or False
#        self.period_to = data['form']['period_to'] and data['form']['period_to'][0] or False
#        self.supp_field_selection = data['form']['supp_field_selection']
#        self.supp_code_from = data['form']['supp_code_from'] and data['form']['supp_code_from'][0] or False
#        self.supp_code_to = data['form']['supp_code_to'] and data['form']['supp_code_to'][0] or False
#        self.supp_code_input_from = data['form']['supp_code_input_from'] or False
#        self.supp_code_input_to = data['form']['supp_code_input_to'] or False
#        self.supp_ids = data['form']['supp_ids'] or False
#
#        self.tax_field_selection = data['form']['tax_field_selection']
#        self.purchase_tax_from = data['form']['purchase_tax_from'] and data['form']['purchase_tax_from'][0] or False
#        self.purchase_tax_to = data['form']['purchase_tax_to'] and data['form']['purchase_tax_to'][0] or False
#        self.purchase_tax_input_from = data['form']['purchase_tax_input_from'] or False
#        self.purchase_tax_input_to = data['form']['purchase_tax_input_to'] or False
#        self.taxes_ids = data['form']['taxes_ids'] or False
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(purchase_tax_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(purchase_tax_report, self).__init__(cr, uid, name, context=context)
        self.tax_home = 0.00
        self.difference = 0.00
        self.balance_by_cur = {}
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
#            'get_curr': self._get_curr,
            'get_tax_home': self._get_tax_home,
            'total_difference' : self._total_difference,
            'get_balance_by_cur': self._get_balance_by_cur,
#            'get_lines': self._get_lines,
#            'get_code_from': self._get_code_from,
#            'get_code_to': self._get_code_to,
#            'get_period_from': self._get_period_from,
#            'get_period_to': self._get_period_to,
#            'get_tax_from': self._get_tax_from,
#            'get_tax_to': self._get_tax_to,
            })

    def _get_balance_by_cur(self):

        result = []
        currency_obj    = self.pool.get('res.currency')
        for item in self.balance_by_cur.items():
            result.append({
                'cur_name' : currency_obj.browse(self.cr, self.uid, item[0]).name,
                'taxable_amt' : item[1]['taxable_amt'],
                'tax_amt' : item[1]['tax_amt'],
                'sup_tax' : item[1]['sup_tax'],
            })
        result = result and sorted(result, key=lambda val_res: val_res['cur_name']) or []
        return result

#    def _get_curr(self):
#        results = []
#        period_from = self.period_from
#        period_to = self.period_to
#        type = self.type
#        state = self.state
#        type_query = ''
#        state_query = ''
#        if type:
#            type_query = "('" + str(type) + "')"
#        else:
#            type_query = "('in_invoice', 'in_refund')"
#        if state:
#            state_query = "('" + str(state) + "')"
#        else:
#            state_query = "('open', 'paid')"
#        partner_ids = []
#        partner_ids_ref = {}
#        partner_ids_name = {}
#        partner_ids_cur_lines = {}
#        partner_id = False
#        part_curr_ids = []
#        part_curr_ids_lines = {}
#        part_curr_id = False
#
#        val_period = []
#        curr_ids = []
#        line_ids = []
#        curr_xx_ids = []
#
#        account_period_obj = self.pool.get('account.period')
#    
##        self.cr.execute("SELECT l.id as period_id " \
##               " FROM account_period l " \
##               " GROUP BY l.id, l.date_start, l.special order by l.date_start desc, l.special desc")
##        period_id_search = self.cr.dictfetchone()
##        cr_period_to = period_to or period_id_search and period_id_search['period_id']
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
#        self.cr.execute("select rc.id as curr_id, rc.name as curr_name, " \
#                        "round(sum(ai.amount_total), 2) as total, " \
#                        "round(sum(ai.amount_tax), 2) as tax, " \
#                        "round(sum(ai.amount_tax/ai.inv_rate), 2) as supp_tax " \
#                        "from account_invoice ai " \
#                        "left join res_currency rc on ai.currency_id = rc.id " \
#                        "WHERE ai.period_id in (" + val_ss + ") and ai.state in " + state_query + " " \
#                        "and ai.type in " + type_query + " "\
#                        "group by curr_id, curr_name "
#                        "order by curr_name, curr_id")
#
#        qry = self.cr.dictfetchall()
#        if qry:
#            for r in qry:
#                res = {}
#                res['curr_name'] = r['curr_name']
#                res['total'] = r['total']
#                res['tax'] = r['tax']
#                res['supp_tax'] = r['supp_tax']
#                results.append(res)
#        return results
#
    def _get_tax_home(self):
        return self.tax_home

    def _total_difference(self):
        return self.difference
#
#    def _get_code_from(self):
#        if self.supp_field_selection == 'normal':
#            return self.supp_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.supp_code_from).ref or False
#        elif self.supp_field_selection == 'input':
#            return self.supp_code_input_from or False
#        else:
#            return False
#
#
#    def _get_code_to(self):
#        if self.supp_field_selection == 'normal':
#            return self.supp_code_to and self.pool.get('res.partner').browse(self.cr, self.uid,self.supp_code_to).ref or False
#        elif self.supp_field_selection == 'input':
#            return self.supp_code_input_to or False
#        else:
#            return False
#
#
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
#        if self.tax_field_selection == 'normal':
#            return self.purchase_tax_from and self.pool.get('account.tax').browse(self.cr, self.uid,self.purchase_tax_from).name or False
#        elif self.tax_field_selection == 'input':
#            return self.purchase_tax_input_from or False
#        else:
#            return False
#
#    def _get_tax_to(self):
#        if self.tax_field_selection == 'normal':
#            return self.purchase_tax_to and self.pool.get('account.tax').browse(self.cr, self.uid,self.purchase_tax_to).name or False
#        elif self.tax_field_selection == 'input':
#            return self.purchase_tax_input_to or False
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

#    def _get_lines(self):
##Valiable
#        results = []
#        fpos_obj = self.pool.get('account.fiscal.position')
#        partner_obj = self.pool.get('res.partner')
#        tax_obj = self.pool.get('account.tax')
#        cr = self.cr
#        uid = self.uid
#
#        state_query = "('open', 'paid')"
##Period
#        val_period = []
#        period_from = self.period_from
#        period_to = self.period_to
#        account_period_obj = self.pool.get('account.period')
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
##purchase_tax
#        if self.tax_field_selection == 'normal':
#            val_tax = []
#            tax_from = self.purchase_tax_from
#            tax_to = self.purchase_tax_to
#            if tax_from and tax_obj.browse(self.cr, self.uid, tax_from) and tax_obj.browse(self.cr, self.uid, tax_from).name:
#                val_tax.append(('name', '>=', tax_obj.browse(self.cr, self.uid, tax_from).name))
#            if tax_to and tax_obj.browse(self.cr, self.uid, tax_to) and tax_obj.browse(self.cr, self.uid, tax_to).name:
#                val_tax.append(('name', '<=', tax_obj.browse(self.cr, self.uid, tax_to).name))
#            val_tax.append(('type_tax_use', '=', 'purchase'))
#            tax_ids = tax_obj.search(self.cr, self.uid, val_tax, order='name ASC')
#
#        elif self.tax_field_selection == 'input':
#            val_tax = []
#            val_tax.append(('type_tax_use', '=', 'purchase'))
#            tax_from = self.purchase_tax_input_from
#            if tax_from:
#                self.cr.execute("select name " \
#                                "from account_tax "\
#                                "where type_tax_use = 'sale' and " \
#                                "ref ilike '" + str(tax_from) + "%' " \
#                                "order by name limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_tax.append(('name', '>=', qry['name']))
#            tax_to = self.purchase_tax_input_to
#
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
#        elif self.tax_field_selection == 'selection':
#            if self.taxes_ids:
#                tax_ids = self.taxes_ids
#
##Partner
#        # partner
#        if self.supp_field_selection == 'normal':
#            val_part = []
#            code_from = self.supp_code_from
#            code_to = self.supp_code_to
#            if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
#                val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
#            if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#                val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#            val_part.append(('supplier', '=', True))
#            part_ids = partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#        elif self.supp_field_selection == 'input':
#            val_part = []
#            val_part.append(('supplier', '=', True))
#            supp_from = self.supp_code_input_from
#            if supp_from:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_from) + "%' " \
#                                "order by ref limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '>=', qry['ref']))
#            supp_to = self.supp_code_input_to
#            if supp_to:
#                self.cr.execute("select ref " \
#                                "from res_partner "\
#                                "where supplier = True and " \
#                                "ref ilike '" + str(supp_to) + "%' " \
#                                "order by ref desc limit 1")
#                qry = self.cr.dictfetchone()
#                if qry:
#                    val_part.append(('ref', '<=', qry['ref']))
#            part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
#
#
#        elif self.supp_field_selection == 'selection':
#            if self.supp_ids:
#                part_ids = self.supp_ids
#
#
#
#
#        partner_ids = []
#        partner_ids_ref = {}
#        partner_ids_name = {}
#        partner_ids_cur_lines = {}
#        partner_id = False
#        part_curr_ids = []
#        part_curr_ids_lines = {}
#        part_curr_id = False
#
#
#        curr_ids = []
#        line_ids = []
#        curr_xx_ids = []
#
#        
#    
##        self.cr.execute("SELECT l.id as period_id " \
##               " FROM account_period l " \
##               " GROUP BY l.id, l.date_start, l.special order by l.date_start desc, l.special desc")
##        period_id_search = self.cr.dictfetchone()
##        cr_period_to = period_to or period_id_search and period_id_search['period_id']
#
#
#        self.cr.execute("select rp.id as part_id, rp.ref as part_ref, rp.name as part_name, rc.id as curr_id, rc.name as curr_name, ai.number as number, " \
#                        "round(ai.amount_total, 2) as total, " \
#                        "round(ai.amount_tax, 2) as tax, " \
#                        "(select rate from res_currency_rate where currency_id = ai.currency_id and name < ai.cur_date order by name desc limit 1)  as rate, " \
#                        "round(ai.amount_tax_home, 2) as tax_home, " \
#                        "ai.inv_rate as supp_exrate, " \
#                        "round((ai.amount_tax/ai.inv_rate), 2) as supp_tax, " \
#                        "round(ai.amount_tax_home - (ai.amount_tax/ai.inv_rate), 2) as difference " \
#                        "from account_invoice ai " \
#                        "left join res_partner rp on ai.partner_id = rp.id " \
#                        "left join res_currency rc on ai.currency_id = rc.id " \
#                        "WHERE ai.period_id in (" + val_ss + ") and ai.state in " + state_query + " " \
#                        "and ai.type in ('in_invoice','in_refund') "\
#                        "order by rp.ref, rp.id, rc.name, rc.id")
#
#        qry = self.cr.dictfetchall()
#        if qry:
#            curr_xx2 = []
#            for r in qry:
#                if r['part_id'] not in partner_ids:
#                    partner_ids.append(r['part_id'])
#                    partner_ids_ref[r['part_id']] = str(r['part_ref'])
#                    partner_ids_name[r['part_id']] = str(r['part_name'])
#                    if partner_id:
#                        partner_ids_cur_lines[partner_id] = curr_ids
#                        curr_ids = []
#                        curr_xx2 = []
#                    partner_id = r['part_id']
#                if r['curr_id'] not in curr_xx2:
#                    curr_xx2.append(r['curr_id'])
#                    curr_ids.append({
#                                     'curr_id' : r['curr_id'],
#                                     'curr_name' : r['curr_name'],
#                                     })
#                if str(r['part_id']) + str(r['curr_id']) not in part_curr_ids:
#                    part_curr_ids.append(str(r['part_id']) + str(r['curr_id']))
#                    if part_curr_id:
#                        part_curr_ids_lines[part_curr_id] = line_ids
#                        line_ids = []
#                    part_curr_id = str(r['part_id']) + str(r['curr_id'])
#                line_ids.append({
#                                 'number' : r['number'],
#                                 'total' : r['total'],
#                                 'tax' : r['tax'],
#                                 'rate' : r['rate'],
#                                 'tax_home' : r['tax_home'],
#                                 'supp_exrate' : r['supp_exrate'],
#                                 'supp_tax' : r['supp_tax'],
#                                 'difference' : r['difference'],
#                                 })
#            if partner_id:
#                partner_ids_cur_lines[partner_id] = curr_ids
#                curr_ids = []
#            if part_curr_id:
#                part_curr_ids_lines[part_curr_id] = line_ids
#                line_ids = []
#        if partner_ids:
#            for partner in partner_ids:
#                res = {}
#                res['part_ref'] = partner_ids_ref[partner]
#                res['part_name'] = partner_ids_name[partner]
#                vals_ids = []
#                if partner_ids_cur_lines[partner]:
#                    for rs in partner_ids_cur_lines[partner]:
#                        vals_ids2 = []
#                        sum_total = 0
#                        sum_tax = 0
#                        sum_tax_home = 0
#                        sum_supp_tax = 0
#                        sum_difference = 0
#                        if part_curr_ids_lines[str(partner) + str(rs['curr_id'])]:
#                            vals_ids2 = []
#                            for rs2 in part_curr_ids_lines[str(partner) + str(rs['curr_id'])]:
#                                vals_ids2.append({
#                                    'number' : rs2['number'],
#                                    'total' : rs2['total'],
#                                    'tax' : rs2['tax'],
#                                    'rate' : rs2['rate'],
#                                    'tax_home' : rs2['tax_home'],
#                                    'supp_exrate' : rs2['supp_exrate'],
#                                    'supp_tax' : rs2['supp_tax'],
#                                    'difference' : rs2['difference'],
#                                    })
#                                sum_total += rs2['total']
#                                sum_tax += rs2['tax']
#                                sum_tax_home += rs2['tax_home']
#                                sum_supp_tax += rs2['supp_tax']
#                                sum_difference += rs2['difference']
#                                self.tax_home += rs2['tax_home']
#                                self.difference += rs2['difference']
#                        vals_ids.append({
#                            'curr_name' : rs['curr_name'],
#                            'lines' : vals_ids2,
#                            'sum_total' : sum_total,
#                            'sum_tax' : sum_tax,
#                            'sum_tax_home' : sum_tax_home,
#                            'sum_supp_tax' : sum_supp_tax,
#                            'sum_difference' : sum_difference,
#                            })
#                res['curr_lines'] = vals_ids
#                results.append(res)
#        return results

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

        sign = -1

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
                "SELECT DISTINCT ai.partner_id " \
                "from account_invoice_tax ait " \
                "left join account_invoice ai on ait.invoice_id = ai.id " \
                "left join account_tax ac_t on ait.base_code_id in (ac_t.base_code_id, ac_t.ref_base_code_id) " \
                "WHERE ai.partner_id IS NOT NULL " \
                    "and ai.type in ('in_invoice', 'in_refund') " \
                    "AND ai.state IN ('open', 'paid') " \
                    + partner_qry \
                    + tax_qry \
                    + date_from_qry \
                    + date_to_qry \
                    + period_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])


        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "
        cr.execute(
                "SELECT id, name, ref " \
                "FROM res_partner " \
                      + partner_ids_vals_qry \
                      + " order by name")
        qry = cr.dictfetchall()
        if qry:

            for s in qry:
                inv_val = []
                credit_val = []
#                print str(s['id'])
#                print "and aml.partner_id = " + str(s['id']) + " "
#                print tax_qry2
#                print period_qry2
#                print "select ai.currency_id as inv_curr, ai.number as inv_name, ai.date_invoice as inv_date, ait.base as taxable_amt, ait.amount as tax_amt, coalesce(ai.inv_rate, 0) as supplier_rate, ai.id as inv_id " \
#                        "from account_invoice_tax ait " \
#                        "left join account_invoice ai on ait.invoice_id = ai.id " \
#                        "left join account_tax ac_t on ac_t.base_code_id = ait.base_code_id " \
#                        "WHERE ai.partner_id IS NOT NULL " \
#                            "and ai.type in ('in_invoice') " \
#                            "AND ai.state IN ('open', 'paid') " \
#                            + tax_qry2 + \
#                            period_qry2 + \
#                            "order by ai.date_invoice, ait.sequence"
                cr.execute(
                        "select ai.currency_id as inv_curr, ai.number as inv_name, ai.date_invoice as inv_date, ait.base as taxable_amt, ait.amount as tax_amt, coalesce(ai.inv_rate, 0) as supplier_rate, ai.id as inv_id " \
                        "from account_invoice_tax ait " \
                        "left join account_invoice ai on ait.invoice_id = ai.id " \
                        "left join account_tax ac_t on ac_t.base_code_id = ait.base_code_id " \
                        "WHERE ai.partner_id IS NOT NULL " \
                            "and ai.type in ('in_invoice') " \
                            "AND ai.state IN ('open', 'paid') " \
                            + tax_qry \
                            + date_from_qry \
                            + date_to_qry \
                            + period_qry + \
                            "and ai.partner_id = " + str(s['id']) + " " \
                            "order by ai.date_invoice, ait.sequence")
                qry_inv = cr.dictfetchall()
                inv_taxable_amt = inv_tax_amt = inv_tax_home = inv_sup_tax = inv_difference = 0
                if qry_inv:
                    for inv in qry_inv:
                        rate = tax_home = home_rate = sup_tax = difference = supp_exrate = 0
                        cur_date = inv['inv_date'] or False

                        if home_currency_id and cur_date:
                            res_currency_home_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', home_currency_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_home_ids:
                                home_rate = res_currency_rate2_obj.browse(cr, uid, res_currency_home_ids[0]).rate
#                        print home_currency_id
#                        print cur_date
#                        print home_rate
#                        raise osv.except_osv(_('Error !'), _('test'))
                        cur_id = inv['inv_curr'] or False


                        if cur_id and cur_date:
                            res_currency_rate_ids = res_currency_rate2_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                            if res_currency_rate_ids:
                                rate = res_currency_rate2_obj.browse(cr, uid, res_currency_rate_ids[0]).rate
                        tax = inv['tax_amt'] or 0
#                        print home_rate
#                        print rate
#                        print tax
                        
                        if rate > 0 and tax > 0:
                            tax_home = round(tax / home_rate * rate, 2)

                        if home_currency_id == cur_id:
                            supp_exrate = home_rate
                        else:
                            supp_exrate = inv['supplier_rate']
                        if supp_exrate > 0 and tax > 0:
                            sup_tax =  round(tax / home_rate * supp_exrate, 2)
                        difference = round(tax_home - sup_tax, 2)
                        inv_taxable_amt += inv['taxable_amt']
                        inv_tax_amt += inv['tax_amt']
                        inv_tax_home += tax_home
                        inv_sup_tax += sup_tax
                        inv_difference += difference
                        inv_val.append({
                            'number': inv['inv_name'],
                            'date': inv['inv_date'],
                            'total': inv['taxable_amt'],
                            'tax': inv['tax_amt'],
                            'rate': rate,
                            'tax_home' : tax_home,
                            'supp_exrate' : supp_exrate,
                            'supp_tax' : sup_tax,
                            'difference' : difference,
                            })

#Credit Value
                cr.execute(
                        "select ai.currency_id as inv_curr, ai.number as inv_name, ai.date_invoice as inv_date, ait.base as taxable_amt, ait.amount as tax_amt, coalesce(ai.inv_rate, 0) as supplier_rate, ai.id as inv_id " \
                        "from account_invoice_tax ait " \
                        "left join account_invoice ai on ait.invoice_id = ai.id " \
                        "left join account_tax ac_t on ac_t.ref_base_code_id = ait.base_code_id " \
                        "WHERE ai.partner_id IS NOT NULL " \
                            "and ai.type in ('in_refund') " \
                            "AND ai.state IN ('open', 'paid') " \
                            + tax_qry \
                            + date_from_qry \
                            + date_to_qry \
                            + period_qry + \
                            "and ai.partner_id = " + str(s['id']) + " " \
                            "order by ai.date_invoice, ait.sequence")
                qry_cred = cr.dictfetchall()
                cred_taxable_amt = cred_tax_amt = cred_tax_home = cred_sup_tax = cred_difference = 0
                if qry_cred:
                    for cred in qry_cred:
                        rate = tax_home = home_rate = sup_tax = difference = supp_exrate = 0
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
                        tax = cred['tax_amt'] or 0
                        if rate > 0 and tax > 0:
                            tax_home = round(tax / home_rate * rate, 2)
                        if home_currency_id == cur_id:
                            supp_exrate = home_rate
                        else:
                            supp_exrate = cred['supplier_rate']
                        if supp_exrate > 0 and tax > 0:
                            sup_tax =  round(tax / home_rate * supp_exrate, 2)
                        difference = round(tax_home - sup_tax, 2)
                        cred_taxable_amt += cred['taxable_amt']
                        cred_tax_amt += cred['tax_amt']
                        cred_tax_home += tax_home
                        cred_sup_tax += sup_tax
                        cred_difference += difference
                        credit_val.append({
                            'number': cred['inv_name'],
                            'date': cred['inv_date'],
                            'total': cred['taxable_amt'],
                            'tax': cred['tax_amt'],
                            'rate': rate,
                            'tax_home' : tax_home,
                            'supp_exrate' : supp_exrate,
                            'supp_tax' : sup_tax,
                            'difference' : difference,
                            })

                cur_name = 'False'
                cur_name = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.name
                cur_id = partner_obj.browse(self.cr, self.uid, s['id']).property_product_pricelist_purchase.currency_id.id
                self.tax_home += (inv_tax_home - cred_tax_home)
                self.difference += (inv_difference - cred_difference)

                if cur_id not in self.balance_by_cur:
                    self.balance_by_cur.update({cur_id : {
                             'taxable_amt' : (inv_taxable_amt - cred_taxable_amt),
                             'tax_amt' : (inv_tax_amt - cred_tax_amt),
                             'sup_tax' : (inv_sup_tax - cred_sup_tax),
                             }
                            })
                else:
                    res_currency_grouping = self.balance_by_cur[cur_id].copy()
                    res_currency_grouping['taxable_amt'] += (inv_taxable_amt - cred_taxable_amt)
                    res_currency_grouping['tax_amt'] += (inv_tax_amt - cred_tax_amt)
                    res_currency_grouping['sup_tax'] += (inv_sup_tax - cred_sup_tax)
                    self.balance_by_cur[cur_id] = res_currency_grouping

                results.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    'cur_name': cur_name,
                    'invoice_vals' : inv_val,
                    'credit_vals' : credit_val,
                    'inv_taxable_amt' : inv_taxable_amt,
                    'inv_tax_amt' : inv_tax_amt,
                    'inv_tax_home' : inv_tax_home,
                    'inv_sup_tax' : inv_sup_tax,
                    'inv_difference' : inv_difference,
                    'cred_taxable_amt' : cred_taxable_amt,
                    'cred_tax_amt' : cred_tax_amt,
                    'cred_tax_home' : cred_tax_home,
                    'cred_sup_tax' : cred_sup_tax,
                    'cred_difference' : cred_difference,
                    'total_taxable_amt' : inv_taxable_amt - cred_taxable_amt,
                    'total_tax_amt' : inv_tax_amt - cred_tax_amt,
                    'total_tax_home' : inv_tax_home - cred_tax_home,
                    'total_sup_tax' : inv_sup_tax - cred_sup_tax,
                    'total_difference' : inv_difference - cred_difference,
                    })
                
        results = results and sorted(results, key=lambda val_res: val_res['part_name']) or []
        return results

report_sxw.report_sxw('report.purchase.tax.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/purchase_tax_report.rml', parser=purchase_tax_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
