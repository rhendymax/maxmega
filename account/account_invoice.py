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

import tools
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
from datetime import datetime
import time
from dateutil.relativedelta import relativedelta
from tools import float_round, float_is_zero, float_compare

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _description = "Invoice"
    
    def _amount_all_home(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed_home': 0.0,
                'amount_tax_home': 0.0,
                'amount_total_home': 0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed_home'] += (line.price_subtotal)
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax_home'] += line.amount
            
            ctx = context.copy()
            ctx.update({'date': invoice.cur_date})
            invoice_rate = self.browse(cr, uid, invoice.id, context=ctx).currency_id.rate
            company_currency_rate = invoice.company_id.currency_id.rate
            if invoice.company_id.currency_id.id != invoice.currency_id.id:
                res[invoice.id]['amount_tax_home'] = float_round(res[invoice.id]['amount_tax_home'] / invoice_rate * company_currency_rate,2)
                res[invoice.id]['amount_untaxed_home'] = float_round(res[invoice.id]['amount_untaxed_home'] / invoice_rate * company_currency_rate,2)

            res[invoice.id]['amount_total_home'] = res[invoice.id]['amount_tax_home'] + res[invoice.id]['amount_untaxed_home']
        return res

    def create(self, cr, user, vals, context=None):
        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            vals.update({'partner_id': partner_id})
            partner = self.pool.get('res.partner').browse(cr, user, partner_id, context=None)
            addr = self.pool.get('res.partner').address_get(cr, user, [partner_id], ['delivery', 'invoice', 'contact'])
            if vals['type'] in ('in_invoice', 'in_refund'):
                currency_id = partner and partner.property_product_pricelist_purchase and \
                                partner.property_product_pricelist_purchase.currency_id and \
                                partner.property_product_pricelist_purchase.currency_id.id or False
                account_id = partner and partner.property_account_payable and \
                                partner.property_account_payable.id or False
            else:
                currency_id = partner and partner.property_product_pricelist and \
                                partner.property_product_pricelist.currency_id and \
                                partner.property_product_pricelist.currency_id.id or False
                account_id = partner and partner.property_account_receivable and \
                                partner.property_account_receivable.id or False
            vals.update({
                         'partner_id': partner_id,
                         'address_contact_id': addr['contact'],
                         'address_invoice_id': addr['invoice'],
                         'currency_id': currency_id,
                         'account_id':account_id,
                         'fiscal_position' : partner.property_account_position and partner.property_account_position.id or False,
                         })
        if 'picking_id' not in vals:
            cur_date = False
            if 'date_invoice' in vals:
                cur_date = vals['date_invoice']
            vals.update({
                         'cur_date': cur_date or time.strftime('%Y-%m-%d'),
                         })

        if 'invoice_no' in vals:
            if vals['invoice_no']:
                account_invoice_obj =  self.pool.get('account.invoice')
                invoice_ids = account_invoice_obj.search(cr, user, [('invoice_no', '=', vals['invoice_no'])], limit=1)
#                if invoice_ids:
#                    raise osv.except_osv(_('Error !'), _('Please retype the invoice no, the invoice no your key in is already input.'))
        new_id = super(account_invoice, self).create(cr, user, vals, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):

        invoice_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
#        invoice_id = ids or False
        invoice_obj = self.pool.get('account.invoice')
        typexx = ('type' in vals and vals['type']) or (invoice_obj.browse(cr, uid, invoice_id, context=None).type) or False
        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=None)
            addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery', 'invoice', 'contact'])
            if typexx in ('in_invoice', 'in_refund'):
                currency_id = partner and partner.property_product_pricelist_purchase and \
                                partner.property_product_pricelist_purchase.currency_id and \
                                partner.property_product_pricelist_purchase.currency_id.id or False
                account_id = partner and partner.property_account_payable and \
                                partner.property_account_payable.id or False
            else:
                currency_id = partner and partner.property_product_pricelist and \
                                partner.property_product_pricelist.currency_id and \
                                partner.property_product_pricelist.currency_id.id or False
                account_id = partner and partner.property_account_receivable and \
                                partner.property_account_receivable.id or False
            vals.update({
                         'partner_id': partner_id,
                         'address_contact_id': addr['contact'],
                         'address_invoice_id': addr['invoice'],
                         'currency_id': currency_id,
                         'account_id':account_id,
                         'cur_date': time.strftime('%Y-%m-%d'),
                         'fiscal_position' : partner.property_account_position and partner.property_account_position.id or False,
                         })
        if 'invoice_no' in vals:
            account_invoice_obj =  self.pool.get('account.invoice')
            invoice_ids = account_invoice_obj.search(cr, uid, [('invoice_no', '=', vals['invoice_no'])], limit=1)
            if invoice_ids:
                raise osv.except_osv(_('Error !'), _('Please retype the invoice no, the invoice no your key in is already input.'))
        return super(account_invoice, self).write(cr, uid, ids, vals, context=context)

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cursor, user, ids, context=context):
            res[invoice.id] = False
            if (invoice.state == 'open'):
                sale_term_id = invoice.sale_term_id and invoice.sale_term_id.id or False
                if sale_term_id:
                    d = datetime.strptime(invoice.date_invoice, '%Y-%m-%d')
                    delta = datetime.now() - d
                    daysremaining = delta.days
                    gracedays = 0
                    partner_grace = invoice.partner_id and invoice.partner_id.grace or 0
                    sale_grace = invoice.partner_id and invoice.partner_id.sale_term_id and invoice.partner_id.sale_term_id.grace or 0
                    if partner_grace > 0:
                        gracedays = partner_grace
                    else:
                        gracedays = sale_grace
                    termdays = (invoice.sale_term_id and invoice.sale_term_id.days or 0) + gracedays
                    if daysremaining > termdays:
                        res[invoice.id] = True
        return res

    def _rate(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        res_currency_rate_obj = self.pool.get("res.currency.rate")

        for obj in self.browse(cr, uid, ids, context=context):
            cur_id = obj.currency_id and obj.currency_id.id or False
            cur_date = obj.cur_date or False
            if cur_id and cur_date:
                res_currency_rate_ids = res_currency_rate_obj.search(cr, uid, [('currency_id', '=', cur_id), ('name', '<=', cur_date)], order='name DESC', limit=1)
                if res_currency_rate_ids:
                    res[obj.id] = res_currency_rate_obj.browse(cr, uid, res_currency_rate_ids[0], context=context).rate
                else:
                    res[obj.id] = 0
            else:
                res[obj.id] = 0

        return res

    def _get_analytic_lines(self, cr, uid, id, context=None):
        if context is None:
            context = {}
        inv = self.browse(cr, uid, id)
        cur_obj = self.pool.get('res.currency')

        company_currency = inv.company_id.currency_id.id
        if inv.type in ('out_invoice', 'in_refund'):
            sign = 1
        else:
            sign = -1

        iml = self.pool.get('account.invoice.line').move_line_get(cr, uid, inv.id, context=context)
        for il in iml:
            if il['account_analytic_id']:
                if inv.type in ('in_invoice', 'in_refund'):
                    ref = inv.reference
                else:
                    ref = self._convert_ref(cr, uid, inv.number)
                if not inv.journal_id.analytic_journal_id:
                    raise osv.except_osv(_('No Analytic Journal !'),_("You have to define an analytic journal on the '%s' journal!") % (inv.journal_id.name,))
                il['analytic_lines'] = [(0,0, {
                    'name': il['name'],
                    'date': inv['date_invoice'],
                    'account_id': il['account_analytic_id'],
                    'unit_amount': il['quantity'],
                    'amount': cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, il['price'], context={'date': inv.cur_date}) * sign,
                    'product_id': il['product_id'],
                    'product_uom_id': il['uos_id'],
                    'general_account_id': il['account_id'],
                    'journal_id': inv.journal_id.analytic_journal_id.id,
                    'ref': ref,
                })]
        return iml

    def line_get_convert(self, cr, uid, x, part, date, cur_date, exrate, is_refund, context=None):
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'cur_date': cur_date,
            'exrate': exrate,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'is_refund': is_refund,
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount') and float_round(x.get('tax_amount'),2) or False,
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }

    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error !'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines !'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue
            
            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = inv.company_id.currency_id.id
            # create the analytical lines
            # one move line per invoice line

            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)

            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            #if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
            #    raise osv.except_osv(_('Bad total !'), _('Please verify the price of the invoice !\nThe real total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error !'), _("Can not create the invoice !\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. The latest line of your payment term must be of type 'balance' to avoid rounding issues."))

            # one move line per tax line
