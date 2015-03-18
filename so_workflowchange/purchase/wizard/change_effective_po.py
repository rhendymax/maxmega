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

class change_effective_po(osv.osv_memory):
    _name = 'change.effective.po'
    _description = 'Change Effective Date'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        res = super(change_effective_po, self).default_get(cr, uid, fields, context=context)
        for lines in purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'po_line_id' in fields:
                res.update({'po_line_id': lines.id or False})
        return res

    def do_reschedule(self, cr, uid, ids, context=None):
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom_obj = self.pool.get('product.uom')
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price = self.pool.get('product.supplier.price')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')
        currency_obj = self.pool.get('res.currency')
        product_product_obj = self.pool.get('product.product')
        for obj in self.browse(cr, uid, ids, context=context):
            currency_id = obj.po_line_id.order_id.pricelist_id.currency_id.id
            ptype_src = obj.po_line_id.order_id.company_id.currency_id.id
            uom = obj.po_line_id.product_uom.id
            qty = obj.po_line_id.product_qty
            default_uom = obj.po_line_id.product_id.product_tmpl_id.uom_id.id
            qty_overall = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            effective_date = obj.change_date
            product_supplier_id = product_supplier_obj.search(cr, uid, [('product_id','=',obj.po_line_id.product_id.id),('partner_child_id','=',obj.po_line_id.order_id.partner_child_id.id)])[0]
            product_supplier_val = product_supplier_obj.browse(cr, uid, product_supplier_id, context=context)
            product_supplier_price_ids = product_supplier_price.search(cr, uid, [('product_supplier_id','=',product_supplier_id),('effective_date','<=',effective_date)], order='effective_date DESC')
            if product_supplier_price_ids:
                product_supplier_price_id = product_supplier_price.browse(cr, uid, product_supplier_price_ids[0], context=context)
                product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',qty_overall)], order='qty DESC')
                if product_supplier_upper_limit_id:
                    product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                    price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
                else:
                    price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
                price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                price = product_uom_obj._compute_price(cr, uid, default_uom, price, uom)
                price = product_product_obj.round_p(cr, uid, price, 'Purchase Price',)
            else:
                price = 0.00
            po_line_obj.write(cr, uid, obj.po_line_id.id, {'original_request_date': effective_date, 'price_unit': price}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'po_line_id': fields.many2one('purchase.order.line', 'Purchase Order Line', ondelete='cascade'),
        'change_date': fields.date('Effective Date', required=True, select=True),
        'reason': fields.char('Reason', size=254, required=True, select=True),
        'create_uid': fields.many2one('res.users', 'Responsible'),
        'create_date': fields.datetime('Creation Date',),
    }

change_effective_po()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
