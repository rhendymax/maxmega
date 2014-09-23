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
from datetime import datetime, timedelta
from tools.translate import _

class param_payable_aging_report(osv.osv_memory):
    _name = 'param.payable.aging.report'
    _description = 'Param Payable Aging Report'
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'supplier_search_vals': fields.selection([('code','Supplier Code'),('name', 'Supplier Name')],'Supplier Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supp Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Supplier From', domain=[('supplier','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Supplier To', domain=[('supplier','=',True)], required=False),
        'partner_input_from': fields.char('Supplier From', size=128),
        'partner_input_to': fields.char('Supplier To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_payable_aging_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
        'date_to': fields.date("Age Reference Date", required=True),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'report_type' : 'payable',
        'supp_selection': 'all',
        'supplier_search_vals': 'code',
        'filter_selection': 'all_vall',
    }

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
                                                'date_to'], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_to']:
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
        result['date_to'] = data['form']['date_to']
        result['date_to_header'] = data['form']['date_to'] or False
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
                    qry = self.cr.dictfetchone()
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
        partner_add_obj = self.pool.get('res.partner.address')
        sale_payment_term_obj = self.pool.get('sale.payment.term')
        report_total = 0.00
        balance_by_cur = {}
        ####################
#         pp_ids = []
#         val_part = []
#         val_part.append(('customer', '=', True))
#         pp_search = partner_obj.search(cr, uid, val_part, order='ref ASC')
#         for pp_ids_brw in partner_obj.browse(cr, uid, pp_search):
#             if pp_ids_brw.property_product_pricelist.currency_id.id == 38:
#                 pp_ids.append(pp_ids_brw.id)
#         print pp_ids
#         raise osv.except_osv(_('Invalid action !'), _('test'))
        #######################
        results = []
        results1 = []
        sign = -1

        if type == 'payable':
            sign = -1
        elif type == 'receivable':
            sign = 1
        date_to = form['date_to']
        partner_ids = form['partner_ids'] or False
        #print partner_ids
        
        supp_selection = form['supp_selection']
        data_search = form['data_search']
        
        all_content_line = ''
        
        header = 'sep=;' + " \n"
#        header += ('fiscal_year' in form and 'Fiscal Year : ' + str(form['fiscal_year']) + " \n") or ''
        if type == 'payable':
            header += 'Account Payable Aging Report' + " \n"
            header += 'Supplier : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Supplier search : ' + form['filter_selection'] + " \n") or ''
            deposit_qry = 'and not (aml.credit > 0 and aml.is_depo = True) '
            sign = -1
            
        elif type == 'receivable':
            header += 'Account Receivable Aging Report' + " \n"
            header += 'Customer : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''
            deposit_qry = 'and not (aml.debit > 0 and aml.is_depo = True) '
            sign = 1
        
        header += ('date_to_header' in form and 'Age Reference Date : ' + form['date_to_header'] + ' \n') or ''

#        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
#                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += 'Vch No;Sales Person;TP Doc Date;Due Date;Ref No;Cust PO No;Orig Amt;Orig Amt Home;Paid/CN;Paid/CN Home;< 31;< 31 Home;31 To 60;31 To 60 Home;61 To 90;61 To 90 Home;Over 91;Over 91 Home' + " \n"

        

        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND aml.partner_id = " + str(partner_ids[0]) + " ") or "AND aml.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND aml.partner_id IN (0) "
        cr.execute(
                "select DISTINCT aml.partner_id " \
                "from account_move_line aml " \
                "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
                "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
                "left join res_users rs on rs.id = ai.user_id where aml.partner_id IS NOT NULL " \
                "and am.state IN ('draft', 'posted')  " \
                "and aa.type = '" + type + "' " \
                "and not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                + deposit_qry + \
                "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), 0 " \
                ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                "And aml.date  <= '" +str(date_to) + "' "\
                "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
                + partner_qry)
