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
from tools.translate import _
import re

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    def button_dummy2(self, cr, uid, ids, context=None):
        return True
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, partner_id2, partner_child_id, order_line):
        if order_line:
            partner_id = partner_id2
        result = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id:
            return result
        addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery', 'invoice', 'contact'])
        partner_address_obj = self.pool.get('res.partner.address')
#        ship_address = self.pool.get('res.partner.address').
        ship_address = partner_address_obj.browse(cr, uid, partner_address_obj.search(cr, uid, [('loc_address','=',True)]), context=None)
        default_ship_addr = False
        for sh in ship_address:
            if sh.default_key == True:
                if not default_ship_addr:
                    default_ship_addr = sh.id
        result['value'].update({
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': default_ship_addr,
            })

        res_partner_obj = self.pool.get('res.partner')
        partner_child_ids = []
        partner = res_partner_obj.browse(cr, uid, partner_id, context=None)
        partner_child = partner.pchild_ids

        for pc in partner_child:
            partner_child_ids.append(pc.id)

        if 'domain' in result:
            result['domain'].update({'partner_child_id': [('id', 'in', partner_child_ids)]})
        else:
            result['domain'] = {'partner_child_id': [('id', 'in', partner_child_ids)]}


        if partner_child_id:
            if partner_child_id not in partner_child_ids:
                result['value'].update({'partner_child_id': False})
                if 'warning' in result:
                    if 'message' in result['warning']:
                        mess = result['warning']['message']
                        result['warning'].update({'message': _( mess + '\n & \n' +'The selected Supplier Branch is not belong to Supplier ' + str(partner.name) + ' !')})
                    else:
                        result['warning'].update({'message': _('The selected Supplier Branch is not belong to Supplier ' + str(partner.name) + ' !')})
                else:
                    result['warning'] = {'title': _('Warning'), 'message': _('The selected Supplier Branch is not belong to Supplier ' + str(partner.name) + ' !')}
        else:
            if partner_child_ids:
                result['value'].update({'partner_child_id': partner_child_ids[0]})
            else:
                result['value'].update({'partner_child_id': False})

#        raise osv.except_osv(_('Debug!'), _(str(result)))
        result['value'].update({'partner_id2': partner_id, 'partner_id' : partner_id})
        return result

    def onchange_partner_child_id(self, cr, uid, ids, partner_child_id, partner_child_id2, order_line):
        res = {}
        if order_line:
            partner_child_id = partner_child_id2
        res['value'] = {'partner_child_id2': partner_child_id, 'partner_child_id' : partner_child_id}
        return res

    _columns = {
        'partner_id2':fields.many2one('res.partner', 'Supplier2', required=True,),
        'partner_child_id': fields.many2one('res.partner.child', 'Supplier Branch', required=True),
        'partner_child_id2': fields.many2one('res.partner.child', 'Supplier Branch', required=True),
        'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True, required=True, help="Invoice address for current purchase order."),
        'partner_order_id': fields.many2one('res.partner.address', 'Ordering Contact', readonly=True, required=True,),
        'partner_shipping_id': fields.many2one('res.partner.address', 'Shipping Address', readonly=True, required=True, states={'draft': [('readonly', False)]},),
        'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', required=True, readonly=True, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'location_id': fields.many2one('stock.location', 'Destination', domain=[('usage','<>','view')]),
    }

    def create(self, cr, user, vals, context=None):
        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, user, partner_id, context=None)
            addr = self.pool.get('res.partner').address_get(cr, user, [partner_id], ['delivery', 'invoice', 'contact'])
            vals.update({'partner_id': partner_id,
                         'partner_invoice_id': addr['invoice'],
                         'partner_order_id': addr['contact'],
                         'pricelist_id': partner.property_product_pricelist_purchase.id,
                         })
        if 'partner_child_id2' in vals:
            partner_child_id = vals['partner_child_id2']
            vals.update({'partner_child_id': partner_child_id})
        new_id = super(purchase_order, self).create(cr, user, vals, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        po_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        partner_id2 = ('partner_id2' in vals and vals['partner_id2']) or (self.pool.get('purchase.order').browse(cr, uid, po_id, context=None).partner_id.id) or False
        if 'partner_id2' in vals:
            partner_id22 = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id22, context=None)
            addr = self.pool.get('res.partner').address_get(cr, uid, [vals['partner_id2']], ['delivery', 'invoice', 'contact'])
            vals.update({
                         'partner_id': partner_id22,
                         'partner_invoice_id': addr['invoice'],
                         'partner_order_id': addr['contact'],
                         'pricelist_id': partner.property_product_pricelist_purchase.id,
                         })
        if 'partner_child_id2' in vals:
            partner_child_id = vals['partner_child_id2']
            vals.update({'partner_child_id': partner_child_id})
        return super(purchase_order, self).write(cr, uid, ids, vals, context=context)

