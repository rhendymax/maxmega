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

class change_effective(osv.osv_memory):
    _name = 'change.effective'
    _description = 'Change Effective Date'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        res = super(change_effective, self).default_get(cr, uid, fields, context=context)
        for lines in sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'sale_order_line_id' in fields:
                res.update({'sale_order_line_id': lines.id or False})
        return res

    def do_reschedule(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        product_uom_obj = self.pool.get('product.uom')
        product_customer_price = self.pool.get('product.customer.price')
        product_customer_upper_limit_obj = self.pool.get('product.customer.upper.limit')
        currency_obj = self.pool.get('res.currency')
        product_product_obj = self.pool.get('product.product')
        for obj in self.browse(cr, uid, ids, context=context):
            ptype_src = obj.sale_order_line_id.order_id.company_id.currency_id.id
            pricelist = obj.sale_order_line_id.order_id.pricelist_id
            uom = obj.sale_order_line_id.product_uom.id
            qty = obj.sale_order_line_id.product_uom_qty
            default_uom = obj.sale_order_line_id.product_id.product_tmpl_id.uom_id.id
            qty_overall = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            effective_date = obj.change_date
            product_customer_id = obj.sale_order_line_id.product_customer_id
            product_customer_price_ids = product_customer_price.search(cr, uid, [('product_customer_id','=',product_customer_id.id),('effective_date','<=',effective_date)], order='effective_date ASC')
            price = 0.00
            if product_customer_price_ids:
                product_customer_price_id = product_customer_price.browse(cr, uid, product_customer_price_ids[0], context=context)
                product_customer_upper_limit_ids = product_customer_upper_limit_obj.search(cr, uid, [('product_customer_price_id','=',product_customer_price_id.id),('qty','<=',qty_overall)], order='qty DESC')
                currency_id = pricelist.currency_id.id
                if product_customer_upper_limit_ids:
                    product_customer_upper_limit_id = product_customer_upper_limit_obj.browse(cr, uid, product_customer_upper_limit_ids[0], context=context)
                    price = currency_obj.compute(cr, uid, product_customer_id.pricelist_id.currency_id.id, ptype_src, product_customer_upper_limit_id.unit_cost, round=False)
                else:
                    price = currency_obj.compute(cr, uid, product_customer_id.pricelist_id.currency_id.id, ptype_src, product_customer_price_id.unit_cost, round=False)
                price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                price = product_uom_obj._compute_price(cr, uid, default_uom, price, default_uom)
                price = product_product_obj.round_p(cr, uid, price, 'Sale Price')

            sale_order_line_obj.write(cr, uid, obj.sale_order_line_id.id, {'effective_date': effective_date, 'price_unit': price}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', ondelete='cascade'),
        'change_date': fields.date('Effective Date', required=True, select=True),
        'reason': fields.char('Reason', size=254, required=True, select=True),
        'create_uid': fields.many2one('res.users', 'Responsible'),
        'create_date': fields.datetime('Creation Date',),
    }

change_effective()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
