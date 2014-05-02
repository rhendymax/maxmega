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

class po_value(osv.osv_memory):
    _name = 'po.value'
    _description = 'Purchase Order Value'

    def _amount_line(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for line in self.browse(cr, uid, ids, context=context):
            taxes_id = []
            taxes = tax_obj.compute_all(cr, uid, taxes_id, line.price_unit, line.quantity)
            cur = line.so_po_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    def onchange_ord(self, cr, uid, ids, original_request_date, product_id, partner_child_id, pricelist_id, quantity_order, context=None):
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price_obj = self.pool.get('product.supplier.price')
        res_company_obj = self.pool.get('res.company')
        product_pricelist_obj = self.pool.get('product.pricelist')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')
        currency_obj = self.pool.get('res.currency')

        warning = {}
        result = {}
        warning_msgs = ''

        product_supplier_id = product_supplier_obj.search(cr, uid, [('product_id','=',product_id),('partner_child_id','=',partner_child_id)])[0]
        product_supplier_vals = product_supplier_obj.browse(cr, uid, product_supplier_id, context=context)
        product_supplier_price_ids = product_supplier_price_obj.search(cr, uid, [('product_supplier_id','=',product_supplier_id),('effective_date','<=',original_request_date)], order='effective_date ASC')
        if product_supplier_price_ids:
            product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, product_supplier_price_ids[0], context=context)
            company = res_company_obj.browse(cr, uid, res_company_obj._company_default_get(cr, uid, 'purchase.order', context=context), context=context)
            ptype_src = company.currency_id.id
            currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id
            product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',quantity_order)], order='qty DESC')
            if product_supplier_upper_limit_id:
                product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                price = currency_obj.compute(cr, uid, product_supplier_vals.pricelist_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
            else:
                price = currency_obj.compute(cr, uid, product_supplier_vals.pricelist_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
            price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
            result['price_unit'] = price
        else:
            product_supplier_price_ids2 = self.pool.get('product.supplier.price').search(cr, uid, [('product_supplier_id','=',product_supplier_id)], order='effective_date ASC')
            if product_supplier_price_ids2:
                product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, product_supplier_price_ids2[0], context=context)
                company = res_company_obj.browse(cr, uid, res_company_obj._company_default_get(cr, uid, 'purchase.order', context=context), context=context)
                ptype_src = company.currency_id.id
                currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id
                product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',quantity_order)], order='qty DESC')
                if product_supplier_upper_limit_id:
                    product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                    price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
                else:
                    price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
                price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)

                warn_msg = _('cannot find unit cost price at Supplier Part No with Original Request Date : ' + str(original_request_date))
                warning_msgs += _("no Unit Cost Price found ! : ") + warn_msg +"\n\n"

                result['price_unit'] = price
                result['original_request_date'] = product_supplier_price_id.effective_date

            else:
                warn_msg = _('no effective date found in Supplier Part No')
                warning_msgs += _("no Effective Date found ! : ") + warn_msg +"\n\n"

                result['price_unit'] = 0.00
                result['original_request_date'] = False

        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }

        return {'value': result, 'warning': warning}

    def onchange_quantity_order(self, cr, uid, ids, original_request_date,
                                product_id, partner_child_id, pricelist_id,
                                quantity, quantity_order, context=None):
        if not original_request_date:
            return {'value': {'price_unit': 0.00}}
        warning = {}
        result = {}
        warning_msgs = ''
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price_obj = self.pool.get('product.supplier.price')
        res_company_obj = self.pool.get('res.company')
        product_pricelist_obj = self.pool.get('product.pricelist')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')
        currency_obj = self.pool.get('res.currency')
        if quantity_order > 0:
            if quantity_order > quantity:
                warn_msg = _("the Order Quantity entered cannot more than non allocated quantity.")
                warning_msgs += _("Qty Error ! : ") + warn_msg +"\n\n"
                quantity_order = quantity
                result['quantity_order'] = quantity
        else:
            quantity_order = quantity
            result['quantity_order'] = quantity


        product_supplier_id = product_supplier_obj.search(cr, uid, [('product_id','=',product_id),('partner_child_id','=',partner_child_id)])[0]
        product_supplier_val = product_supplier_obj.browse(cr, uid, product_supplier_id, context=context)
        product_supplier_price_ids = product_supplier_price_obj.search(cr, uid, [('product_supplier_id','=',product_supplier_id),('effective_date','<=',original_request_date)], order='effective_date ASC')
        if product_supplier_price_ids:
            product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, product_supplier_price_ids[0], context=context)
            company = res_company_obj.browse(cr, uid, res_company_obj._company_default_get(cr, uid, 'purchase.order', context=context), context=context)
            ptype_src = company.currency_id.id
            currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id
            product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',quantity_order)], order='qty DESC')
            if product_supplier_upper_limit_id:
                price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
            else:
                price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
            price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
            result['price_unit'] = price

        else:
            warn_msg = _("no effective date found in Supplier Part No.")
            warning_msgs += _("no effective date found ! : ") + warn_msg +"\n\n"

            result['price_unit'] = 0.00
            result['original_request_date'] = False

        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }

        return {'value': result, 'warning': warning}

    _columns = {
        'wizard_id' : fields.many2one('so.to.po', string="Wizard", ondelete='cascade'),
        'sale_id': fields.many2one('sale.order', 'Sale Order', required=True, ondelete='cascade'),
        'partner_child_id' : fields.many2one('res.partner.child', 'Supplier Child', select=1, required=True),
        'partner_id': fields.many2one('res.partner', 'Supplier', required=True),
        'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'product_id' : fields.many2one('product.product', string="Supplier Part No", required=True),
        'real_quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'), required=True),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price'), readonly=True),
        'move_id' : fields.many2one('sale.order.line', "Order Line", ondelete='cascade'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Purchase Price')),
        'quantity_order' : fields.float("Quantity Order", digits_compute=dp.get_precision('Product UoM')),
        'original_request_date': fields.date('Original Request Date', required=True),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', help="Location where the system will stock the finished products.", readonly=True),
    }

po_value()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
