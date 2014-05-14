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
from tools import float_round, float_is_zero, float_compare

class monthly_pos_with_sale_order_report(report_sxw.rml_parse):
    _name = 'monthly.pos.with.sale.order.report'

    def set_context(self, objects, data, ids, report_type=None):
            new_ids = ids
            res = {}
            account_invoice_obj = self.pool.get('account.invoice')
            qry_supp = ''
            val_part = []
            qry_ai = ''
            val_ai = []
            
            partner_ids = False
            invoice_ids = False

            #Date
            if data['form']['date_selection'] == 'none_sel':
                self.date_from = False
                self.date_to = False
            else:
                self.date_from = data['form']['date_from']
                self.date_to = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

            #invoice
            qry_ai = 'type = "out_invoice" and state in ("open","paid") '
            val_ai.append(('type','=', 'out_invoice'))
            val_ai.append(('state','in', ('open','paid')))
            ai_default_from = data['form']['invoice_default_from'] and data['form']['invoice_default_from'][0] or False
            ai_default_to = data['form']['invoice_default_to'] and data['form']['invoice_default_to'][0] or False
            ai_input_from = data['form']['invoice_input_from'] or False
            ai_input_to = data['form']['invoice_input_to'] or False
    
            if data['form']['invoice_selection'] == 'all_vall':
                invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            if data['form']['invoice_selection'] == 'def':
                data_found = False
                if ai_default_from and account_invoice_obj.browse(self.cr, self.uid, ai_default_from) and account_invoice_obj.browse(self.cr, self.uid, ai_default_from).number:
                    data_found = True
                    val_ai.append(('number', '>=', account_invoice_obj.browse(self.cr, self.uid, ai_default_from).number))
                if ai_default_to and account_invoice_obj.browse(self.cr, self.uid, ai_default_to) and account_invoice_obj.browse(self.cr, self.uid, ai_default_to).number:
                    data_found = True
                    val_ai.append(('number', '<=', account_invoice_obj.browse(self.cr, self.uid, ai_default_to).number))
                if data_found:
                    invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            elif data['form']['invoice_selection'] == 'input':
                data_found = False
                if ai_input_from:
                    self.cr.execute("select number " \
                                    "from account_invoice "\
                                    "where " + qry_ai + " and " \
                                    "name ilike '" + str(ai_input_from) + "%' " \
                                    "order by number limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_ai.append(('number', '>=', qry['number']))
                if ai_input_to:
                    self.cr.execute("select number " \
                                    "from account_invoice "\
                                    "where " + qry_ai + " and " \
                                    "name ilike '" + str(ai_input_to) + "%' " \
                                    "order by number desc limit 1")
                    qry = self.cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_ai.append(('number', '<=', qry['number']))
                #print val_part
                if data_found:
                    invoice_ids = account_invoice_obj.search(self.cr, self.uid, val_ai, order='number ASC')
            elif data['form']['invoice_selection'] == 'selection':
                if data['form']['invoice_ids']:
                    invoice_ids = data['form']['invoice_ids']
            self.invoice_ids = invoice_ids
            return super(monthly_pos_with_sale_order_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(monthly_pos_with_sale_order_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            })

    def _get_lines(self):
        results = []
        cr              = self.cr
        uid             = self.uid
        date_from = self.date_from
        date_to = self.date_to
        date_from_qry = date_from and "And ai.date_invoice >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And ai.date_invoice <= '" + str(date_to) + "' " or " "

        invoice_ids = self.invoice_ids or False
        invoice_qry = (invoice_ids and ((len(invoice_ids) == 1 and "AND ai.id = " + str(invoice_ids[0]) + " ") or "AND ai.id IN " + str(tuple(invoice_ids)) + " ")) or "AND ai.id IN (0) "
        res_lines = []

        cr.execute("select ai.number as invoice_no, " \
                        "ai.date_invoice as date_inv, " \
                        "so.name as so_no, " \
                        "so.client_order_ref as customer_po_no, " \
                        "sl.name as location, " \
                        "rp.name as customer_name, " \
                        "pc.name as cpn, " \
                        "pt.name as mpn, " \
                        "ail.price_unit as selling_price, " \
                        "ail.quantity as quantity, " \
                        "ail.price_unit * ail.quantity as total, " \
                        "pb.name as brand_name " \
                        "from account_invoice ai " \
                        "inner join account_invoice_line ail on ai.id = ail.invoice_id " \
                        "left join res_partner rp on ai.partner_id = rp.id " \
                        "left join product_template pt on ail.product_id = pt.id " \
                        "left join product_product pp on pt.id = pp.id " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "left join stock_move sm on ail.stock_move_id = sm.id " \
                        "left join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "left join sale_order so on sol.order_id = so.id " \
                        "left join stock_location sl on sol.location_id = sl.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "where ai.type = 'out_invoice' and ai.state in ('open','paid') and ail.product_id is not null " \
                        + date_from_qry \
                        + date_to_qry \
                        + invoice_qry + \
                        "order by ai.date_invoice, invoice_no, brand_name")

        results = cr.dictfetchall()
        return results

report_sxw.report_sxw('report.monthly.pos.with.sale.order.report_landscape', 'account.invoice',
    'addons/max_custom_report/account/report/monthly_pos_with_sale_order_report.rml', parser=monthly_pos_with_sale_order_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
