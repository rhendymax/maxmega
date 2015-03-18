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

class param_payment_register_by_deposit_bank(osv.osv_memory):
    _name = 'param.payment.register.by.deposit.bank'
    _description = 'Param Payment Register By Deposit Bank'
    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
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
        'journal_ids' :fields.many2many('account.journal', 'report_payment_deposit_bank_rel', 'report_id', 'journal_id', 'Bank', domain=[('type','in',('bank', 'cash'))]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'report_type' : 'payable',
        'date_selection': 'none_sel',
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

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.payment.register.by.deposit.bank'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.payment.register.report_landscape',
            'datas': datas,
            'nodestroy':True,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
                                                'journal_selection','journal_default_from','journal_default_to', 'journal_input_from','journal_input_to','journal_ids' \
                                                ], context=context)[0]
        for field in ['date_selection', 'date_from', 'date_to','period_filter_selection','period_default_from','period_default_to','period_input_from','period_input_to', \
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
        account_journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        qry_jour = ''
        val_jour = []
        journal_ids = False
        
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
        voucher_obj = self.pool.get('account.voucher')
        results = []
#                RT 201405288
        qry_type = ''
        journal_ids = form['journal_ids'] or False

        date_from = form['date_from']
        date_to = form['date_to']

        date_from_qry = date_from and "And l.date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And l.date <= '" + str(date_to) + "' " or " "

        period_ids = form['period_ids'] or False
        min_period = False

        all_content_line = ''
        header = 'sep=;' + " \n"

        if type == 'payable':
            qry_type = "and l.type in ('payment') "
            header += 'Payment Register By Deposit Bank Report' + " \n"
        elif type == 'receivable':
            qry_type = "and l.type in ('receipt') "
            header += 'Receipt Register By Deposit Bank Report' + " \n"

        header += ('date_search' in form and (form['date_search'] == 'date' and 'Date : ' + str(form['date_showing']) + " \n") or \
                   (form['date_search'] == 'period' and 'Period : ' + str(form['date_showing']) + " \n")) or ''

        header += ('journal_selection' in form and 'Bank : ' + str(form['journal_selection']) + "\n") or ''
        if type == 'payable':
            header += 'Payment No;Cheque Date;Cheque No;Cheque Amt;Cheque Home Amt;Supplier;Supplier Name;Ccy;Exch Rate;Bank Draft;Charges;Charges Home' + " \n"
        elif type == 'receivable':
            header += 'Receipt No;Cheque Date;Cheque No;Cheque Amt;Cheque Home Amt;Customer;Customer Name;Ccy;Exch Rate;Bank Draft;Charges;Charges Home' + " \n"
             
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
                "SELECT DISTINCT l.journal_id " \
                "FROM account_voucher AS l " \
                "WHERE l.journal_id IS NOT NULL " \
                "AND l.state IN ('posted') " \
                + qry_type \
                + journal_qry \
                + date_from_qry \
                + date_to_qry \
                + period_qry)
        journal_ids_vals = []
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                journal_ids_vals.append(r['journal_id'])
        
        journal_ids_vals_qry = (len(journal_ids_vals) > 0 and ((len(journal_ids_vals) == 1 and "where id = " +  str(journal_ids_vals[0]) + " ") or "where id IN " +  str(tuple(journal_ids_vals)) + " ")) or "where id IN (0) "
        cr.execute(
                "SELECT id, code, name " \
                "FROM account_journal " \
                + journal_ids_vals_qry \
                + " order by code")
        qry = cr.dictfetchall()
        
        if qry:
            gt_amt = gt_amt_home = gt_charges = gt_charge_home = 0.00
            for s in qry:
                header += '[' + str(s['code'] or '') + '] ' + str(s['name'] or '') + ' \n'
                cr.execute(
                        "SELECT l.id as voucher_id " \
                        "FROM account_voucher AS l " \
                        "WHERE l.journal_id IS NOT NULL " \
                        "AND l.state IN ('posted') " \
                        + qry_type \
                        + date_from_qry \
                        + date_to_qry \
                        + period_qry + \
                        "and l.journal_id = " + str(s['id']) + " "\
                        "order by l.date")
                qry3 = cr.dictfetchall()
                if qry3:
                    t_amt = t_amt_home = t_charges = t_charge_home = 0.00
                    for t in qry3:
                        voucher = voucher_obj.browse(cr, uid, t['voucher_id'])
                        t_amt += voucher.grand_total or 0.00
                        t_amt_home += (voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00) or 0.00
                        t_charges += voucher.bank_charges_amount or 0.00
                        t_charge_home += (voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00)  or 0.00
                        gt_amt += voucher.grand_total or 0.00
                        gt_amt_home += (voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00) or 0.00
                        gt_charges += voucher.bank_charges_amount or 0.00
                        gt_charge_home += (voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00)  or 0.00
                        header += str(voucher.number or '') + ';' + str(voucher.date or '') + ';' + str(voucher.reference or '') + ';' \
                                + str(voucher.grand_total or 0.00) + ';' + str((voucher.grand_total or 0.00) * (voucher.ex_rate or 0.00)) + ';' + str(voucher.partner_id and voucher.partner_id.ref or '') + ';' \
                                + str(voucher.partner_id and voucher.partner_id.name or '') + ';' + str(voucher.currency_id and voucher.currency_id.name or '') + ';' \
                                + str(voucher.ex_rate or 0.00) + ';' + str(voucher.bank_draft_no or '') + ';' + str(voucher.bank_charges_amount or 0.00) + ';' \
                                + str((voucher.bank_charges_amount or 0.00) * (voucher.ex_rate or 0.00)) + ' \n'
                    header += 'Total For : ' + str(voucher.number or '') + ';;;' + str(t_amt) + ';' + str(t_amt_home) + ';;;;;;' + str(t_charges) + ';' +str(t_charge_home) +'\n \n'
            header += 'Report Total :' + ';;;' + str(gt_amt) + ';' + str(gt_amt_home) + ';;;;;;' + str(gt_charges) + ';' + str(gt_charge_home) + ' \n'
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        if type == 'payable':
            filename = 'Payment Register By Deposit Bank Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.payment.register.by.deposit.bank').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','payment_register_by_deposit_bank_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Payment Register By Deposit Bank Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.payment.register.by.deposit.bank',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }
        elif type == 'receivable':
            filename = 'Receipt Register By Deposit Bank Report.csv'
            out = base64.encodestring(all_content_line)
            self.pool.get('param.receipt.register.by.deposit.bank').write(cr, uid, ids,{'data':out, 'filename':filename})
            obj_model = self.pool.get('ir.model.data')
            model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','receipt_register_by_deposit_bank_result_csv_view')])
            resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
            return {
                    'name':'Receipt Register By Deposit Bank Report',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'param.receipt.register.by.deposit.bank',
                    'views': [(resource_id,'form')],
                    'type': 'ir.actions.act_window',
                    'target':'new',
                    'res_id':ids[0],
                    }

        

param_payment_register_by_deposit_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
