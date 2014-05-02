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

class sale_order_issued_report(report_sxw.rml_parse):
    _name = 'sale.order.issued.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.partner_code_from = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
        self.partner_code_to = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(sale_order_issued_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(sale_order_issued_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_code_from': self._get_code_from,
            'get_code_to': self._get_code_to,
            })

    def _get_code_from(self):
        return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
    
    def _get_code_to(self):
        return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False

    def _get_lines(self):
        results = []
        val_part = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        code_from = self.partner_code_from
        code_to = self.partner_code_to
        res_partner_obj = self.pool.get('res.partner')
        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
        val_part.append(('customer', '=', True))
        part_ids = res_partner_obj.search(self.cr, self.uid, val_part, order='ref ASC')
        val_ss = ''
        if part_ids:
            for ss in part_ids:
                if val_ss == '':
                    val_ss += str(ss)
                else:
                    val_ss += (', ' + str(ss))

        self.cr.execute("select so.name as so_no, " \
                        "so.date_order as so_date, " \
                        "so.client_order_ref as customer_po_no, " \
                        "sol.price_unit as unit_price, " \
                        "sol.product_uom_qty as qty, " \
                        "sol.price_unit * sol.product_uom_qty as total, " \
                        "sl.name as location, " \
                        "rp.ref as partner_ref, " \
                        "rp.name as partner_name, " \
                        "pc.name as customer_part_no, " \
                        "pt.name as part_no, " \
                        "pb.name as brand " \
                        "from sale_order so " \
                        "inner join sale_order_line sol on so.id = sol.order_id " \
                        "left join stock_location sl on sol.location_id = sl.id " \
                        "left join res_partner rp on so.partner_id = rp.id " \
                        "left join product_customer pc on sol.product_customer_id = pc.id " \
                        "left join product_template pt on sol.product_id2 = pt.id " \
                        "left join product_product pp on sol.product_id2 = pp.id " \
                        "left join product_brand pb on pp.brand_id = pb.id " \
                        "WHERE so.date_order >= '" + str(date_from) + "' AND so.date_order <= '" + str(date_to) + "' " \
                        "and so.partner_id in (" + val_ss + ") and so.state in ('progress','done') " \
                        "order by so.name")
        res_general = self.cr.dictfetchall()
#        val_sale = []
#        sale_order_obj = self.pool.get('sale.order')
#        val_sale.append(('date_order', '>=', date_from))
#        val_sale.append(('date_order', '<=', date_to))
#        val_sale.append(('partner_id', 'in', part_ids))
#        val_sale.append(('state', 'in', ('progress', 'done')))
#        sale_order_ids = sale_order_obj.search(self.cr, self.uid, val_sale, order='name ASC')
#        for sale_order_id in sale_order_obj.browse(self.cr, self.uid, sale_order_ids):
#            for lines in sale_order_id.order_line:
#                res = {}
#                res['so_no'] = sale_order_id.name
#                res['so_date'] = sale_order_id.date_order
#                res['customer_po_no'] = sale_order_id.client_order_ref
#                res['unit_price'] = lines.price_unit
#                res['qty'] = lines.product_uom_qty
#                res['total'] = lines.price_subtotal
#                res['location'] = lines.location_id.name
#                res['partner_ref'] = sale_order_id.partner_id.ref
#                res['partner_name'] = sale_order_id.partner_id.name
#                res['customer_part_no'] = lines.product_customer_id.name
#                res['part_no'] = lines.product_id2.name
#                res['brand'] = lines.product_id2.brand_id.name
#                results.append(res)
        return res_general

report_sxw.report_sxw('report.sale.order.issued.report_landscape', 'sale.order.line',
    'addons/max_custom_report/sale/report/sale_order_issued_report.rml', parser=sale_order_issued_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