#         print "select DISTINCT aml.partner_id " \
#                 "from account_move_line aml " \
#                 "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
#                 "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
#                 "left join res_users rs on rs.id = ai.user_id where aml.partner_id IS NOT NULL " \
#                 "and am.state IN ('draft', 'posted')  " \
#                 "and aa.type = '" + type + "' " \
#                 "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
#                 "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
#                 "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id), " \
#                 "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id), 0 " \
#                 ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
#                 "And aml.date  <= '" +str(date_to) + "' "\
#                 "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
#                 + partner_qry
#         raise osv.except_osv(_('Invalid action !'), _('test'))
        partner_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                partner_ids_vals.append(r['partner_id'])
        
        partner_ids_vals_qry = (len(partner_ids_vals) > 0 and ((len(partner_ids_vals) == 1 and "where id = " +  str(partner_ids_vals[0]) + " ") or "where id IN " +  str(tuple(partner_ids_vals)) + " ")) or "where id IN (0) "

        cr.execute(
                "SELECT id, name, ref, credit_limit " \
                "FROM res_partner " \
                + partner_ids_vals_qry \
                + " order by name")
        qry = cr.dictfetchall()

        if qry:
            for s in qry:
                partner = partner_obj.browse(cr, uid, s['id'])
                cur_name = 'False'
                if type == 'payable':
                    cur_name = partner.property_product_pricelist_purchase.currency_id.name
                    cur_id = partner.property_product_pricelist_purchase.currency_id.id
                elif type == 'receivable':
                    cur_name = partner.property_product_pricelist.currency_id.name
                    cur_id = partner.property_product_pricelist.currency_id.id
                addr = partner_obj.address_get(cr, uid, [s['id']], ['delivery', 'invoice', 'contact'])
                addr = addr and addr['invoice'] and partner_add_obj.browse(cr, uid, addr['invoice']) or False
                
                cr.execute(
                        "select sp.id as picking_id, ai.sale_term_id as term_id, aml.id as aml_id, am.name as inv_name, aml.date as inv_date, ai.ref_no as inv_ref, rs.name as sales_name, aml.debit - aml.credit as home_amt, " \
                        "abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) THEN amount_currency ELSE aml.debit - aml.credit END) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) " \
                        "as inv_amt, " \
                        "abs(coalesce ( " \
                        "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                        "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), " \
                        "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid_home, " \
                        "abs(coalesce ( " \
                        "(select sum(CASE WHEN (aml4.currency_id is not null) and (aml4.cur_date is not null) THEN amount_currency ELSE aml4.debit - aml4.credit END) from account_move_line aml4 where aml4.reconcile_partial_id = aml.reconcile_partial_id and aml4.id != aml.id and aml4.date  <= '" +str(date_to) + "'), " \
                        "(select sum(CASE WHEN (aml5.currency_id is not null) and (aml5.cur_date is not null) THEN amount_currency ELSE aml5.debit - aml5.credit END) from account_move_line aml5 where aml5.reconcile_id = aml.reconcile_id and aml5.id != aml.id and aml5.date  <= '" +str(date_to) + "'), " \
                        "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid " \
                        "from account_move_line aml " \
                        "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
                        "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
                        "left join res_users rs on rs.id = ai.user_id left join stock_picking sp on ai.picking_id = sp.id where aml.partner_id IS NOT NULL " \
                        "and am.state IN ('draft', 'posted')  " \
                        "and aa.type = '" + type + "' " \
                        "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                        + deposit_qry + \
                        "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                        "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                        "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), 0 " \
                        ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                        "And aml.date  <= '" +str(date_to) + "' "\
                        "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
                        "and aml.partner_id = " + str(s['id']) + " order by aml.date")
