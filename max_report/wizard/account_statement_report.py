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
from tools.translate import _
import time
from datetime import datetime
from mx import DateTime as dt
from mx.DateTime import RelativeDateTime as rdt
from datetime import timedelta
import pooler
import base64

class account_statement_report(osv.osv_memory):
    _name = "account.statement.report"
    _description = "Statement of Account"
    
    def _get_period(self, cr, uid, context=None):
        period_obj  = self.pool.get('account.period')
        date_now    = time.strftime('%Y-%m-%d')
        period_ids  = period_obj.search(cr, uid, [('date_stop','>=',date_now)], order="date_stop ASC")
        period_id   = False
        if period_ids:
            period_id = period_ids[0]
        return period_id

    _columns = {
        'period_id'     : fields.many2one('account.period', 'Period', domain=[('state', '=','draft')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }
    _defaults = {
        'period_id'     : _get_period,
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas           = {'ids': context.get('active_ids')}
        datas['model']  = 'account.statement.report'
        datas['form']   = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.account.statement',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        print data
        partner_ids = ('ids' in data and data['ids']) or False
        model = ('model' in data and data['model']) or False
        period_id = data['form']['period_id'] or False
        
        if period_id:
            result['period_id'] = period_id
        if partner_ids:
            result['partner_ids'] = partner_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['period_id'], context=context)[0]
        
        for field in ['period_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_tplines(self, cr, uid, ids, data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        res_obj = self.pool.get('res.partner')
        invoice_obj     = self.pool.get('account.invoice')
        sale_payment_term_obj     = self.pool.get('sale.payment.term')
        period_obj = self.pool.get('account.period')
        
        period_id = form['period_id'] or False
        period = self.pool.get('account.period').browse(cr, uid, period_id)
        company = self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id))
        partner_ids = form['partner_ids'] or False
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Statement Of Account' + " \n"
        if partner_ids:
            for partner in  res_obj.browse(cr, uid, partner_ids):
#                 partner_ref = (partner.ref and str(partner.ref) + '\n') or ''
                name = (partner.name and str(partner.name) + '\n') or ''
                street = (partner.address and partner.address[0].street and str(partner.address[0].street) + '\n') or ''
                street2 = (partner.address and partner.address[0].street2 and str(partner.address[0].street2) + '\n') or ''
                zip = (partner.address and partner.address[0].zip and str(partner.address[0].zip + ' ' + partner.address[0].city and str(partner.address[0].city)) + '\n') or ''
                country = (partner.address and partner.address[0].country_id and partner.address[0].country_id.name and str(partner.address[0].country_id.name) + '\n') or ''

#                 print partner.address and partner.address[0].street2
#                 print str(partner.address[0].street2)
                header += str(partner.ref or '') + ';;;;;' + str((partner.sale_term_id and partner.sale_term_id.name) or '') + '\n' \
                          + name + street + street2 + zip + country
                header += 'Statement As At : ' + str((period and period.date_stop) or '') + ';;;' + 'Deposit : ' + str(partner.depo_credit - partner.depo_debit) \
                        + ';' + 'Currency : ' + (str(company.currency_id.name + company.currency_id.symbol) or '') + ' \n'
                header += 'Invoice / Deposit No.' + ';' + 'TP' + ';' + 'Cust PO No' + ';' + 'Invoice Date' + ';' + 'Due Date' + ';' + 'Debit' + ';' + 'Credit' + '\n'
                sign = 1
                max_period = period.id or False
                date_to = max_period and period_obj.browse(cr, uid, max_period).date_stop or False
                period_1 = period_2 = period_3 = False
                date_start_max_period = max_period and period_obj.browse(cr, uid, max_period).date_start or False
                val_period = []
                val_period.append(('special', '=', False))
                if date_start_max_period:
                    val_period.append(('date_start', '<=', date_start_max_period))
        
                qry_period_ids = period_obj.search(cr, uid, val_period, order='date_start DESC')
                if qry_period_ids[1]:
                    period_1 = qry_period_ids[1]
                    print qry_period_ids[1]
                if qry_period_ids[2]:
                    period_2 = qry_period_ids[2]
                    print qry_period_ids[2]
                if qry_period_ids[3]:
                    period_3 = qry_period_ids[3]
                    print qry_period_ids[3]
        
                if date_to:
                    cr.execute(
                            "select aml.is_depo as deposit, ai.id as invoice_id, aml.period_id as period_id, sp.id as picking_id, ai.sale_term_id as term_id, aml.id as aml_id, am.name as inv_name, aml.date as inv_date, ai.ref_no as inv_ref, rs.name as sales_name, aml.debit - aml.credit as home_amt, " \
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
                            "and aa.type = 'receivable' " \
                            "And not (aml.debit > 0 and aml.is_depo = False and aj.type in ('cash', 'bank')) " \
                            "and abs((aml.debit - aml.credit) - (abs(coalesce ( " \
                            "(select sum(aml2.debit - aml2.credit) from account_move_line aml2 where aml2.reconcile_partial_id = aml.reconcile_partial_id and aml2.id != aml.id and aml2.date  <= '" +str(date_to) + "'), " \
                            "(select sum(aml3.debit - aml3.credit) from account_move_line aml3 where aml3.reconcile_id = aml.reconcile_id and aml3.id != aml.id and aml3.date  <= '" +str(date_to) + "'), 0 " \
                            ")) * (CASE WHEN (debit - credit) > 0 THEN 1 ELSE -1 END))) > 0 " \
                            "And aml.date  <= '" +str(date_to) + "' "\
                            "and not (aj.type in ('bank', 'cash') and aml.is_depo = False) " \
                            "and aml.partner_id = " + str(partner.id) + " order by aml.date")
                    qry3 = cr.dictfetchall()
                    val = []
                    current = due_1 = due_2 = due_3 = due_4 = 0.00
                    total_debit = total_credit = total_balance = 0.00
                    total_amt1 = total_amt2= total_amt3 = total_amt4 = total_home_amt1 = total_home_amt2 = total_home_amt3 = total_home_amt4 = 0
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
                                due_date = Date + timedelta(days=(termdays))
                            #print EndDate
                            due_date = due_date and due_date.strftime('%Y-%m-%d') or False
                            d = datetime.strptime(t['inv_date'], '%Y-%m-%d')
                            delta = datetime.strptime(date_to, '%Y-%m-%d') - d
                            daysremaining = delta.days
                            remain_amt = (t['inv_amt'] * sign) - (t['paid'] * sign)
                            
                            #get Type
                            type = ''
                            deposit = t['deposit'] or 0.00
                            debit = ((remain_amt > 0) and remain_amt) or 0.00
                            credit = ((remain_amt < 0) and (remain_amt * -1)) or 0.00
                            if deposit:
                                type = 'DP'
                            else:
                                remain = debit - credit
                                if remain > 0:
                                    type = 'IN'
                                else:
                                    type = 'CN'
                            ######################
                            #get cust po no
                            cust_po_no = False
                            invoice = False
                            if t['invoice_id']:
                                invoice = invoice_obj.browse(cr, uid, t['invoice_id'])
                            picking_id = (invoice and invoice.picking_id and invoice.picking_id.id) or False
                            picking_qry = ''
                            if picking_id:
                                picking_qry = "AND ai.picking_id = %s "%picking_id
                            else:
                                picking_qry = "AND ai.picking_id IN (0) "
                            #print picking_qry
                            cr.execute("select so.client_order_ref from account_invoice ai inner join " \
                                            "sale_order_picking_rel sopr on sopr.picking_id = ai.picking_id " \
                                            "inner join sale_order so on so.id = sopr.order_id where ai.type = 'out_invoice' " + picking_qry)
                    
                            qry = cr.dictfetchall()
                            if qry:
                                for s in qry:
                                    if cust_po_no == False:
                                        cust_po_no = str(s['client_order_ref'])
                                    else:
                                        cust_po_no += ', %s'%s['client_order_ref']
                                        
                            total_debit += ((remain_amt > 0) and remain_amt) or 0.00
                            total_credit += ((remain_amt < 0) and (remain_amt * -1)) or 0.00
                            total_balance = total_debit - total_credit
                            
                            if t['period_id'] == max_period:
                                current += remain_amt
                            elif t['period_id'] == period_1:
                                due_1 += remain_amt
                            elif t['period_id'] == period_2:
                                due_2 += remain_amt
                            elif t['period_id'] == period_3:
                                due_3 += remain_amt
                            else:
                                due_4 += remain_amt
                            
                            header += str(t['inv_name'] or '') + ';' + str(type or '') + ';' + str(cust_po_no or '') + ';' + str(t['inv_date'] or '') + ';' + str(due_date or '') + ';' \
                            + str(((remain_amt > 0) and remain_amt) or 0.00) + ';' + str(((remain_amt < 0) and (remain_amt * -1)) or 0.00) + ';' \
                            + ' \n'
                    
                    header += 'Cummulative Total' + ';;;;;' + str(total_debit or 0.00) + ';' + str(total_credit) + ' \n'
                    header += 'Cummulative Total' + ';;;;;' + str(total_balance or 0.00) + ' \n'
                    header += 'Aged by Due Date' + ' \n'
                    header += 'Current (Not Due)' + ';' + '1 To 30' + ';' + '31 To 60' + ';' + '61 To 90' + ';' + 'Over 90' + ' \n'
                    header += str(current or 0.00) + ';' + str(due_1) + ';' + str(due_2) + ';' + str(due_3) + ';' + str(due_4) + ' \n'
                    
        #                     val.append({
        #                         'invoice_id': t['invoice_id'],
        #                         'invoice_name' : t['inv_name'],
        #                         'invoice_date' : t['inv_date'],
        #                         'due_date' : due_date,
        #                         'debit':  ((remain_amt > 0) and remain_amt) or 0.00,
        #                         'credit':  ((remain_amt < 0) and (remain_amt * -1)) or 0.00,
        #                         'deposit': t['deposit'],
        #                         })
#                             if t['period_id'] == max_period:
#                                 self.current += remain_amt
#                             elif t['period_id'] == period_1:
#                                 self.due_1 += remain_amt
#                             elif t['period_id'] == period_2:
#                                 self.due_2 += remain_amt
#                             elif t['period_id'] == period_3:
#                                 self.due_3 += remain_amt
#                             else:
#                                 self.due_4 += remain_amt
                        

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Statement Of Account.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','action_account_statement_csv_report')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Statement Of Account',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.statement.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }


account_statement_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
