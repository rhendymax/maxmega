# -*- encoding: utf-8 -*-
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
from osv import osv, fields
from tools.translate import _
import decimal_precision as dp

class change_price(osv.osv_memory):
    _name = 'change.price'
    _description = 'Change Price'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        res = super(change_price, self).default_get(cr, uid, fields, context=context)
        for lines in sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'sale_order_line_id' in fields:
                res.update({'sale_order_line_id': lines.id or False})
        return res

    def change_price(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            sale_order_line_obj.write(cr, uid, obj.sale_order_line_id.id, {'price_unit': obj.price_unit}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', ondelete='cascade'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
    }

change_price()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