#            raise osv.except_osv(_('UserErrorx1'),
#                    _(str(iml)))
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            is_refund = False
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    is_refund = True
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    is_refund = True
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml)

            acc_id = inv.account_id.id

            name = inv['name'] or '/'

            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
#            raise osv.except_osv(_('UserError'),
#                    _(str(totlines)))
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.cur_date})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })
#            raise osv.except_osv(_('UserError'),
#                    _(str(iml)))
            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            cur_date = inv.cur_date or date
            exrate = inv.cur_rate
            part = inv.partner_id.id

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, cur_date, exrate, is_refund, context=ctx)),iml)
#            raise osv.except_osv(_('UserError'),
#                    _(str(line)))
            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                        _('You cannot create an invoice on a centralised journal. Uncheck the centralised counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)
#            raise osv.except_osv(_('UserError'),
#                    _(str(line)))

#create invoice no
            obj_sequence = self.pool.get('ir.sequence')

            if inv.type == 'in_invoice':
                if inv.charge_seq:
                    seq_id = inv.company_id and inv.company_id.sinv_chrg_seq_id and inv.company_id.sinv_chrg_seq_id.id or False
                    if not seq_id:
                        raise osv.except_osv(_('Invalid action !'), _('not Supplier Invoice(Charges) sequence defined in company configuration'))
                    move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)

                else:
                    if inv.partner_id.sundry:
                        seq_id = inv.company_id and inv.company_id.sinv_sundry_seq_id and inv.company_id.sinv_sundry_seq_id.id or False
                        if not seq_id:
                            raise osv.except_osv(_('Invalid action !'), _('not Supplier Invoice(Sundry) sequence defined in company configuration'))
                        move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)
                    else:
                        seq_id = inv.company_id and inv.company_id.sinv_seq_id and inv.company_id.sinv_seq_id.id or False
                        if not seq_id:
                            raise osv.except_osv(_('Invalid action !'), _('not Supplier Invoice sequence defined in company configuration'))
                        move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)
            elif inv.type == 'in_refund':
                if inv.partner_id.sundry:
                    seq_id = inv.company_id and inv.company_id.sref_sundry_seq_id and inv.company_id.sref_sundry_seq_id.id or False
                    if not seq_id:
                        raise osv.except_osv(_('Invalid action !'), _('not Supplier Refund(Sundry) sequence defined in company configuration'))
                    move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)
                else:
                    seq_id = inv.company_id and inv.company_id.sref_seq_id and inv.company_id.sref_seq_id.id or False
                    if not seq_id:
                        raise osv.except_osv(_('Invalid action !'), _('not Supplier Refund sequence defined in company configuration'))
                    move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)
            elif inv.type == 'out_invoice':
                if inv.charge_seq:
                    seq_id = inv.company_id and inv.company_id.cinv_chrg_seq_id and inv.company_id.cinv_chrg_seq_id.id or False
                    if not seq_id:
                        raise osv.except_osv(_('Invalid action !'), _('not Customer Invoice(Charges) sequence defined in company configuration'))
                    move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)
                else:
                    move_n = inv.picking_id and inv.picking_id.name or obj_sequence.next_by_id(cr, uid, inv.journal_id.sequence_id.id, None)
            elif inv.type == 'out_refund':
                if inv.partner_id.sundry:
                    raise osv.except_osv(_('Invalid action !'), _('cannot process customer with sundry, please uncheck sundry at customer configuration'))
                else:
                    seq_id = inv.company_id and inv.company_id.cref_seq_id and inv.company_id.cref_seq_id.id or False
                    if not seq_id:
                        raise osv.except_osv(_('Invalid action !'), _('not Customer Refund sequence defined in company configuration'))
                    move_n = obj_sequence.next_by_id(cr, uid, seq_id, None)

            move = {
                'name': move_n,
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration':inv.comment
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update({'company_id': inv.company_id.id})
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

#            raise osv.except_osv(_('UserError'),
#                    _(str(move)))
            
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
#            raise osv.except_osv(_('UserError'),
#                    _(str(new_move_name)))
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            ctx.update({'invoice':inv})
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

    def _get_rate(self, cr, uid, context=None):
        if context is None:
            context = {}
        res_user_obj = self.pool.get("res.users")
        res_user = res_user_obj.browse(cr, uid, uid, context=context)
        currency_id = res_user and res_user.company_id and res_user.company_id.currency_id and res_user.company_id.currency_id.id or False
        curr = currency_id and self.pool.get("res.currency").browse(cr, uid, currency_id, context=context)
        rate = curr and curr.rate or 0

        return rate

    def _due_date(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cursor, user, ids, context=context):
            res[invoice.id] = False
            if (invoice.state == 'open'):
                sale_term_id = invoice.sale_term_id and invoice.sale_term_id.id or False
#                if invoice.partner_id.id == 427:
#                    raise osv.except_osv(_('Error !'), _(sale_term_id))
                if sale_term_id:

                    gracedays = 0
                    partner_grace = invoice.partner_id and invoice.partner_id.grace or 0
                    sale_grace = invoice.partner_id and invoice.partner_id.sale_term_id and invoice.partner_id.sale_term_id.grace or 0
                    if partner_grace > 0:
                        gracedays = partner_grace
                    else:
                        gracedays = sale_grace
                    termdays = (invoice.sale_term_id and invoice.sale_term_id.days or 0) + gracedays
                    next_date = (datetime.strptime(invoice.date_invoice, '%Y-%m-%d') + relativedelta(days=termdays))
#                    raise osv.except_osv(_('UserError'),
#                                         _(str(next_date.strftime('%Y-%m-%d')) + str(invoice.date_invoice)))
                    res[invoice.id] = next_date.strftime('%Y-%m-%d')
        return res

    _columns = {
        'fob_id': fields.many2one('fob.point.key', 'FOB Point Key', select=True, readonly=True,),
        'sales_zone_id': fields.many2one('res.partner.sales.zone','Sales Zone',readonly=True),
        'ship_method_id': fields.many2one('shipping.method','Ship Method', readonly=True),
        'charge_seq': fields.boolean('Charges Sequence', help="tick it when want to use charges sequence no"),
        'ref_no': fields.char('Reference No', size=64),
        'invoice_date': fields.date('Supplier Invoice Date'),
        'invoice_no': fields.char('Supplier Invoice No', size=64),
        'header_invoice': fields.text('Header'),
        'footer_invoice': fields.text('Footer'),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', select=True, change_default=True),
        'partner_id2': fields.many2one('res.partner', 'Partner', invisible=True),
        'inv_rate': fields.float('Invoice Exchange Rate', digits=(12,6), help='The rate of the currency that supplier/customer give'),
        'cur_rate': fields.function(_rate, type='float', digits=(12,6), string='Currency Rate'),
        'cur_date': fields.datetime('Currency Date', help="Date of Currency Retrieve"),
        'picking_id': fields.many2one('stock.picking', 'Picking', select=True),
        'sale_term_id': fields.many2one('sale.payment.term','Sale Payment Term',readonly=True, states={'draft':[('readonly',False)]}),
        'expired_term': fields.function(_invoiced, string='Expired Term', type='boolean',),
        'due_date': fields.function(_due_date, string='Due Date', type='date',),
        'amount_untaxed_home': fields.function(_amount_all_home, digits_compute=dp.get_precision('Account'), string='Untaxed Home',
            store=True,
            multi='all'),
        'amount_tax_home': fields.function(_amount_all_home, digits_compute=dp.get_precision('Account'), string='Tax Home',
            store=True,
            multi='all'),
        'amount_total_home': fields.function(_amount_all_home, digits_compute=dp.get_precision('Account'), string='Total Home',
            store=True,
            multi='all'),
        'user_id': fields.many2one('res.users', 'Salesman', readonly=True),
    }

    def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines):
        total = 0
        total_currency = 0
        cur_obj = self.pool.get('res.currency')
        for i in invoice_move_lines:
            if inv.currency_id.id != company_currency:
                i['currency_id'] = inv.currency_id.id
                i['amount_currency'] = i['price']
                i['price'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id,
                        company_currency, i['price'],
                        context={'date': inv.cur_date or time.strftime('%Y-%m-%d')}), 2)
                
            else:
                i['amount_currency'] = False
                i['currency_id'] = False
            i['ref'] = ref
            if inv.type in ('out_invoice','in_refund'):
                total += float_round(i['price'],2)
                total_currency += i['amount_currency'] or i['price']
                i['price'] = - i['price']
            else:
                total -= i['price']
                total_currency -= i['amount_currency'] or i['price']
        return total, total_currency, invoice_move_lines

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, partner_id2,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False, invoice_line=False):
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,\
                    date_invoice, payment_term, partner_bank_id,company_id)

        if not partner_id:
            return result
        if invoice_line:
            partner_id = partner_id2

        if 'value' in result:
            result['value'].update({'partner_id': partner_id, 'partner_id2' : partner_id})
        else:
            result['value'] = {'partner_id': partner_id, 'partner_id2' : partner_id}

        if not type:
            return result
        res_partner_obj = self.pool.get('res.partner')
        partner = res_partner_obj.browse(cr, uid, partner_id, context=None)
        salesman = False
        sales_zone = False
        if type in ('in_invoice', 'in_refund'):
            currency_id = partner and partner.property_product_pricelist_purchase and \
                            partner.property_product_pricelist_purchase.currency_id and \
                            partner.property_product_pricelist_purchase.currency_id.id or False
        else:
            currency_id = partner and partner.property_product_pricelist and \
                            partner.property_product_pricelist.currency_id and \
                            partner.property_product_pricelist.currency_id.id or False
            salesman = (partner.user_id and partner.user_id.id) or False
            sales_zone = (partner.sales_zone_id and partner.sales_zone_id.id) or False
        curr = currency_id and self.pool.get("res.currency").browse(cr, uid, currency_id, context=None)
        rate = curr and curr.rate or 0
        result['value'].update({'fob_id': (partner.fob_id and partner.fob_id.id) or False,
                                'ship_method_id': (partner.ship_method_id and partner.ship_method_id.id) or False,
                                'sale_term_id': (partner.sale_term_id and partner.sale_term_id.id) or False,
                                'currency_id': currency_id,
                                'user_id' : salesman,
                                'sales_zone_id' : sales_zone,
                                'cur_rate':rate})