purchase_order()

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    def onchange_product_uom2(self, cr, uid, ids, company_id, partner_child_id, pricelist_id, product_id, qty, uom_id,
            partner_id, original_request_date=False, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, notes=False, context=None):
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or'', 'product_uom' : uom_id or False}}
        return self.onchange_product_id2(cr, uid, ids, company_id, partner_child_id, pricelist_id, product_id, qty, uom_id,
            partner_id, original_request_date=original_request_date, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes, context=context)

    def onchange_product_id2(self, cr, uid, ids, company_id, partner_child_id,
                             pricelist_id, product_id, qty, uom_id,
                             partner_id, original_request_date=False,
                             date_order=False, fiscal_position_id=False,
                             date_planned=False, name=False, price_unit=False,
                             notes=False, context=None):
#        raise osv.except_osv(_('UserErrorxx2'),
#                _(str('xxxx')))
        if not partner_child_id:
            raise osv.except_osv(_('No Supplier Child!'), _('You have to select a Supplier Branch in the purchase form !\nPlease set one supplier child before choosing a product.'))
        if not partner_id:
            raise osv.except_osv(_('No Partner!'), _('You have to select a partner in the purchase form !\nPlease set one partner before choosing a product.'))
        if not original_request_date:
            raise osv.except_osv(_('No Original Request Date Found!'), _('You have to input a original request date in the purchase line form !\nPlease input original request date before choosing a product.'))


        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res
        partner_child_obj = self.pool.get('res.partner.child')
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price = self.pool.get('product.supplier.price')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')
        product_pricelist = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')

        product_supplier_ids = product_supplier_obj.search(cr, uid, [('partner_child_id','=',partner_child_id)])
        partner_child_name = partner_child_obj.browse(cr, uid, partner_child_id, context=context).name

        product_ids = []
        for pr in product_supplier_ids:
            product_id2 = product_supplier_obj.browse(cr, uid, pr, context=context).product_id.id
            product_ids.append(product_id2)

        res['domain'] = {'product_id': [('id','in',product_ids)]}
#        raise osv.except_osv(_('Debug!'), _(str(product_ids)))

        if product_id not in product_ids:
            res['value'].update({'product_id': False})
            res['warning'] = {'title': _('Warning'), 'message': _('The selected Supplier Part No is not belong to Supplier Branch ' + str(partner_child_name) + ' !')}
            return res
        if not pricelist_id:
            raise osv.except_osv(_('No Pricelist !'), _('You have to select a pricelist or a supplier in the purchase form !\nPlease set one before choosing a product.'))

        product_vals = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned, name=name, price_unit=price_unit, notes=notes, context=context)

        product_supplier_id = product_supplier_obj.search(cr, uid, [('product_id','=',product_id),('partner_child_id','=',partner_child_id)])[0]
        product_supplier_val = product_supplier_obj.browse(cr, uid, product_supplier_id, context=context)
        product_supplier_price_ids = product_supplier_price.search(cr, uid, [('product_supplier_id','=',product_supplier_id),('effective_date','<=',original_request_date)], order='effective_date DESC')

        spq = product_product.browse(cr, uid, product_id, context=context).spq
        moq = product_supplier_val.moq
        product_vals['value'].update({
                             'spq': spq,
                             'moq': moq,
                             })

        uom_id = product_vals['value']['product_uom']
        default_uom = product_product.browse(cr, uid, product_id, context=context).product_tmpl_id.uom_id.id
        if qty > 0:
            qty_overall = product_uom._compute_qty(cr, uid, uom_id, qty, default_uom)