#                 print "select sp.id as picking_id, ai.sale_term_id as term_id, aml.id as aml_id, am.name as inv_name, aml.date as inv_date, ai.ref_no as inv_ref, rs.name as sales_name, aml.debit - aml.credit as home_amt, " \
#                         "abs(CASE WHEN (aml.currency_id is not null) and (aml.cur_date is not null) THEN amount_currency ELSE aml.debit - aml.credit END) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) " \
#                         "as inv_amt, " \
#                         "abs(coalesce ( " \
#                         "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
#                         "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), " \
#                         "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid_home, " \
#                         "abs(coalesce ( " \
#                         "(select sum(CASE WHEN (aml4.currency_id is not null) and (aml4.cur_date is not null) THEN amount_currency ELSE aml4.debit - aml4.credit END) from account_move_line aml4 where aml4.reconcile_partial_id = aml.reconcile_partial_id and aml4.id != aml.id and aml4.date  <= '" +str(date_to) + "'), " \
#                         "(select sum(CASE WHEN (aml5.currency_id is not null) and (aml5.cur_date is not null) THEN amount_currency ELSE aml5.debit - aml5.credit END) from account_move_line aml5 where aml5.reconcile_id = aml.reconcile_id and aml5.id != aml.id and aml5.date  <= '" +str(date_to) + "'), " \
#                         "0)) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END) as paid " \
#                         "from account_move_line aml " \
#                         "left join account_move am on aml.move_id = am.id left join account_invoice ai on am.id = ai.move_id " \
#                         "left join account_account aa on aml.account_id = aa.id left join account_journal aj on am.journal_id = aj.id " \
#                         "left join res_users rs on rs.id = ai.user_id left join stock_picking sp on ai.picking_id = sp.id where aml.partner_id IS NOT NULL " \
#                         "and am.state IN ('draft', 'posted')  " \
#                         "and aa.type = '" + type + "' " \
#                         "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
#                         "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
#                         "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
#                         "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), 0 " \
#                         ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
#                         "And aml.date  <= '" +str(date_to) + "' "\
#                         "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
#                         "and aml.partner_id = " + str(s['id']) + " order by aml.date"
#                 raise osv.except_osv(_('Invalid action !'), _('test'))
                
                qry3 = cr.dictfetchall()
                val = []
                total_amt1 = total_amt2= total_amt3 = total_amt4 = total_home_amt1 = total_home_amt2 = total_home_amt3 = total_home_amt4 = 0.00
                if qry3:
                    for t in qry3:
                        due_date = False
                        sale_term_id = t['term_id'] and sale_payment_term_obj.browse(cr, uid, t['term_id']) or False
                        daysremaining = 0
                        if sale_term_id:
                            partner_grace = partner and partner.grace or 0
                            sale_grace = sale_term_id.grace or 0
                            gracedays = partner_grace > 0 and partner_grace or sale_grace
                            termdays = sale_term_id.days
                            Date = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                            due_date = Date + timedelta(days=(termdays + gracedays))
                        #print EndDate
                        due_date = due_date and due_date.strftime('%Y-%m-%d') or False
                        d = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                        delta = datetime.strptime(date_to, '%Y-%m-%d') - d
                        daysremaining = delta.days
                        cust_po_no = ''
                        if type == 'receivable':
                                if t['picking_id']:
                                    cr.execute(
                                            "select so.client_order_ref as cust_po_no from sale_order_picking_rel sopr " \
                                            "left join sale_order so on sopr.order_id = so.id left join stock_picking sp on sopr.picking_id = sp.id " \
                                            "where sopr.picking_id = " + str(t['picking_id']) + " " \
                                            "order by so.date_order limit 1")
                                    qry4 = cr.dictfetchall()
                                    if qry4:
                                        for u in qry4:
                                            cust_po_no = u['cust_po_no']
                        remain_amt = (t['inv_amt'] * sign) - (t['paid'] * sign)
                        remain_home_amt = (t['home_amt'] * sign) - (t['paid_home'] * sign)
                        total_amt1 += daysremaining < 31 and remain_amt or 0.00
                        total_amt2 += (daysremaining > 30 and daysremaining < 61 and remain_amt) or 0.00
                        total_amt3 += (daysremaining > 60 and daysremaining < 91 and remain_amt) or 0.00
                        total_amt4 += daysremaining > 90 and remain_amt or 0.00
                        total_home_amt1 += daysremaining < 31 and remain_home_amt or 0.00
                        total_home_amt2 += (daysremaining > 30 and daysremaining < 61 and remain_home_amt) or 0.00
                        total_home_amt3 += (daysremaining > 60 and daysremaining < 91 and remain_home_amt) or 0.00
                        total_home_amt4 += daysremaining > 90 and remain_home_amt or 0.00
                        val.append({
                            'invoice_name' : t['inv_name'] or '',
                            'sales_person': t['sales_name'] or '',
                            'invoice_date' : t['inv_date'] or '',
                            'due_date' : due_date or '',
                            'ref_no' : t['inv_ref'] or '',
                            'cust_po_no' : cust_po_no or '',
                            'orig_amt' : (t['inv_amt'] * sign) or 0.00,
                            'home_orig_amt' : (t['home_amt'] * sign) or 0.00,
                            'paid_amt' : (t['paid'] * sign) or 0.00,
                            'home_paid_amt' : (t['paid_home'] * sign) or 0.00,
                            'amt1':  daysremaining < 31 and remain_amt or 0.00,
                            'home_amt1': daysremaining < 31 and remain_home_amt or 0.00,
                            'amt2': (daysremaining > 30 and daysremaining < 61 and remain_amt) or 0.00,
                            'home_amt2': (daysremaining > 30 and daysremaining < 61 and remain_home_amt) or 0.00,
                            'amt3': (daysremaining > 60 and daysremaining < 91 and remain_amt) or 0.00,
                            'home_amt3': (daysremaining > 60 and daysremaining < 91 and remain_home_amt) or 0.00,
                            'amt4': daysremaining > 90 and remain_amt or 0.00,
                            'home_amt4': daysremaining > 90 and remain_home_amt or 0.00,
                            })
                val = val and sorted(val, key=lambda val_res: val_res['invoice_date']) or []
                results1.append({
                    'part_name' : s['name'] or '',
                    'part_ref' : s['ref'] or '',
                    'cur_name': cur_name or '',
                    'contact_phone' : addr and addr.phone or '',
                    'contact_person' : addr and addr.name or '',
                    'credit_limit' : s['credit_limit'] or 0.00,
                    'total_inv' : (total_amt1 + total_amt2 + total_amt3 + total_amt4) or 0.00,
                    'total_home' : (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4) or 0.00,
                    'total_amt1' : total_amt1 or  0.00,
                    'total_home_amt1' : total_home_amt1 or 0.00,
                    'total_amt2' : total_amt2 or 0.00,
                    'total_home_amt2' : total_home_amt2 or 0.00,
                    'total_amt3' : total_amt3 or 0.00,
                    'total_home_amt3' : total_home_amt3 or 0.00,
                    'total_amt4' : total_amt4 or 0.00,
                    'total_home_amt4' : total_home_amt4 or 0.00,
                    'val_ids': val,
                    })

                if cur_id not in balance_by_cur:
                    balance_by_cur.update({cur_id : {
                             'inv_amt' : (total_amt1 + total_amt2 + total_amt3 + total_amt4),
                             'home_amt' : (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4),
                             'amt1' : total_amt1,
                             'amt2' : total_amt2,
                             'amt3' : total_amt3,
                             'amt4' : total_amt4,
                             'home_amt1' : total_home_amt1,
                             'home_amt2' : total_home_amt2,
                             'home_amt3' : total_home_amt3,
                             'home_amt4' : total_home_amt4,
                             }
                            })
                else:
                    res_currency_grouping = balance_by_cur[cur_id].copy()
                    res_currency_grouping['inv_amt'] += (total_amt1 + total_amt2 + total_amt3 + total_amt4)
                    res_currency_grouping['home_amt'] += (total_home_amt1 + total_home_amt2 + total_home_amt3 + total_home_amt4)
                    res_currency_grouping['amt1'] += total_amt1
                    res_currency_grouping['amt2'] += total_amt2
                    res_currency_grouping['amt3'] += total_amt3
                    res_currency_grouping['amt4'] += total_amt4
                    res_currency_grouping['home_amt1'] += total_home_amt1
                    res_currency_grouping['home_amt2'] += total_home_amt2
                    res_currency_grouping['home_amt3'] += total_home_amt3
                    res_currency_grouping['home_amt4'] += total_home_amt4
                    balance_by_cur[cur_id] = res_currency_grouping
                    
        results1 = results1 and sorted(results1, key=lambda val_res: val_res['part_name']) or []
        for rs1 in results1:
            header += '[' + str(rs1['part_ref'])  + '] ' + str(rs1['part_name']) + ';' + str(rs1['cur_name']) + ';' + 'Tel : ' + str(rs1['contact_phone']) + ';' + 'Contact : ' + str(rs1['contact_person']) \
                          + ';' + 'Credit Limit : ' + str(rs1['credit_limit'] or 0.00) + ' \n'
            total_home_amt = 0
            for rs2 in rs1['val_ids']:
                header += str(rs2['invoice_name']) + ';' + str(rs2['sales_person']) + ';' + str(rs2['invoice_date']) + ';' + str(rs2['due_date']) + ';' \
                          + str(rs2['ref_no']) + ';' + str(rs2['cust_po_no']) + ';' + str(rs2['orig_amt']) + ';' + str(rs2['home_orig_amt']) + ';' \
                          + str(rs2['paid_amt']) + ';' + str(rs2['home_paid_amt']) + ';' + str(rs2['amt1']) + ';' \
                          + str(rs2['home_amt1']) + ';' + str(rs2['amt2']) + ';' + str(rs2['home_amt2']) + ';' \
                          + str(rs2['amt3']) + ';' + str(rs2['home_amt3']) + ';' + str(rs2['amt4']) + ';' + str(rs2['home_amt4']) + ' \n'
            header += str('Total For : ' + rs1['part_ref']) + ';' + 'Oustanding Amount;< 31;31 To 60;61 To 90;Over 90' + ' \n'

            header += str(rs1['cur_name']) + ';' + str(rs1['total_inv']) + ';' \
                    + str(rs1['total_amt1']) + ';' + str(rs1['total_amt2']) + ';' \
                    + str(rs1['total_amt3']) + ';' + str(rs1['total_amt4']) + ' \n'
            header += 'Home;' + str(rs1['total_home']) + ';' \
                    + str(rs1['total_home_amt1']) + ';' + str(rs1['total_home_amt2']) + ';' \
                    + str(rs1['total_home_amt3']) + ';' + str(rs1['total_home_amt4']) + ' \n \n'
                    
        result_currency = []
        currency_obj    = self.pool.get('res.currency')
        for item in balance_by_cur.items():
            result_currency.append({
                'cur_name' : currency_obj.browse(cr, uid, item[0]).name,
                'total_inv' : item[1]['inv_amt'],
                'total_home' : item[1]['home_amt'],
                'amt1' : item[1]['amt1'],
                'amt2' : item[1]['amt2'],
                'amt3' : item[1]['amt3'],
                'amt4' : item[1]['amt4'],
                'home_amt1' : item[1]['home_amt1'],
                'home_amt2' : item[1]['home_amt2'],
                'home_amt3' : item[1]['home_amt3'],
                'home_amt4' : item[1]['home_amt4'],
            })
            
        result_currency = result_currency and sorted(result_currency, key=lambda val_res: val_res['cur_name']) or []
        _total_home = 0
        _total_amt1 = _total_amt2 = _total_amt3 = _total_amt4 = 0.00
        header += 'Report Total By Currency;Oustanding Amount;< 31;31 To 60;61 To 90;Over 90' + ' \n'
        for rs_curr in result_currency:
            _total_home += rs_curr['total_home'] or 0
            _total_amt1 += rs_curr['home_amt1'] or 0.00
            _total_amt2 += rs_curr['home_amt2'] or 0.00
            _total_amt3 += rs_curr['home_amt3'] or 0.00
            _total_amt4 += rs_curr['home_amt4'] or 0.00
            
            header += str(rs_curr['cur_name']) + ';' + str(rs_curr['total_inv']) + ';' + str(rs_curr['amt1']) + ';' \
                    + str(rs_curr['amt2']) + ';' + str(rs_curr['amt3']) + ';' + str(rs_curr['amt4']) + ' \n'
            
            header += 'Home' + ';' + str(rs_curr['total_home']) + ';' + str(rs_curr['home_amt1']) + ';' + str(rs_curr['home_amt2']) + ';' \
                    + str(rs_curr['home_amt3']) + ';' + str(rs_curr['home_amt4']) + ' \n'
                    
        header += 'Total Home' + ';' + str(_total_home) + ';' + str(_total_amt1) + ';' + str(_total_amt2) + ';' + str(_total_amt3) + ';' \
                + str(_total_amt4) + ' \n'
        
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        if type == 'payable':
            filename = 'Payable Aging Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.payable.aging.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','payable_aging_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Payable Aging Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.payable.aging.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
        elif type == 'receivable':
            filename = 'Receivable Aging Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.receivable.aging.report').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','receivable_aging_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Receivable Aging Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.receivable.aging.report',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
    def generate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.payable.aging.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.aging.report_landscape',
            'datas': datas,
        }

param_payable_aging_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