#        contact_person_ids = []
#        for pc in partner.contact_person_ids:
#            contact_person_ids.append(pc.id)
#
#        if 'domain' in result:
#            result['domain'].update({'contact_person_id': [('id', 'in', contact_person_ids)]})
#        else:
#            result['domain'] = {'contact_person_id': [('id', 'in', contact_person_ids)]}
#
#        if contact_person_id:
#            if contact_person_id not in contact_person_ids:
#                result['value'].update({'contact_person_id': False})
#                if 'warning' in result:
#                    if 'message' in result['warning']:
#                        mess = result['warning']['message']
#                        result['warning'].update({'message': _( mess + '\n & \n' +'The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')})
#                    else:
#                        result['warning'].update({'message': _('The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')})
#                else:
#                    result['warning'] = {'title': _('Warning'), 'message': _('The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')}
#        else:
#            if contact_person_ids:
#                result['value'].update({'contact_person_id': contact_person_ids[0]})
#            else:
#                result['value'].update({'contact_person_id': False})
#
#        result['value'].update({'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
#                                'fob_id': (partner.fob_id and partner.fob_id.id) or False,
#                                'sale_term_id': (partner.sale_term_id and partner.sale_term_id.id) or False,
#                                })
        return result

    def button_reset_taxes(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('account.invoice.tax')
        for id in ids:
            cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
            partner = self.browse(cr, uid, id, context=ctx).partner_id
            if partner.lang:
                ctx.update({'lang': partner.lang})
            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
                ait_obj.create(cr, uid, taxe)
        # Update the stored value (fields.function), so we write to trigger recompute
        self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
        return True

    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        #TODO: not correct fix but required a frech values before reading it.
        self.write(cr, uid, ids, {})

        for obj_inv in self.browse(cr, uid, ids, context=context):
            id = obj_inv.id
            invtype = obj_inv.type
            number = obj_inv.number
            move_id = obj_inv.move_id and obj_inv.move_id.id or False
            reference = obj_inv.reference or ''

            self.write(cr, uid, ids, {'internal_number':number})

            if invtype in ('in_invoice', 'in_refund'):
                if not reference:
                    ref = self._convert_ref(cr, uid, number)
                else:
                    ref = reference
            else:
                ref = self._convert_ref(cr, uid, number)

            cr.execute('UPDATE account_move SET ref=%s ' \
                    'WHERE id=%s AND (ref is null OR ref = \'\')',
                    (ref, move_id))
            cr.execute('UPDATE account_move_line SET ref=%s ' \
                    'WHERE move_id=%s AND (ref is null OR ref = \'\')',
                    (ref, move_id))
            cr.execute('UPDATE account_analytic_line SET ref=%s ' \
                    'FROM account_move_line ' \
                    'WHERE account_move_line.move_id = %s ' \
                        'AND account_analytic_line.move_id = account_move_line.id',
                        (ref, move_id))

            for inv_id, name in self.name_get(cr, uid, [id]):
                ctx = context.copy()
#                print ctx
#                print name
                
#                if obj_inv.type in ('out_invoice', 'out_refund'):
#                    ctx = self.get_log_context(cr, uid, context=ctx)
#                print ctx
#                raise osv.except_osv(_('UserError'),
#                                 _(str('invoice_lines')))
                message = _("Invoice  '%s' is validated.") % name
                self.log(cr, uid, inv_id, message, context=ctx)
        return True

    def _refund_cleanup_lines(self, cr, uid, lines):
        for line in lines:
            del line['id']
            del line['invoice_id']
            del line['stock_move_id']
            for field in ('company_id', 'partner_id', 'account_id', 'product_id',
                          'uos_id', 'account_analytic_id', 'tax_code_id', 'base_code_id'):
                if line.get(field):
                    line[field] = line[field][0]
            if 'invoice_line_tax_id' in line:
                line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
        return map(lambda x: (0,0,x), lines)

    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None):
        invoices = self.read(cr, uid, ids, ['name', 'type', 'number', 'reference', 'comment', 'date_due', 'partner_id', 'address_contact_id', 'address_invoice_id', 'partner_contact', 'partner_insite', 'partner_ref', 'payment_term', 'account_id', 'currency_id', 'invoice_line', 'tax_line', 'journal_id', 'cur_date'])
        obj_invoice_line = self.pool.get('account.invoice.line')
        obj_invoice_tax = self.pool.get('account.invoice.tax')
        obj_journal = self.pool.get('account.journal')
        new_ids = []
        for invoice in invoices:
            del invoice['id']

            type_dict = {
                'out_invoice': 'out_refund', # Customer Invoice
                'in_invoice': 'in_refund',   # Supplier Invoice
                'out_refund': 'out_invoice', # Customer Refund
                'in_refund': 'in_invoice',   # Supplier Refund
            }

            invoice_lines = obj_invoice_line.read(cr, uid, invoice['invoice_line'])
            invoice_lines = self._refund_cleanup_lines(cr, uid, invoice_lines)
            print invoice_lines