#            raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(qty_overall,))


            if qty_overall < moq:
                if 'warning' in product_vals:
                    if 'message' in product_vals['warning']:
                        message = product_vals['warning']['message']
                        message = message + '\n & \n the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                        product_vals['warning'].update({
                                         'message': message,
                                         })
                    else:
                        message = 'the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                        product_vals['warning'].update({
                                        'title': _('Configuration Error !'),
                                        'message': message,
                                        })
                else:
                    warning = {
                               'title': _('Configuration Error !'),
                               'message' : 'the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                               }
                    product_vals['warning'] = warning

            if qty_overall < spq:
                qty_overall = 0
            if qty_overall%spq != 0:
                qty_overall= 0
            if qty_overall == 0:
                if 'warning' in product_vals:
                    if 'message' in product_vals['warning']:
                        message = product_vals['warning']['message']
                        message = message + '\n & \n the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                        product_vals['warning'].update({
                                         'message': message,
                                         })
                    else:
                        message = 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                        product_vals['warning'].update({
                                        'title': _('Configuration Error !'),
                                        'message': message,
                                        })
                else:
                    warning = {
                               'title': _('Configuration Error !'),
                               'message' : 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                               }
                    product_vals['warning'] = warning
        else:
            qty_overall = 0

        if product_supplier_price_ids:
            product_supplier_price_id = product_supplier_price.browse(cr, uid, product_supplier_price_ids[0], context=context)
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)

            ptype_src = company.currency_id.id
            currency_id = product_pricelist.browse(cr, uid, pricelist_id, context=context).currency_id.id

#            raise osv.except_osv(_('Debug !'), _(str(qty_overall)))
            product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',qty_overall)], order='qty DESC')
            
            if product_supplier_upper_limit_id:
                product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
            else:
                price = currency_obj.compute(cr, uid, product_supplier_val.pricelist_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
            price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
            price = product_uom._compute_price(cr, uid, default_uom, price, uom_id)
            price = product_product.round_p(cr, uid, price, 'Purchase Price',)
        else:
            product_vals['warning'] = {'title': _('Warning'), 'message': _('cannot find unit cost price at supplier code')}
            price = 0.00

        product_vals['value'].update({'price_unit': price, 'product_qty' : qty_overall})

        return product_vals

    def spq_onchange(self, cursor, user, ids, product, context=None):
        product_product_obj = self.pool.get('product.product')
        spq = 0.00
        if product:
            spq = product_product_obj.browse(cursor, user, product, context=context).spq
        return {'value': {'spq': spq}}

    def moq_onchange(self, cursor, user, ids, product_id, partner_child_id, context=None):
        if not partner_child_id:
            return {'value' : {'moq':0},
                    'warning' : {'title': _('No Supplier Child'), 'message': _('You have to select a Supplier Branch in the purchase form !\nPlease set one supplier child before choosing a product.')}
                    }
        moq = 0.00
        product_supplier_obj = self.pool.get('product.supplier')
        if product_id:
            product_supplier_id = product_supplier_obj.search(cursor, user, [('product_id','=',product_id),('partner_child_id','=',partner_child_id)])[0]
            product_supplier_val = product_supplier_obj.browse(cursor, user, product_supplier_id, context=context)
            moq = product_supplier_val.moq

        return {'value': {'moq': moq}}

    _columns = {
        'original_request_date': fields.date('Effective Date', required=True, select=True),
        'original_request_date2': fields.date('Original Request Date', required=True, select=True),
        'estimated_time_departure': fields.date('Estimated Time Departure', select=True),
        'estimated_time_arrive': fields.date('Estimated Time Arrive', select=True),
        'done_savedrecords': fields.boolean('Saved Records'),
        'spq': fields.float('SPQ (*)', help="Standard Packaging Qty"),
        'moq': fields.float('MOQ (*)', help="Minimum Order Qty"),
    }

    _defaults = {
        'original_request_date2': fields.date.context_today,
        'original_request_date': fields.date.context_today,
        'product_qty': lambda *a: 0,
    }


    def create(self, cr, user, vals, context=None):
        vals['done_savedrecords'] = True
        new_id = super(purchase_order_line, self).create(cr, user, vals, context)
        return new_id

purchase_order_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
