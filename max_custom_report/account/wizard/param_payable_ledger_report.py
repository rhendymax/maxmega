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

from osv import fields, osv
import time
import pooler
import base64
from tools import float_round, float_is_zero, float_compare

class param_payable_report(osv.osv_memory):
    _name = 'param.payable.ledger.report'
    _description = 'Param Payable Ledger Report'
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'supplier_search_vals': fields.selection([('code','Supplier Code'),('name', 'Supplier Name')],'Supplier Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supp Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Supplier From', domain=[('supplier','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Supplier To', domain=[('supplier','=',True)], required=False),
        'partner_input_from': fields.char('Supplier From', size=128),
        'partner_input_to': fields.char('Supplier To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_partner_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
        'fiscal_year':fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'report_type' : 'payable',
        'date_selection': 'none_sel',
        'supp_selection': 'all',
        'supplier_search_vals': 'code',
        'filter_selection': 'all_vall',
    }

    def onchange_date_selection(self, cr, uid, ids, date_selection, context=None):
        if context is None:
            context = {}
        res = {}
        if date_selection:
            if date_selection == 'period_sel':
                res['value'] = {'period_filter_selection': 'def',
                                 }
            else:
                res['value'] = {'period_filter_selection': False,
                                 }
        return res

    def onchange_supp_selection(self, cr, uid, ids, supp_selection, context=None):
        if context is None:
            context = {}
        
        res = {'value': {'partner_code_from': False, 'partner_code_to':False, 'partner_ids':False}}

        if supp_selection:
            if supp_selection == 'all':
                res['domain'] = {'partner_code_from': [('supplier','=',True)],
                                 'partner_code_to': [('supplier','=',True)],
                                 'partner_ids': [('supplier','=',True)],
                                 }
            elif supp_selection == 'supplier':
                res['domain'] = {'partner_code_from': [('supplier','=',True),('sundry', '=', False)],
                                 'partner_code_to': [('supplier','=',True),('sundry', '=', False)],
                                 'partner_ids': [('supplier','=',True),('sundry', '=', False)],
                                 }
            elif supp_selection == 'sundry':
                res['domain'] = {'partner_code_from': [('sundry','=',True),('supplier', '=', True)],
                                 'partner_code_to': [('sundry','=',True),('supplier', '=', True)],
                                 'partner_ids': [('sundry','=',True),('supplier', '=', True)],
                                 }
        return res

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'fiscal_year','date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to' \
                                                ], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'fiscal_year','date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to' \
                    ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, 'payable',  context=context)

        return self._get_tplines(cr, uid, ids, used_context, 'payable', context=context)

    def _build_contexts(self, cr, uid, ids, data, report_type, context=None):
        if context is None:
            context = {}
        result = {}
        res_partner_obj = self.pool.get('res.partner')
        account_journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        account_fiscalyear_obj = self.pool.get('account.fiscalyear')
        result['fiscal_year'] = data['form']['fiscal_year'] or ''
        fiscal_year_name =  data['form']['fiscal_year'] and account_fiscalyear_obj.browse(cr, uid, data['form']['fiscal_year']) \
                            and account_fiscalyear_obj.browse(cr, uid, data['form']['fiscal_year']).name or False
        result['fiscal_year_name'] = fiscal_year_name
        qry_supp = ''
        val_part = []
        qry_jour = ''
        val_jour = []
        
        partner_ids = False
        journal_ids = False
        
        if report_type == 'receivable':
            data_search = data['form']['cust_search_vals']
            result['supp_selection'] = 'Customer'
            qry_supp = 'customer = True'
            val_part.append(('customer', '=', True))
        elif report_type == 'payable':
            data_search = data['form']['supplier_search_vals']
            if data['form']['supp_selection'] == 'all':
                result['supp_selection'] = 'Supplier & Sundry'
                qry_supp = 'supplier = True'
                val_part.append(('supplier', '=', True))
            elif data['form']['supp_selection'] == 'supplier':
                result['supp_selection'] = 'Supplier'
                qry_supp = 'supplier = True and sundry = False'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', False))
            elif data['form']['supp_selection'] == 'sundry':
                result['supp_selection'] = 'Sundry'
                qry_supp = 'supplier = True and sundry = True'
                val_part.append(('supplier', '=', True))
                val_part.append(('sundry', '=', True))
        
        partner_default_from = data['form']['partner_default_from'] or False
        partner_default_to = data['form']['partner_default_to'] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False
        partner_default_from_str = partner_default_to_str = ''
        partner_input_from_str = partner_input_to_str= ''
        
        if data_search == 'code':
            if report_type =='payable':
                result['data_search'] = 'Supplier Code'
            elif report_type =='receivable':
                result['data_search'] = 'Customer Code'
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).ref:
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).ref
                    val_part.append(('ref', '>=', res_partner_obj.browse(cr, uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).ref:
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).ref
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(cr, uid, partner_default_to).ref))
                result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    partner_input_from_str = partner_input_from
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    partner_input_to_str = partner_input_to
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))

                result['filter_selection'] = '"' + partner_input_from_str + '" - "' + partner_input_to_str + '"'

                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                pr_ids = ''
                if data['form']['partner_ids']:
                    for pr in  res_partner_obj.browse(cr, uid, data['form']['partner_ids']):
                        pr_ids += '"' + str(pr.ref) + '",'
                    partner_ids = data['form']['partner_ids']
                result['filter_selection'] = '[' + pr_ids +']'
                
        elif data_search == 'name':
            if report_type =='payable':
                result['data_search'] = 'Supplier Name'
            elif report_type =='receivable':
                result['data_search'] = 'Customer Name'
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'name':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).name:
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).name
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(cr, uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).name:
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).name
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(cr, uid, partner_default_to).name))
                result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    partner_input_from_str = partner_input_from
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    partner_input_to_str = partner_input_to
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                result['filter_selection'] = '"' + partner_input_from_str + '" - "' + partner_input_to_str + '"'
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                pr_ids = ''
                if data['form']['partner_ids']:
                    for pr in  res_partner_obj.browse(cr, uid, data['form']['partner_ids']):
                        pr_ids += '"' + str(pr.name) + '",'
                    partner_ids = data['form']['partner_ids']
                result['filter_selection'] = '[' + pr_ids +']'

        result['partner_ids'] = partner_ids
        #Period
        period_default_from = data['form']['period_default_from'] or False
        period_default_from = period_default_from and period_obj.browse(cr, uid, period_default_from) or False
        period_default_to = data['form']['period_default_to'] or False
        period_default_to = period_default_to and period_obj.browse(cr, uid, period_default_to) or False

        period_input_from = data['form']['period_input_from'] or False
        period_input_to = data['form']['period_input_to'] or False
        period_default_from_str = period_default_to_str = False
        period_input_from_str = period_input_from_str= False

        if data['form']['date_selection'] == 'none_sel':
            result['date_search'] = ''
            result['period_ids'] = False
            result['date_from'] = False
            result['date_to'] = False
        elif data['form']['date_selection'] == 'period_sel':
            result['date_search'] = 'period'
            val_period = []
            period_from_txt = period_to_txt = ''
            if data['form']['period_filter_selection'] == 'def':
                if period_default_from and period_default_from.date_start:
                    period_from_txt = period_default_from.code
                    val_period.append(('date_start', '>=', period_default_from.date_start))
                if period_default_to and period_default_to.date_start:
                    period_to_txt = period_default_to.code
                    val_period.append(('date_start', '<=', period_default_to.date_start))
                result['period_ids'] = period_obj.search(cr, uid, val_period)
            elif data['form']['period_filter_selection'] == 'input':
                if period_input_from:
                    period_from_txt = period_input_from
                    cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_from) + "%' " \
                                    "order by code limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        
                        val_period.append(('code', '>=', qry['code']))
                        
                if period_input_to:
                    period_to_txt = period_input_to
                    cr.execute("select code " \
                                    "from account_period "\
                                    "where " \
                                    "code ilike '" + str(period_input_to) + "%' " \
                                    "order by code limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        val_period.append(('code', '<=', qry['code']))
                result['period_ids'] = period_obj.search(cr, uid, val_period)
            result['date_showing'] = '"' + period_from_txt + '" - "' + period_to_txt + '"'
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['period_ids'] = False
            result['date_search'] = 'date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'
            
        return result

    def _get_tplines(self, cr, uid, ids,data, type, context):

        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        cr = cr
        uid = uid
        period_obj = self.pool.get('account.period')
        invoice_obj = self.pool.get('account.invoice')
        aml_obj = self.pool.get('account.move.line')
        partner_obj = self.pool.get('res.partner')
        report_total = 0.00
        balance_by_cur = {}
        results = []
        results1 = []
        fiscal_year = form['fiscal_year'] or ''
        partner_ids = form['partner_ids'] or False
        
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "

        date_from = form['date_from']
        date_to = form['date_to']

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "
        
        period_ids = form['period_ids'] or False
        min_period = False
        supp_selection = form['supp_selection']
        data_search = form['data_search']
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        if type == 'payable':
            header += 'Account Payable Ledger Report' + " \n"
            header += 'Supplier : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Supplier search : ' + form['filter_selection'] + " \n") or ''
            sign = -1
        elif type == 'receivable':
            header += 'Account Receivable Ledger Report' + " \n"
            header += 'Customer : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''
            sign = 1
        fiscal_year_name = form['fiscal_year_name'] or False
        header += (fiscal_year_name and 'Fiscal Year : ' + str(fiscal_year_name) + " \n") or ''
        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += 'Invoice No;Invoice Date;Type;CCY;Exchange Rate;Amt;Home Amt;New Home Balance' + " \n"


        min_period = False
        if period_ids:
            min_period = period_obj.search(cr, uid, [('id', 'in', period_ids)], order='date_start', limit=1)

        elif date_from:
            min_period = period_obj.search(cr, uid, [('date_start', '<=', date_from)], order='date_start Desc', limit=1)
        if fiscal_year:
            
            if min_period:
                if fiscal_year != period_obj.browse(cr, uid, min_period[0]).fiscalyear_id.id:
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
                if fiscal_year != period_obj.browse(cr, uid, max_period[0]).fiscalyear_id.id:
                    max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
            else:
                max_period = period_obj.search(cr, uid, [('fiscalyear_id', '=', fiscal_year)], order='date_start Desc', limit=1)
        if not max_period:
            max_period = period_obj.search(cr, uid, [], order='date_start Desc', limit=1)
        max_period = period_obj.browse(cr, uid, max_period[0])

        date_start_min_period = min_period and min_period.date_start or False
        date_start_max_period = max_period and period_obj.browse(cr, uid, max_period.id).date_start or False
        val_period = []
        if date_start_max_period:
            val_period.append(('date_start', '<=', date_start_max_period))

        qry_period_ids = period_obj.search(cr, uid, val_period)
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_move_line AS l, account_account AS account, " \
                " account_move AS am " \
                "WHERE l.partner_id IS NOT NULL " \
                    "AND l.account_id = account.id " \
                    "AND am.id = l.move_id " \
                    "And account.type = '" + type + "' " \
                    "AND am.state IN ('draft', 'posted') " \
                    + partner_qry \
                    + date_to_qry \
                    + period_qry)
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "
        period_qry2 = (qry_period_ids and ((len(qry_period_ids) == 1 and "and aml.period_id = " + str(qry_period_ids[0]) + " ") or "and aml.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND and aml.period_id IN (0) "
        date_from_qry2 = date_from and "And aml.date >= '" + str(date_from) + "' " or " "
        date_to_qry2 = date_to and "And aml.date <= '" + str(date_to) + "' " or " "
        
        cr.execute(
                "SELECT id, name, ref " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()
        if qry:
            for s in qry:
                val = []
                cr.execute("SELECT DISTINCT ap.id as period_id " \
                    "from account_move_line aml "\
                    "left join account_move am on aml.move_id = am.id "\
                    "left join account_account aa on aml.account_id = aa.id "\
                    "left join res_company rco on aml.company_id = rco.id "\
                    "left join res_currency rc on COALESCE(aml.currency_id,rco.currency_id) = rc.id "\
                    "left join res_partner rp on aml.partner_id = rp.id "\
                    "left join account_period ap on aml.period_id = ap.id "\
                    "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                    "left join account_journal aj on aml.journal_id = aj.id "\
                    "where " \
                    "am.state in ('draft', 'posted') " \
                    "and aa.type = '" + type + "' " \
                     + period_qry2 \
                    + date_to_qry2 + \
                    "and aml.partner_id = " + str(s['id']))
                period_ids_vals = []
                qry3 = cr.dictfetchall()
                if qry3:
                    for t in qry3:
                        period_ids_vals.append(t['period_id'])
                period_ids_vals_qry = (len(period_ids_vals) > 0 and ((len(period_ids_vals) == 1 and "where ap.id = " +  str(period_ids_vals[0]) + " ") or "where ap.id IN " +  str(tuple(period_ids_vals)) + " ")) or "where ap.id IN (0) "
                cr.execute(
                        "SELECT ap.id, ap.code, ap.date_start as period_startdate, af.name as fiscalyear_name " \
                        "FROM account_period ap " \
                        "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                        + period_ids_vals_qry \
                        + " order by ap.date_start")
                qry4 = cr.dictfetchall()
                balance = 0
                closing = 0
                closing_inv = 0
                if qry4:
                    for u in qry4:
                        opening_balance = balance
                        cr.execute("select rp.id as partner_id, " \
                            "rp.ref as partner_ref, " \
                            "rp.name as partner_name, " \
                            "rc.id as currency_id, " \
                            "rc.name as currency_name, " \
                            "af.id as fiscalyear_id, " \
                            "af.name as fiscalyear_name, " \
                            "ap.id as period_id, " \
                            "ap.code as period_code, " \
                            "ap.date_start as period_startdate, " \
                            "aml.is_depo as depo_status, " \
                            "am.name as am_name, " \
                            "sum(aml.debit - aml.credit) as home_amt, " \
                            "sum(abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) " \
                            "THEN amount_currency " \
                            "ELSE aml.debit - aml.credit " \
                            "END) * (" \
                            "CASE WHEN (debit - credit) > 0 " \
                            "THEN 1 " \
                            "ELSE -1 " \
                            "END" \
                            ")) as inv_amt, " \
                            "aml.exrate as rate, " \
                            "aj.type as journal_type, " \
                            "aml.date as aml_date "\
                            "from account_move_line aml "\
                            "left join account_move am on aml.move_id = am.id "\
                            "left join account_account aa on aml.account_id = aa.id "\
                            "left join res_company rco on aml.company_id = rco.id "\
                            "left join res_currency rc on COALESCE(aml.currency_id,rco.currency_id) = rc.id "\
                            "left join res_partner rp on aml.partner_id = rp.id "\
                            "left join account_period ap on aml.period_id = ap.id "\
                            "left join account_fiscalyear af on ap.fiscalyear_id = af.id "\
                            "left join account_journal aj on aml.journal_id = aj.id "\
                            "where " \
                            "am.state in ('draft', 'posted') " \
                            "and aa.type = '" + type + "' " \
                            "and ap.id = " + str(u['id']) + " "\
                            + date_to_qry2 + \
                            "and aml.partner_id = " + str(s['id']) + " "\
                            "group by rp.id, rp.ref, rp.name, rc.id, rc.name, af.id, " + \
                            "af.name, ap.id, ap.code, ap.date_start, aml.is_depo, am.name, " + \
                            "aml.exrate, aj.type, aml.date " + \
                            "order by rp.ref,af.name, ap.date_start, aml.date")
                        qry5 = cr.dictfetchall()
                        period = False
                        val_ids2 = []
                        period_id_vals = {}
                        if qry5:
                            for v in qry5:
                                balance += (v['home_amt'] * sign)
                                closing += (v['home_amt'] * sign)
                                closing_inv += (v['inv_amt'] * sign)
                                
                                if u['period_startdate'] < min_period.date_start:
                                    continue

                                else:
                                    if v['journal_type'] == 'purchase':
                                        journal_type = 'INV'
                                    elif v['journal_type'] == 'sale':
                                        journal_type = 'INV'
                                    elif v['journal_type'] == 'purchase_refund':
                                        journal_type = 'INV-REF'
                                    elif v['journal_type'] == 'sale_refund':
                                        journal_type = 'INV-REF'
                                    elif v['journal_type'] in ('bank','cash') and v['depo_status'] == True:
                                        journal_type = 'DEPOSIT'
                                    elif v['journal_type'] in ('bank', 'cash') and v['depo_status'] == False:
                                        journal_type = 'PAYMENT'
                                    val_ids2.append({
                                       'am_name' : v['am_name'],
                                       'aml_date' : v['aml_date'],
                                       'journal_type' : journal_type,
                                       'currency_name': v['currency_name'],
                                       'exchange_rate': v['rate'],
                                       'inv_amount': (v['inv_amt'] * sign),
                                       'home_amount': (v['home_amt'] * sign),
                                       'balance': balance,
                                       })
                        val_ids2 = val_ids2 and sorted(val_ids2, key=lambda val_res: val_res['aml_date']) or []

                        if u['period_startdate'] < min_period.date_start:
                            continue
                        else:
                            val.append({
                               'opening_balance' : opening_balance,
                               'fiscalyear_name' : u['fiscalyear_name'],
                               'period_code': u['code'],
                               'period_startdate': u['period_startdate'],
                               'val_ids2': val_ids2,
                               })
                val = val and sorted(val, key=lambda val_res: val_res['period_startdate']) or []
                cur_name = 'False'
                if type == 'payable':
                    cur_name = partner_obj.browse(cr, uid, s['id']).property_product_pricelist_purchase.currency_id.name
                    cur_id = partner_obj.browse(cr, uid, s['id']).property_product_pricelist_purchase.currency_id.id
                elif type == 'receivable':
                    cur_name = partner_obj.browse(cr, uid, s['id']).property_product_pricelist.currency_id.name
                    cur_id = partner_obj.browse(cr, uid, s['id']).property_product_pricelist.currency_id.id
                report_total += closing
                if cur_id not in balance_by_cur:
                    balance_by_cur.update({cur_id : {
                             'inv' : closing_inv,
                             'home' : closing,
                             }
                        })
                else:
                    res_currency_grouping = balance_by_cur[cur_id].copy()
                    res_currency_grouping['inv'] += closing_inv
                    res_currency_grouping['home'] += closing

                    balance_by_cur[cur_id] = res_currency_grouping
                results1.append({
                    'part_name' : s['name'],
                    'part_ref' : s['ref'],
                    'cur_name': cur_name,
                    'closing' : closing_inv,
                    'closing_home': closing,
                    'val_ids' : val,
                    })
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['part_name']) or []
        for rs1 in results1:
            header += '[' + str(rs1['part_ref']) + '] ' + str(rs1['part_name']) + ';;;;' + str(rs1['cur_name']) + ' \n'
            total_home_amt = 0
            for rs2 in rs1['val_ids']:
                header += str(rs2['fiscalyear_name']) + ';' + str(rs2['period_code']) + ';;' + 'Opening Balance' + ';;;;' \
                        + str(rs2['opening_balance']) + ' \n'
                
                for rs3 in rs2['val_ids2']:
                    total_home_amt += rs3['home_amount'] or 0
                    header += str(rs3['am_name']) + ';' + str(rs3['aml_date']) + ';' + str(rs3['journal_type']) + ';' \
                        + str(rs3['currency_name']) + ';' + str(rs3['exchange_rate']) + ';' + str(rs3['inv_amount']) + ';' \
                        + str(rs3['home_amount']) + ';' + str(rs3['balance']) + ' \n'
                header += ';' + ';' + ';' + 'Closing Balance' + ';;;;' + str(total_home_amt + rs2['opening_balance']) + ' \n'
            header += 'Closing Balance By Currency' + ';;;' + 'Currency' + ';;' + 'Inv Amount' + ';' + 'Home Amount' + ' \n'
            header += ';;;' + str(rs1['cur_name']) + ';;' + str(rs1['closing']) + ';' + str(rs1['closing_home']) + ' \n \n'
        header += 'Report Total :;;;;;;;' + str(report_total) + '\n \n \n'
        
        result_currency = []
        currency_obj    = self.pool.get('res.currency')
        for item in balance_by_cur.items():
            result_currency.append({
                'cur_name' : currency_obj.browse(cr, uid, item[0]).name,
                'inv' : item[1]['inv'],
                'home' : item[1]['home'],
            })
        total_home = 0
        result_currency = result_currency and sorted(result_currency, key=lambda val_res: val_res['cur_name']) or []
        header += 'Closing Balance By Currency'
        
        for rs_curr in result_currency:
            if float_is_zero(rs_curr['home'], precision_digits=5):
                rs_curr['home'] = 0.00000
            header += ';;;' + str(rs_curr['cur_name']) + ';;;' + str(rs_curr['inv']) + ';' + str(rs_curr['home']) + ' \n'
            total_home += rs_curr['home'] or 0
        header += ';;;;;;' + 'Total Home :;' + str(total_home) + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        if type == 'payable':
            filename = 'Payable Ledger Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.payable.ledger.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','payable_ledger_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Payable Ledger Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.payable.ledger.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
        elif type == 'receivable':
            filename = 'Receivable Ledger Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.receivable.ledger.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','receivable_ledger_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Receivable Ledger Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.receivable.ledger.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }

    def generate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.payable.ledger.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.ledger.report_landscape',
            'datas': datas,
        }

param_payable_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
