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

class add_so_line_wzd(osv.osv_memory):
    _name = 'add.so.line.wzd'
    _description = 'Add SO Line'

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}
        sale_order_obj = self.pool.get('sale.order')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        res = super(add_so_line_wzd, self).default_get(cr, uid, fields, context=context)
        for lines in sale_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'discount' in fields:
                res.update({'discount': 0.0})
            if 'product_uom_qty' in fields:
                res.update({'product_uom_qty': 1})
            if 'price_unit' in fields:
                res.update({'price_unit': 0.0})
            if not lines.partner_id:
                raise osv.except_osv(_('Error !'), _('please select the customer before adding lines'))

            if 'partner_id' in fields:
                res.update({'partner_id': lines.partner_id.id})
            if 'company_id' in fields:
                res.update({'company_id': lines.shop_id.company_id.id})
            if 'pricelist_id' in fields:
                res.update({'pricelist_id': lines.pricelist_id.id})
            if 'date_order' in fields:
                res.update({'date_order': lines.date_order})
            if 'fiscal_position' in fields:
                res.update({'fiscal_position': lines.fiscal_position.id})
        return res

    def delete_line(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        sale_order_obj = self.pool.get('sale.order')
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.qty_received > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because some qty has received from this line'))
            if obj.qty_allocated_onorder > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because find some allocated po in this line. unallocated it to process.'))
            if obj.qty_allocated_onhand > 0:
                raise osv.except_osv(_('Error !'), _('cannot delete this line /n, because find some allocated onhand in this line. unallocated it to process.'))
            so_id = sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context).order_id.id
            amount_untaxed = sale_order_obj.browse(cr, uid, so_id, context=context).amount_untaxed
            amount_tax = sale_order_obj.browse(cr, uid, so_id, context=context).amount_total
            amount_total = sale_order_obj.browse(cr, uid, so_id, context=context).amount_total
            sol_val = sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context=context)
            line_untax =  sol_val.price_subtotal
            line_tax = sale_order_obj._amount_line_tax(cr, uid, sol_val, context=context)
            sale_order_line_obj.write(cr, uid, context.get(('active_ids'), []), {'product_uom_qty': 0}, context=context)
            sale_order_line_obj.unlink(cr, uid, context.get(('active_ids'), []))
        return {'type': 'ir.actions.act_window_close'}
    
    _columns = {
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True),
        'company_id':fields.many2one('res.company', 'Company', required=True),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True),
        'date_order': fields.date('Date', required=True),
        'product_customer_id':fields.many2one('product.customer', 'Customer Part No.', required=True, change_default=True),
        'product_supplier_id':fields.many2one('product.supplier', 'Supplier Branch Name.', required=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)]),
        'location_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', required=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'spq': fields.float('SPQ (*)', help="Standard Packaging Qty"),
        'moq': fields.float('MOQ (*)', help="Minimum Order Qty"),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True),
        'product_uom_qty': fields.float('Quantity (UoM)', digits_compute= dp.get_precision('Product UoS'), required=True),
        'effective_date': fields.date('Effective Date', required=True, help="Effective date is impact with the price of the product.", select=True),
        'customer_original_date': fields.date('Customer Original Date (COD)', required=True, select=True),
        'customer_rescheduled_date': fields.date('Customer Rescheduled Date (CRD) (*)', required=True, select=True),
        'notes': fields.text('Notes'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'confirmation_date': fields.date('Confirmation Date (ETD)', required=True, ),
#        'tax_id': fields.one2many('account.tax', 'sale_order_tax', 'order_line_id', 'tax_id', 'Taxes'),
    }

add_so_line_wzd()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
