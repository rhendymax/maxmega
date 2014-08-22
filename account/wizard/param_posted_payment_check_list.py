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

class param_posted_payment_check_list(osv.osv_memory):
    _name = 'param.posted.payment.check.list'
    _description = 'Param Posted Payment Check List'
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'supplier_search_vals': fields.selection([('code','Supplier Code'),('name', 'Supplier Name')],'Supplier Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supp Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Supplier From', domain=[('supplier','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Supplier To', domain=[('supplier','=',True)], required=False),
        'partner_input_from': fields.char('Supplier From', size=128),
        'partner_input_to': fields.char('Supplier To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_payment_supplier_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'journal_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Bank Filter Selection', required=True),
        'journal_default_from':fields.many2one('account.journal', 'Bank From', domain=[('type','in',('bank','cash'))], required=False),
        'journal_default_to':fields.many2one('account.journal', 'Bank To', domain=[('type','in',('bank','cash'))], required=False),
        'journal_input_from': fields.char('Bank From', size=128),
        'journal_input_to': fields.char('Bank To', size=128),
        'journal_ids' :fields.many2many('account.journal', 'report_payment_journal_rel', 'report_id', 'journal_id', 'Bank', domain=[('type','in',('bank', 'cash'))]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'report_type' : 'payable',
        'date_selection': 'none_sel',
        'supp_selection': 'all',
        'supplier_search_vals': 'code',
        'filter_selection': 'all_vall',
        'journal_selection': 'all_vall',
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

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.posted.payment.check.list'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.payment.report_landscape',
            'datas': datas,
            'nodestroy':True,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
                                                'journal_selection','journal_default_from','journal_default_to', 'journal_input_from','journal_input_to','journal_ids' \
                                                ], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
                                                'journal_selection','journal_default_from','journal_default_to', 'journal_input_from','journal_input_to','journal_ids'\
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
                    data_found = True
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
                    qry = self.cr.dictfetchone()
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

#journal
        qry_jour = "type in ('bank', 'cash')"
        val_jour.append(('type', 'in', ('bank', 'cash')))

        journal_default_from = data['form']['journal_default_from'] or False
        journal_default_to = data['form']['journal_default_to'] or False
        journal_input_from = data['form']['journal_input_from'] or False
        journal_input_to = data['form']['journal_input_to'] or False
        journal_default_from_str = journal_default_to_str = ''
        journal_input_from_str = journal_input_to_str= ''

        if data['form']['journal_selection'] == 'all_vall':
            journal_ids = account_journal_obj.search(cr, uid, val_jour, order='name ASC')
        if data['form']['journal_selection'] == 'def':
            data_found = False
            if journal_default_from and account_journal_obj.browse(cr, uid, journal_default_from) and account_journal_obj.browse(cr, uid, journal_default_from).name:
                journal_default_from_str = account_journal_obj.browse(cr, uid, journal_default_from).name
                data_found = True
                val_jour.append(('name', '>=', account_journal_obj.browse(cr, uid, journal_default_from).name))
            if journal_default_to and account_journal_obj.browse(cr, uid, journal_default_to) and account_journal_obj.browse(cr, uid, journal_default_to).name:
                journal_default_to_str = account_journal_obj.browse(cr, uid, journal_default_to).name
                data_found = True
                val_jour.append(('name', '<=', account_journal_obj.browse(cr, uid, journal_default_to).name))
            if data_found:
                result['journal_selection'] = '"' + journal_default_from_str + '" - "' + journal_default_to_str + '"'
                journal_ids = account_journal_obj.search(cr, uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'input':
            data_found = False
            if journal_input_from:
                cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    journal_input_from_str = journal_input_from
                    data_found = True
                    val_jour.append(('name', '>=', qry['name']))
            if journal_input_to:
                cr.execute("select name " \
                                "from account_journal "\
                                "where " + qry_jour + " and " \
                                "name ilike '" + str(journal_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    journal_input_to_str = journal_input_to
                    data_found = True
                    val_jour.append(('name', '<=', qry['name']))
            #print val_part
            if data_found:
                result['journal_selection'] = '"' + journal_input_from_str + '" - "' + journal_input_to_str + '"'
                journal_ids = account_journal_obj.search(cr, uid, val_jour, order='name ASC')
        elif data['form']['journal_selection'] == 'selection':
            j_ids = ''
            if data['form']['journal_ids']:
                for jo in  account_journal_obj.browse(cr, uid, data['form']['journal_ids']):
                    j_ids += '"' + str(jo.name) + '",'
                journal_ids = data['form']['journal_ids']
            result['journal_selection'] = '[' + j_ids +']'
        result['journal_ids'] = journal_ids
        return result

    def _get_tplines(self, cr, uid, ids,data, type, context):

        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        period_obj      = self.pool.get('account.period')
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        balance_by_cur = {}
        results = []
#                RT 201405288
        payment_count = 0.00
        footer_cheque_home = 0.00
        footer_gain_loss_home = 0.00
        footer_alloc_inv_home = 0.00
        footer_bank_charges_home = 0.00
        footer_deposit_home = 0.00
        footer_credit_note_home =0.00


        qry_type = ''

        partner_ids = form['partner_ids'] or False
        print partner_ids
        journal_ids = form['journal_ids'] or False
        
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
            qry_type = "and l.type in ('payment') "
            header += 'Posted Payment Check List' + " \n"
            header += 'Supplier : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Supplier search : ' + form['filter_selection'] + " \n") or ''
        elif type == 'receivable':
            qry_type = "and l.type in ('receipt') "
            header += 'Posted Receipt Check List' + " \n"
            header += 'Customer : ' + supp_selection + " (" + data_search + "); \n"
            header += ('filter_selection' in form and 'Customer search : ' + form['filter_selection'] + " \n") or ''

        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += ('journal_selection' in form and 'Bank : ' + str(form['journal_selection']) + "\n") or ''

        header += 'Voucher No;Credit Note No;Date;Currency Date;Cheque Home;Credit Note Amt;Credit Note Home;Alloc Inv Amt;Alloc Inv Home;Alloc Realized Ex' + " \n"

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
        journal_ids = form['journal_ids'] or False
        journal_qry = (journal_ids and ((len(journal_ids) == 1 and "AND l.journal_id = " + str(journal_ids[0]) + " ") or "AND l.journal_id IN " + str(tuple(journal_ids)) + " ")) or "AND l.journal_id IN (0) "
        cr.execute(
                "SELECT l.id as voucher_id, l.partner_id " \
                "FROM account_voucher AS l " \
                "WHERE l.partner_id IS NOT NULL " \
                "AND l.state IN ('posted') " \
                + qry_type \
                + partner_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry \
                + journal_qry + \
                "order by l.date")
        qry3 = cr.dictfetchall()
        cheque = cheque_home = bank_charges = bank_charges_home = deposit = deposit_home = credit_note = credit_note_home = alloc_inv = alloc_inv_home = 0.00
        if qry3:
            for t in qry3:
                inv = voucher_obj.browse(cr, uid, t['voucher_id'])
                res = {}
                lines_ids = []
                amount_all = 0.00
                amount_home_all = 0.00
                gain_loss_all = 0.00
                credit_inv_amt_credit = 0.00
                credit_inv_home_credit = 0.00
    
                alloc_inv_amt_debit = 0.00
                alloc_inv_home_debit = 0.00
                
                reconcile_title_amt = False
                reconcile_title_home = False

                if inv.payment_option == 'without_writeoff':
                    reconcile_title_amt = 'Deposit Amt : '
                    reconcile_title_home = 'Deposit Home : '
                if inv.payment_option == 'with_writeoff':
                    reconcile_title_amt = 'Reconcile Amt : '
                    reconcile_title_home = 'Reconcile Home : '
                
                if type == 'payable':
                    for lines in inv.line_dr_ids:
                        if lines.amount > 0:
                            amount_all += lines.amount
                            alloc_inv_amt_debit += lines.amount
                            amount_home_all += lines.amount_home or 0.00
                            alloc_inv_home_debit += lines.amount_inv_home or 0.00
        
                            #count Gain Loss
                            amount_home = lines.amount_home or 0.00
                            amount_inv_home = lines.amount_inv_home or 0.00
                            gain_loss = (amount_inv_home - amount_home) or 0.00
                            gain_loss_all += gain_loss
                            #
                    for lines in inv.line_cr_ids:
                        if lines.amount > 0:
                            sign = -1
                            amount_all -= lines.amount
                            credit_inv_amt_credit += (sign * lines.amount)
                            amount_home_all -= lines.amount_home or 0.00
                            credit_inv_home_credit += (sign * (lines.amount_inv_home or 0.00) or 0.00)
                            #count Gain Loss
                            amount_home = lines.amount_home or 0.00
                            amount_inv_home = lines.amount_inv_home or 0.00
                            gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
                            gain_loss_all -= gain_loss
                elif type == 'receivable':
                    for lines in inv.line_cr_ids:
                        if lines.amount > 0:
                            amount_all += lines.amount
                            alloc_inv_amt_debit += lines.amount
                            amount_home_all += lines.amount_home or 0.00
                            alloc_inv_home_debit += lines.amount_inv_home or 0.00
        
                            #count Gain Loss
                            amount_home = lines.amount_home or 0.00
                            amount_inv_home = lines.amount_inv_home or 0.00
                            gain_loss = (amount_inv_home - amount_home) or 0.00
                            gain_loss_all += gain_loss
                            #
                    for lines in inv.line_dr_ids:
                        if lines.amount > 0:
                            sign = -1
                            amount_all -= lines.amount
                            credit_inv_amt_credit += (sign * lines.amount)
                            amount_home_all -= lines.amount_home or 0.00
                            credit_inv_home_credit += (sign * (lines.amount_inv_home or 0.00) or 0.00)
                            #count Gain Loss
                            amount_home = lines.amount_home or 0.00
                            amount_inv_home = lines.amount_inv_home or 0.00
                            gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
                            gain_loss_all -= gain_loss
                payment_count += 1
                res['voucher_no'] = inv.number
                res['supp_ref'] = inv.partner_id and inv.partner_id.ref or ''
                res['supp_name'] = inv.partner_id and inv.partner_id.name or ''
                res['ex_glan'] = inv.company_id and inv.company_id.property_currency_gain_loss and  inv.company_id.property_currency_gain_loss.code or ''
                res['cheque_no'] = inv.cheque_no or ''
                res['curr_name'] = inv.journal_id and inv.journal_id.currency and inv.journal_id.currency.name or inv.company_id and inv.company_id.currency_id and inv.company_id.currency_id.name or ''
                res['cheque_date'] = inv.date or False
                res['bank_glan'] = inv.journal_id and inv.journal_id.property_bank_charges and inv.journal_id.property_bank_charges.code or ''
                ctx = {'date':inv.date}
                res['cur_exrate'] = self.pool.get('res.currency').browse(cr, uid, inv.journal_id and inv.journal_id.currency and inv.journal_id.currency.id or inv.company_id and inv.company_id.currency_id and inv.company_id.currency_id.id, context=ctx).rate or 0.00
#                res['cheq_amount'] = amount_all
#                cheque = amount_all
#                res['cheq_amount_home'] = amount_home_all
#                cheque_home = amount_home_all
                res['cheq_amount'] = inv.amount
                cheque = inv.amount
                res['cheq_amount_home'] = inv.total_in_home_currency
                cheque_home = inv.total_in_home_currency
                footer_cheque_home += amount_home_all
                footer_gain_loss_home += gain_loss_all
                res['credit_inv_amt'] = credit_inv_amt_credit
                credit_note = credit_inv_amt_credit
                res['credit_inv_home'] = credit_inv_home_credit
                credit_note_home = credit_inv_home_credit
                footer_credit_note_home += credit_inv_home_credit
                res['alloc_inv_amt'] = alloc_inv_amt_debit
                alloc_inv = alloc_inv_amt_debit
                res['alloc_inv_home'] = alloc_inv_home_debit
                alloc_inv_home = alloc_inv_home_debit
                footer_alloc_inv_home += alloc_inv_home_debit
                res['bank_draft'] = inv.bank_draft_no or ''
                res['bank_chrgs'] = inv.bank_charges_amount or 0.00
                bank_charges = inv.bank_charges_amount or 0.00
                res['bank_chrgs_home'] = inv.bank_charges_in_company_currency or 0.00
                bank_charges_home = inv.bank_charges_in_company_currency or 0.00
                footer_bank_charges_home += inv.bank_charges_in_company_currency or 0.00
                res['deposit_amt'] = inv.writeoff_amount or 0.00
                res['deposit_amt_home'] = inv.writeoff_amount_home or 0.00
                res['reconcile_title_amt'] = reconcile_title_amt
                res['reconcile_title_home'] = reconcile_title_home
                footer_deposit_home += inv.writeoff_amount_home or 0.00
                res['lines'] = lines_ids
                
                header += 'P/V No. : ' + str(res['voucher_no'] or '') + ";Realized Ex GLAN : " + str(res['ex_glan'] or '') + ";Cheque No. : " + str(res['cheque_no'] or '') + \
                ';Bank Currency Key : ' + str(res['curr_name'] or '') + " \n" 
                
                header +=  (type == 'payable' and 'Supplier' or 'Customer') + ' : ' + str(res['supp_ref'] or '') + ';Currency : ' + str(res['curr_name'] or '') + ";Cheque Date : " + str(res['cheque_date'] or '') + \
                ';Bank Chrgs GLAN : ' + str(res['bank_glan'] or '') + " \n"
                
                header += str(res['supp_name'] or '') + ';Ex Rate : ' + str("%.5f" % res['cur_exrate'] or 0.00000) + ";Cheque Amt : " + str("%.2f" % res['cheq_amount'] or 0.00) + \
                ';Bank Draft No.;' + str(res['bank_draft']) + " \n" 

                if reconcile_title_amt:
                    header += str(reconcile_title_amt) + str("%.2f" % res['deposit_amt'] or 0.00) + ";Cheque Home : " + str("%.2f" % res['cheq_amount_home'] or 0.00) + \
                    ';Bank chrgs Amt : ' + str("%.2f" % res['bank_chrgs'] or 0.00) + "; \n"
                    header += str(reconcile_title_home) + str("%.2f" % res['deposit_amt_home'] or 0.00) + ';Bank chrgs Home : ' + str("%.2f" % res['bank_chrgs'] or  0.00) + "; \n"

                else:
                    header += ";Cheque Home : " + str("%.2f" % res['cheq_amount_home'] or 0.00) + \
                    ';Bank chrgs Amt : ' + str("%.2f" % res['bank_chrgs'] or 0.00) + "; \n"
                    header += ';Bank chrgs Home : ' + str("%.2f" % res['bank_chrgs'] or  0.00) + "; \n"

                
                cur_name = 'False'
                if type == 'payable':
                    #20140716
                    cur_name = res_partner_obj.browse(cr, uid, t['partner_id']).property_product_pricelist_purchase.currency_id.name
                    cur_id = res_partner_obj.browse(cr, uid, t['partner_id']).property_product_pricelist_purchase.currency_id.id
                    for lines in inv.line_dr_ids:
                        if lines.amount > 0:
                            amount_inv_home = lines.amount_inv_home or 0.00
                            amount_home = lines.amount_home or 0.00
                            gain_loss = amount_inv_home - amount_home or 0.00
                            header += str(lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '') + ";" + \
                                      ";" + \
                                      str(lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str("%.2f" % (lines.amount_home or 0.00)) + ";" + \
                                      ";" + \
                                      ";" + \
                                      str("%.2f" % (lines.amount or 0.00)) + ";" + \
                                      str("%.2f" % (lines.amount_inv_home or 0.00)) + ";" + \
                                      str("%.2f" % (((lines.amount_inv_home or 0.00) - (lines.amount_home or 0.00)) or 0.00)) + " \n"
    
                    for lines in inv.line_cr_ids:
                        if lines.amount > 0:
                            sign = -1
                            amount_inv_home = lines.amount_inv_home or 0.00
                            amount_home = lines.amount_home or 0.00
                            gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
                            header += ";" + \
                                      str(lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str("%.2f" % ((sign * lines.amount_home) or 0.00)) + ";" + \
                                      str("%.2f" % ((sign * lines.amount) or 0.00)) + ";" + \
                                      str("%.2f" % ((sign * lines.amount_inv_home) or 0.00)) + ";" + \
                                      ";" + \
                                      ";" + \
                                      str("%.2f" % (gain_loss))+ " \n"
                elif type == 'receivable':
                    #20140716
                    cur_name = res_partner_obj.browse(cr, uid, t['partner_id']).property_product_pricelist.currency_id.name
                    cur_id = res_partner_obj.browse(cr, uid, t['partner_id']).property_product_pricelist.currency_id.id
                    for lines in inv.line_cr_ids:
                        if lines.amount > 0:
                            amount_inv_home = lines.amount_inv_home or 0.00
                            amount_home = lines.amount_home or 0.00
                            gain_loss = amount_inv_home - amount_home or 0.00
                            header += str(lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '') + ";" + \
                                      ";" + \
                                      str(lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str("%.2f" % (lines.amount_home or 0.00)) + ";" + \
                                      ";" + \
                                      ";" + \
                                      str("%.2f" % (lines.amount or 0.00)) + ";" + \
                                      str("%.2f" % (lines.amount_inv_home or 0.00)) + ";" + \
                                      str("%.2f" % (((lines.amount_inv_home or 0.00) - (lines.amount_home or 0.00)) or 0.00)) + " \n"
    
                    for lines in inv.line_dr_ids:
                        if lines.amount > 0:
                            sign = -1
                            amount_inv_home = lines.amount_inv_home or 0.00
                            amount_home = lines.amount_home or 0.00
                            gain_loss = (sign * (amount_inv_home - amount_home)) or 0.00
                            header += ";" + \
                                      str(lines.move_line_id and lines.move_line_id.move_id and lines.move_line_id.move_id.name or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str(lines.move_line_id and lines.move_line_id.cur_date or lines.move_line_id and lines.move_line_id.date or '') + ";" + \
                                      str("%.2f" % ((sign * lines.amount_home) or 0.00)) + ";" + \
                                      str("%.2f" % ((sign * lines.amount) or 0.00)) + ";" + \
                                      str("%.2f" % ((sign * lines.amount_inv_home) or 0.00)) + ";" + \
                                      ";" + \
                                      ";" + \
                                      str("%.2f" % (gain_loss))+ " \n"
                #RT 20140716
                if cur_id not in balance_by_cur:
                    balance_by_cur.update({cur_id : {
                             'cheque' : cheque,
                             'cheque_home' : cheque_home,
                             'bank_charges' : bank_charges,
                             'bank_charges_home' : bank_charges_home,
                             'deposit' : deposit,
                             'deposit_home' : deposit_home,
                             'credit_note' : credit_note,
                             'credit_note_home' : credit_note_home,
                             'alloc_inv' : alloc_inv,
                             'alloc_inv_home' : alloc_inv_home,
                             }
                        })
                else:
                    res_currency_grouping = balance_by_cur[cur_id].copy()
                    res_currency_grouping['cheque'] += cheque
                    res_currency_grouping['cheque_home'] += cheque_home
                    res_currency_grouping['bank_charges'] += bank_charges_home
                    res_currency_grouping['bank_charges_home'] += bank_charges_home
                    res_currency_grouping['deposit'] += deposit
                    res_currency_grouping['deposit_home'] += deposit_home
                    res_currency_grouping['credit_note'] += credit_note
                    res_currency_grouping['credit_note_home'] += credit_note_home
                    res_currency_grouping['alloc_inv'] += alloc_inv
                    res_currency_grouping['alloc_inv_home'] += alloc_inv_home

                    balance_by_cur[cur_id] = res_currency_grouping
                    
                header += 'Total for ' + str(inv.number) + \
                        ';' + ';' + ';' + ';' + str("%.2f" % res['cheq_amount_home']) + ';' + \
                        str("%.2f" % res['credit_inv_amt']) + ';' + \
                        str("%.2f" % res['credit_inv_home']) + ';' + \
                        str("%.2f" % res['alloc_inv_amt']) + ';' + \
                        str("%.2f" % res['alloc_inv_home']) + ';' + \
                        str("%.2f" % gain_loss_all) + ';' + ' \n' + '\n' + ' \n'
#        header += 'Report Total' + ' \n'
#        header += 'No. of Payment Vouchers : ' + str(payment_count or '') + ';' + 'Credit Note Home : ' + str("%.2f" % footer_credit_note_home or 0.00) + ' \n'
#        header += 'Cheque Home : ' + str("%.2f" % footer_cheque_home or 0.00)+ ';' + 'Alloc Inv Home : ' + str("%.2f" %  footer_alloc_inv_home or 0.00) + ' \n'
#        header += 'Bank Charges Home : ' + str("%.2f" % footer_bank_charges_home or 0.00) + ';' + 'Alloc Realize Ex : ' + str("%.2f" % footer_gain_loss_home or 0.00) + ' \n'
#        header += 'Deposit Home : ' + str("%.2f" % footer_deposit_home or 0.00) + ' \n \n'
        
        result_currency = []
        currency_obj    = self.pool.get('res.currency')
        for item in balance_by_cur.items():
            result_currency.append({
                'cur_name' : currency_obj.browse(cr, uid, item[0]).name,
                'cheque' : item[1]['cheque'],
                'cheque_home' : item[1]['cheque_home'],
                'bank_charges' : item[1]['bank_charges'],
                'bank_charges_home' : item[1]['bank_charges_home'],
                'deposit' : item[1]['deposit'],
                'deposit_home' : item[1]['deposit_home'],
                'credit_note' : item[1]['credit_note'],
                'credit_note_home' : item[1]['credit_note_home'],
                'alloc_inv' : item[1]['alloc_inv'],
                'alloc_inv_home' : item[1]['alloc_inv_home'],
            })
        total_home = total_bank_charges_home =  total_deposit_home = total_credit_note_home = total_alloc_inv_home = 0
        result_currency = result_currency and sorted(result_currency, key=lambda val_res: val_res['cur_name']) or []
        header += 'Currency ' + ';' + 'Cheque' + ';' + 'Bank Charges' + ';' + 'Deposit' + ';' + 'Credit Note' + ';' + 'Alloc Inv' + ';' + ' \n'
        for rs_curr in result_currency:
            total_home += rs_curr['cheque_home'] or 0.00
            total_bank_charges_home += rs_curr['bank_charges_home'] or 0.00
            total_deposit_home += rs_curr['deposit_home'] or 0.00
            total_credit_note_home += rs_curr['credit_note_home'] or 0.00
            total_alloc_inv_home += rs_curr['alloc_inv_home'] or 0.00
            header += str(rs_curr['cur_name']) + ' Home;' + str(rs_curr['cheque_home']) + ';' + str(rs_curr['bank_charges_home']) + \
                        ';' + str(rs_curr['deposit_home']) + ';' + str(rs_curr['credit_note_home']) + ';' + str(rs_curr['alloc_inv_home']) + ' \n'
            header += str(rs_curr['cur_name']) + ';' + str(rs_curr['cheque']) + ';' + str(rs_curr['bank_charges']) + \
                        ';' + str(rs_curr['deposit']) + ';' + str(rs_curr['credit_note']) + ';' + str(rs_curr['alloc_inv']) + ';' + str(rs_curr['alloc_inv']) + ' \n'
        header += ' \n' + 'Total Home:' + ';' + str("%.2f" % total_home) + \
                  ';' + str("%.2f" % total_bank_charges_home) + ';' + str("%.2f" % total_deposit_home) + ';' + str("%.2f" % total_credit_note_home) + ';' + str("%.2f" % total_alloc_inv_home) + ' \n \n'
        
        header += 'Alloc Realize Ex :' + ';' + str("%.2f" % footer_gain_loss_home or 0.00) + ' \n'
        header += 'No. of Payment Vouchers :' + ';' + str("%.2f" % payment_count or '') + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        if type == 'payable':
            filename = 'Posted Payment Check List Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.posted.payment.check.list').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','posted_payment_check_list_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Posted Payment Check List Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.posted.payment.check.list',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
        elif type == 'receivable':
            filename = 'Posted Receipt Check List Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.posted.receipt.check.list').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','posted_receipt_check_list_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Posted Receipt Check List Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.posted.receipt.check.list',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }

        

param_posted_payment_check_list()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
