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

import time
from report import report_sxw
from osv import osv
import pooler
import locale
from mx import DateTime as dt
from report.interface import report_rml
from tools import to_xml
import calendar
import math
from datetime import datetime
from tools import amount_to_text_en
import locale
from tools.translate import _
locale.setlocale(locale.LC_ALL, '')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class maxmega_sale_order_confirmation(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(maxmega_sale_order_confirmation, self).__init__(cr, uid, name, context=context)

#        stock_move_obj = self.pool.get('stock.move')
#        product_uom_obj = self.pool.get('product.uom')
        sale_order_obj = self.pool.get('sale.order')
        for sale_order in sale_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            for lines in sale_order.order_line:
                
                if not lines.confirmation_date:
                    raise osv.except_osv(_('Error !'), _('No Confirmation Date Entered'))

        print "1"
        self.localcontext.update({
            'time': time,
            'get_price_subtotal': self._get_subtotal,
        })

    def _get_subtotal(self, sol):
#        sol_obj         = self.pool.get('sale.order.line')
        price_subtotal = 0.00
        if sol.price_subtotal:
            price_subtotal = sol.price_subtotal
        return price_subtotal;

report_sxw.report_sxw(
    'report.max.maxmega.sale.order2',
    'sale.order',
    'addons/maxmega_report_addons/report/sale_order_confirmation.rml',
    parser=maxmega_sale_order_confirmation, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