#            raise osv.except_osv(_('UserError'),
#                                 _(str(invoice_lines)))
            tax_lines = obj_invoice_tax.read(cr, uid, invoice['tax_line'])
            tax_lines = filter(lambda l: l['manual'], tax_lines)
            tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines)
            if journal_id:
                refund_journal_ids = [journal_id]
            elif invoice['type'] == 'in_invoice':
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')])
            else:
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')])

            if not date:
                date = time.strftime('%Y-%m-%d')
            invoice.update({
                'type': type_dict[invoice['type']],
                'date_invoice': date,
                'state': 'draft',
                'number': False,
                'invoice_line': invoice_lines,
                'tax_line': tax_lines,
                'journal_id': refund_journal_ids,
                'picking_id': False,
            })
            if period_id:
                invoice.update({
                    'period_id': period_id,
                })
            if description:
                invoice.update({
                    'name': description,
                })
            # take the id part of the tuple returned for many2one fields
            for field in ('address_contact_id', 'address_invoice_id', 'partner_id',
                    'account_id', 'currency_id', 'payment_term', 'journal_id'):
                invoice[field] = invoice[field] and invoice[field][0]
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice))

        return new_ids
account_invoice()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _description = "Invoice Line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id)
            res[line.id] = taxes['total']
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = float_round(cur_obj.round(cr, uid, cur, res[line.id]),2)
        return res

    _columns = {
        'stock_move_id': fields.many2one('stock.move', 'Move'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
    }


    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            tax_code_found= False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, inv.address_invoice_id.id, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context={'date': inv.cur_date}),2)
        return res

