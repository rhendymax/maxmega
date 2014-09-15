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
import pooler
import base64
import time

class param_purchase_journal_by_supplier_report(osv.osv_memory):
    _name = 'param.purchase.journal.by.supplier.report'
    _description = 'Param Purchase Journal By Supplier Report'

######
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'supplier_search_vals': fields.selection([('code','Supplier Code'),('name', 'Supplier Name')],'Supplier Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supp Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Supplier From', domain=[('supplier','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Supplier To', domain=[('supplier','=',True)], required=False),
        'partner_input_from': fields.char('Supplier From', size=128),
        'partner_input_to': fields.char('Supplier To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_purchase_partner_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
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
###################

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.purchase.journal.by.supplier.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.journal.report_landscape',
            'datas': datas,
        }
        
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to' \
                                                ], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to']:
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
                if data_found:
                    result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
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
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).name:
                    partner_default_from_str = res_partner_obj.browse(cr, uid, partner_default_from).name
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(cr, uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).name:
                    partner_default_to_str = res_partner_obj.browse(cr, uid, partner_default_to).name
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(cr, uid, partner_default_to).name))
                if data_found:
                    result['filter_selection'] = '"' + partner_default_from_str + '" - "' + partner_default_to_str + '"'
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
                    period_from_txt = period_from_txt
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
        
        inv_balance_by_cur = {}
        ref_balance_by_cur = {}
        
        _total_pre_tax_home = _total_sales_tax_home = _total_after_tax_home = 0
        
        period_obj = self.pool.get('account.period')
        invoice_obj = self.pool.get('account.invoice')
        aml_obj = self.pool.get('account.move.line')
        partner_obj = self.pool.get('res.partner')

        results = []
        results1 = []
        qry_type = ''
        if type == 'payable':
            qry_type = "and l.type in ('in_invoice', 'in_refund') "
        elif type == 'receivable':
            qry_type = "and l.type in ('out_invoice', 'out_refund') "

        period_ids = form['period_ids'] or False
        date_from = form['date_from']
        date_to = form['date_to']

        partner_ids = form['partner_ids'] or False
        #print partner_ids
        min_period = False
        supp_selection = form['supp_selection']
        data_search = form['data_search']
        
        all_content_line = ''
        header = 'sep=;' + " \n"

        if type == 'payable':
            qry_type = "and l.type in ('in_invoice', 'in_refund') "
            header += 'Purchase Journal By Supplier' + " \n"
            header += 'Supplier : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Supplier search : ' + form['filter_selection'] + " \n") or ''
        elif type == 'receivable':
            qry_type = "and l.type in ('out_invoice', 'out_refund') "
            header += 'Sale Journal By Customer' + " \n"
            header += 'Customer : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''

        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += ('journal_selection' in form and 'Bank : ' + str(form['journal_selection']) + "\n") or ''

        header += 'Vch No.;Date;Type;Ccy;Sales Person;Pre Tax Amt;Sales Tax Amt;After Tax Amt;Pre Tax Home;Sales Tax Home;After Tax Home' + " \n"

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
        period_qry = (qry_period_ids and ((len(qry_period_ids) == 1 and "AND l.period_id = " + str(qry_period_ids[0]) + " ") or "AND l.period_id IN " +  str(tuple(qry_period_ids)) + " ")) or "AND l.period_id IN (0) "
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND l.partner_id = " + str(partner_ids[0]) + " ") or "AND l.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND l.partner_id IN (0) "

        date_from_qry = date_from and "And l.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date_invoice <= '" + str(date_to) + "' " or " "

        cr.execute(
                "SELECT DISTINCT l.partner_id " \
                "FROM account_invoice AS l " \
                "WHERE l.partner_id IS NOT NULL " \
                "AND l.state IN ('open', 'paid') " \
                + qry_type \
                + partner_qry \
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
                header += '[' + str(s['ref'] or '') + '] ' + str(s['name'] or '') + ' \n'
                cr.execute(
                        "SELECT l.id as inv_id " \
                        "FROM account_invoice AS l " \
                        "WHERE l.partner_id IS NOT NULL " \
                        "AND l.state IN ('open', 'paid') " \
                        + qry_type \
                        + date_from_qry \
                        + date_to_qry \
                        + period_qry + \
                        "and l.partner_id = " + str(s['id']) + " "\
                        "order by l.date_invoice")
                qry3 = cr.dictfetchall()
                val = []
                period_id_vals = {}
                pre_tax_home = sales_tax_home = after_tax_home = 0
                total_pre_tax = total_sale_tax = total_after_tax = total_pre_tax_home = total_sale_tax_home = total_after_tax_home = 0
                if qry3:
                    for t in qry3:
                        sign = 1
                        inv = invoice_obj.browse(cr, uid, t['inv_id'])
                        if inv.type in ('in_refund', 'out_refund'):
                            sign = -1
                        
                        if inv.type in ('in_invoice', 'out_invoice'):
                            if inv.currency_id.id not in inv_balance_by_cur:
                                inv_balance_by_cur.update({inv.currency_id.id : {
                                         'pre_tax' : ((inv.amount_untaxed or 0) * sign),
                                         'sale_tax' : ((inv.amount_tax or 0) * sign),
                                         'after_tax' : ((inv.amount_total or 0) * sign),
                                         'pre_tax_home' : ((inv.amount_untaxed_home or 0) * sign),
                                         'sale_tax_home' : ((inv.amount_tax_home or 0) * sign),
                                         'after_tax_home' : ((inv.amount_total_home or 0) * sign),
                                         }
                                    })
                            else:
                                inv_grouping = inv_balance_by_cur[inv.currency_id.id].copy()
                                inv_grouping['pre_tax'] += ((inv.amount_untaxed or 0) * sign)
                                inv_grouping['sale_tax'] += ((inv.amount_tax or 0) * sign)
                                inv_grouping['after_tax'] += ((inv.amount_total or 0) * sign)
                                inv_grouping['pre_tax_home'] += ((inv.amount_untaxed_home or 0) * sign)
                                inv_grouping['sale_tax_home'] += ((inv.amount_tax_home or 0) * sign)
                                inv_grouping['after_tax_home'] += ((inv.amount_total_home or 0) * sign)
                                inv_balance_by_cur[inv.currency_id.id] = inv_grouping
                        elif inv.type in ('in_refund', 'out_refund'):
                            if inv.currency_id.id not in ref_balance_by_cur:
                                ref_balance_by_cur.update({inv.currency_id.id : {
                                         'pre_tax' : ((inv.amount_untaxed or 0) * sign),
                                         'sale_tax' : ((inv.amount_tax or 0) * sign),
                                         'after_tax' : ((inv.amount_total or 0) * sign),
                                         'pre_tax_home' : ((inv.amount_untaxed_home or 0) * sign),
                                         'sale_tax_home' : ((inv.amount_tax_home or 0) * sign),
                                         'after_tax_home' : ((inv.amount_total_home or 0) * sign),
                                         }
                                    })
                            else:
                                ref_grouping = ref_balance_by_cur[inv.currency_id.id].copy()
                                ref_grouping['pre_tax'] += ((inv.amount_untaxed or 0) * sign)
                                ref_grouping['sale_tax'] += ((inv.amount_tax or 0) * sign)
                                ref_grouping['after_tax'] += ((inv.amount_total or 0) * sign)
                                ref_grouping['pre_tax_home'] += ((inv.amount_untaxed_home or 0) * sign)
                                ref_grouping['sale_tax_home'] += ((inv.amount_tax_home or 0) * sign)
                                ref_grouping['after_tax_home'] += ((inv.amount_total_home or 0) * sign)
                                ref_balance_by_cur[inv.currency_id.id] = ref_grouping

                        pre_tax_home += ((inv.amount_untaxed_home or 0) * sign)
                        sales_tax_home += ((inv.amount_tax_home or 0) * sign)
                        after_tax_home += ((inv.amount_total_home or 0) * sign)

                        total_pre_tax += ((inv.amount_untaxed or 0) * sign)
                        total_sale_tax += ((inv.amount_tax or 0) * sign)
                        total_after_tax += ((inv.amount_total or 0) * sign)
                        total_pre_tax_home += ((inv.amount_untaxed_home or 0) * sign)
                        total_sale_tax_home += ((inv.amount_tax_home or 0) * sign)
                        total_after_tax_home += ((inv.amount_total_home or 0) * sign)
                        
                        header += str(inv.number or '') + ';' + str(inv.date_invoice or '') + ';' \
                        + str((inv.type == 'in_invoice' and 'IN') or (inv.type == 'in_refund' and 'RET') or (inv.type == 'out_invoice' and 'IN') or (inv.type == 'out_refund' and 'RET') or '') + ';' \
                        + str(inv.currency_id and inv.currency_id.name or '') + ';' + str(inv.user_id and inv.user_id.name or '') + ';' \
                        + str((inv.amount_untaxed or 0) * sign) + ';' + str((inv.amount_tax or 0) * sign) + ';' \
                        + str((inv.amount_total or 0) * sign) + ';' + str((inv.amount_untaxed_home or 0) * sign) + ';' + str((inv.amount_tax_home or 0) * sign) + ';' \
                        + str((inv.amount_total_home or 0) * sign) + ' \n'
                    header += 'Total For : ' + str(s['ref'] or '') + ';;;;;' + str(total_pre_tax) + ';' + str(total_sale_tax) + ';' \
                            + str(total_after_tax) + ';' + str(total_pre_tax_home) + ';' + str(total_sale_tax_home) + ';' + str(total_after_tax_home) + ' \n \n'
                    
                    _total_pre_tax_home += total_pre_tax_home
                    _total_sales_tax_home += total_sale_tax_home
                    _total_after_tax_home += total_after_tax_home
                    
        header += 'Report Total By Currency;;;;;Pre Tax Amt;Sales Tax Amt;After Tax Amt;Pre Tax Home;Sales Tax Home;After Tax Home' + ' \n'
        header += ';;;;' + 'Invoice' + ' \n'
        result2 = []
        currency_obj = self.pool.get('res.currency')
        for item in inv_balance_by_cur.items():
            result2.append({
                'cur_name' : currency_obj.browse(cr, uid, item[0]).name,
                'pre_tax' : item[1]['pre_tax'],
                'sale_tax' : item[1]['sale_tax'],
                'after_tax' : item[1]['after_tax'],
                'pre_tax_home' : item[1]['pre_tax_home'],
                'sale_tax_home' : item[1]['sale_tax_home'],
                'after_tax_home' : item[1]['after_tax_home'],
            })
        result2 = result2 and sorted(result2, key=lambda val_res: val_res['cur_name']) or []
        for rs in result2:
            header += ';;;;' +  str(rs['cur_name']) + ';' + str(rs['pre_tax']) + ';' + str(rs['sale_tax']) + ';' \
                    + str(rs['after_tax']) + ';' + str(rs['pre_tax_home']) + ';' + str(rs['sale_tax_home']) + ';' \
                    + str(rs['after_tax_home']) + ' \n'
            
        header += ';;;;' + 'Credit No' + ' \n'
        result3 = []
        currency_obj    = self.pool.get('res.currency')
        for item in ref_balance_by_cur.items():
            result3.append({
                'cur_name' : currency_obj.browse(cr, uid, item[0]).name,
                'pre_tax' : item[1]['pre_tax'],
                'sale_tax' : item[1]['sale_tax'],
                'after_tax' : item[1]['after_tax'],
                'pre_tax_home' : item[1]['pre_tax_home'],
                'sale_tax_home' : item[1]['sale_tax_home'],
                'after_tax_home' : item[1]['after_tax_home'],
            })
        result3 = result3 and sorted(result3, key=lambda val_res: val_res['cur_name']) or []
        for rs in result3:
            header += ';;;;' + str(rs['cur_name']) + ';' + str(rs['pre_tax']) + ';' + str(rs['sale_tax']) + ';' \
                    + str(rs['after_tax']) + ';' + str(rs['pre_tax_home']) + ';' + str(rs['sale_tax_home']) + ';' \
                    + str(rs['after_tax_home']) + ' \n'
            
        header += ';;;;;;;;' + str(_total_pre_tax_home) + ';' + str(_total_sales_tax_home) + ';' + str(_total_after_tax_home) + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        if type == 'payable':
            filename = 'Purchase Journal By Supplier Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.purchase.journal.by.supplier.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','purchase_journal_by_supplier_report_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Purchase Journal By Supplier Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.purchase.journal.by.supplier.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
        elif type == 'receivable':
            filename = 'Sales Journal By Customer Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.sales.journal.by.customer.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','sales_journal_by_customer_report_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Sales Journal By Customer Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.sales.journal.by.customer.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }

param_purchase_journal_by_supplier_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