account_invoice_line()


class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"
    _description = "Invoice Tax"

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id)['taxes']:
                tax['price_unit'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = float_round(tax['amount'],2)
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = float_round(tax['price_unit'] * line['quantity'],2)

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.cur_date or time.strftime('%Y-%m-%d')}, round=False),2)
                    val['tax_amount'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.cur_date or time.strftime('%Y-%m-%d')}, round=False),2)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.cur_date or time.strftime('%Y-%m-%d')}, round=False),2)
                    val['tax_amount'] = float_round(cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.cur_date or time.strftime('%Y-%m-%d')}, round=False),2)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped


account_invoice_tax()


class account_move_line(osv.osv):
    _inherit = 'account.move.line'
    _description = 'Journal Items'

    _columns = {
        'exrate': fields.float('ExRate', digits=(12,6)),
        'stock_move_id': fields.many2one('stock.move','Stock Moves'),
        'is_refund': fields.boolean('Refund Value'),
    }

class account_account(osv.osv):
    _inherit = 'account.account'
    _description = 'Account'

    _columns = {
        'pl_type': fields.selection([
            ('income', 'Main Income (P&L)'),
            ('expense', 'Main Expense (P&L)'),
            ('other_income', 'Other Income (P&L)'),
            ('other_expense', 'Other Expense (P&L)'),
            ('equity', 'EQUITY (BS)'),
            ('fixed_asset', 'FIXED ASSET (BS)'),
            ('accumulated', 'ACCUMULATED DEPRN (BS)'),
            ('investment', 'INVESTMENT (BS)'),
            ('curr_asset', 'CURRENT ASSET (BS)'),
            ('curr_liabilities', 'CURRRENT LIABILITIES (BS)'),
        ], 'P&L / BS Type'),
    }

class account_move(osv.osv):
    _inherit = "account.move"
    _description = "Account Entry"

    _columns = {
        'picking_id': fields.many2one('stock.picking','Picking'),
    }

account_move()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
