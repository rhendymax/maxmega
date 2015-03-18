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

class sale_order(osv.osv):
    _inherit = "sale.order"
    _description = "Sales Order"

    _columns = {
        'partner_id2': fields.many2one('res.partner', 'Customer', required=True),
        'date_so_line': fields.date('Date For So Lines', required=True),
    }

#     _defaults = {
#         'effective_date': fields.date.context_today,
#         'customer_original_date': fields.date.context_today,
#         'customer_rescheduled_date': fields.date.context_today,
#     }

    def create(self, cr, user, vals, context=None):
        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            vals.update({'partner_id': partner_id})
        new_id = super(sale_order, self).create(cr, user, vals, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            vals.update({'partner_id': partner_id})
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def onchange_partner_id(self, cr, uid, ids, part, part2, order_line):
        if order_line:
            part = part2

        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
        if part:
#            raise osv.except_osv(_('Debug!'), _(str(order_line)))
            if 'value' in result:
                result['value'].update({'partner_id': part, 'partner_id2' : part})
            else:
                result['value'] = {'partner_id': part, 'partner_id2' : part}
        return result

#=============================
#       From so_workflowchange
#=============================

#    def _shipped_rate2(self, cr, uid, ids, name, arg, context=None):
#        if not ids: return {}
#        res = {}
#        res2 = {}
#        picking_ids = []
#        stock_move_obj = self.pool.get('stock.move')
#
#        for obj in self.browse(cr, uid, ids, context=context):
#            res[obj.id] = [0.0,0.0]
#            sale_id = obj.id
#            for line in obj.order_line:
#                res[sale_id][1] += line.product_uom_qty or 0.0
#                cr.execute('Select coalesce(sum(product_qty)::decimal, 0.0) as total from stock_move where sale_line_id=%s', (line.id,))
#                res[sale_id][0] += cr.fetchone()[0]
##            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(line.id, total))
#            if res[obj.id][0] == 0:
#                res2[obj.id] = 0.0
#            else:
#                res2[obj.id] = 100.0 * res[obj.id][0] / res[obj.id][1]
#        return res2
sale_order()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    _description = "Sales Order Line"
#=============================
#       For Line Numbers
#=============================
#     def _get_all_so(self, cr, uid, ids, name, args, context=None):
#         res = {}
#         line = 0
#         for sol in self.browse(cr, uid, ids, context=context):
#             print sol.id
#             line +=1
#             res[sol.id] = line
# #             
#         return res
# END

    def create(self, cr, uid, vals, context=None):
        if vals.get('product_supplier_id'):
            vals.update({'product_supplier_id2': vals['product_supplier_id']})
        if vals.get('product_id'):
            vals.update({'product_id2': vals['product_id']})
        vals.update({'save_done': True})
        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        print "write"
        if vals.get('product_supplier_id'):
            vals.update({'product_supplier_id2': vals['product_supplier_id']})
        if vals.get('product_id'):
            vals.update({'product_id2': vals['product_id']})
        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)

    def onchange_product_customer_id(self, cr, uid, ids, company_id, product_customer_id, 
            effective_date, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False,
            packaging=False, fiscal_position=False,
            flag=False, context=None):
        """
        onchange handler of product_id.
        """
        #raise osv.except_osv(_('Debug!'), _('xxxxx'))

        if context is None:
            context = {}
        result = {}
        domain = {}
        warning = {}
        res_final = {'value':result, 'domain':domain, 'warning':warning}
        warning_msgs = ''
        so_date = context.get('date_on_so', False)
#         eff_date = context.get('eff_date', False)
#         etd = context.get('etd', False)
        cod = context.get('cod', False)
        crd = context.get('crd', False)
        if not so_date:
            raise osv.except_osv(_('Error!'), _('Please select Date For So Lines!'))
#         if not etd:
#             res_final['value']['confirmation_date'] = so_date
        if not cod:
            res_final['value']['customer_original_date'] = so_date
        if not crd:
            res_final['value']['customer_rescheduled_date'] = so_date

#         if not eff_date:
#             effective_date = so_date
#             res_final['value']['effective_date'] = so_date

        if not product_customer_id:
            return res_final

        product_customer_obj = self.pool.get('product.customer')
        product_product_obj = self.pool.get('product.product')

        # - check for the presence of partner_id and pricelist_id
        if not partner_id:
            warn_msg = _("Please set one Customer before choosing a Customer Part No.")
            warning_msgs += _("No Partner found ! :") + warn_msg +"\n\n"
        if not effective_date:
            warn_msg = _("Please set effective date before choosing a Customer Part No.")
            warning_msgs += _("No Effective Date found ! :") + warn_msg +"\n\n"
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }
            res_final['value']['customer_id'] = False
            res_final['warning'] = warning
            return res_final
        product_customer = product_customer_obj.browse(cr, uid, product_customer_id, context=context)
        product_id = product_customer.product_id.id
        res_final['value']['product_id'] = product_id
        res_final['value']['product_id2'] = product_id
        if product == product_id:
            return self.product_id_change2(cr, uid, ids, company_id, product_customer_id, effective_date, pricelist, product,
                qty, uom, qty_uos, uos, name,
                partner_id, lang, update_tax,
                date_order, packaging, fiscal_position,
                flag, context=context) 
        return res_final

    def spq_onchange(self, cursor, user, ids, product, context=None):
        product_product_obj = self.pool.get('product.product')
        spq = 0.00
        if product:
            spq = product_product_obj.browse(cursor, user, product, context=context).spq
        return {'value': {'spq': spq}}

    def moq_onchange(self, cursor, user, ids, product_customer_id, context=None):
        product_customer_obj = self.pool.get('product.customer')
        moq = 0.00
        if product_customer_id:
            moq = product_customer_obj.browse(cursor, user, product_customer_id, context=context).moq
        return {'value': {'moq': moq}}

    def cod_onchange(self, cursor, user, ids, cod, context=None):
        return {'value': {'customer_rescheduled_date': cod}}

    def product_supplier_id2_onchange(self, cursor, user, ids, product_supplier_id, context=None):
        return {'value': {'product_supplier_id2': product_supplier_id}}

    def product_id2_onchange(self, cursor, user, ids, product_customer_id, context=None):
        product_customer_obj = self.pool.get('product.customer')
        product_id2 = False
        if product_customer_id:
            product_id2 = product_customer_obj.browse(cursor, user, product_customer_id, context=context).product_id.id
        return {'value': {'product_id2': product_id2}}

    def product_id_change2(self, cr, uid, ids, company_id, product_customer_id,
            effective_date, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False,
            packaging=False, fiscal_position=False,
            flag=False, context=None):
        context = context or {}
        lang = lang or context.get('lang',False)
        warning = {}
        warning_msgs = ''
        if not  partner_id:
            warn_msg = _('Please set one Customer before choosing a Product.')
            warning_msgs += _("No Customer Defined ! : ") + warn_msg + "\n\n"
            return {'value': {'th_weight': 0, 'product_packaging': False,
                    'product_uos_qty': qty}, 'domain': {'product_uom': [],
                    'product_uos': []}, 'warning': warning_msgs}

        partner_obj = self.pool.get('res.partner')

#Developer Code Start
        product_customer_price = self.pool.get('product.customer.price')
        product_customer_obj = self.pool.get('product.customer')
        product_supplier_obj = self.pool.get('product.supplier')
        product_pricelist = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        product_product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        product_customer_upper_limit_obj = self.pool.get('product.customer.upper.limit')
#Developer Code Stop

        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}

#Developer Code Start
        if not product_customer_id:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}

        if not effective_date:
            warn_msg = _('Please set effective date before choosing a Product.')
            warning_msgs += _("No Effective Date found ! : ") + warn_msg + "\n\n"
            return {'value': {'th_weight': 0, 'product_packaging': False,
                    'product_uos_qty': qty}, 'domain': {'product_uom': [],
                    'product_uos': []}, 'warning': warning_msgs}


#Developer Code Stop

        if not product:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        uom = False
#Developer Code Start
        res = self.product_packaging_change2(cr, uid, ids, company_id, product_customer_id,
                                             effective_date, pricelist,
                                             product, qty, uom, partner_id,
                                             packaging, context=context)

        product_customer_val = product_customer_obj.browse(cr, uid, product_customer_id, context=context)
#Developer Code Stop

        result = res.get('value', {})
        warning_msgs = res.get('warning') and res['warning']['message'] or ''
        product_product = product_product_obj.browse(cr, uid, product, context=context)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_product.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_product.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_product.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        if product_product.description_sale:
            result['notes'] = product_product.description_sale
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['delay'] = (product_product.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_product.taxes_id)
            result.update({'type': product_product.procure_method})

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_product.id], context=context_partner)[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_product.uom_id.id
            if product_product.uos_id:
                result['product_uos'] = product_product.uos_id.id
                result['product_uos_qty'] = qty * product_product.uos_coeff
                uos_category_id = product_product.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_product.weight
            domain = {'product_uom':
                        [('category_id', '=', product_product.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_product.uom_id and product_product.uom_id.id
            result['product_uom_qty'] = qty_uos / product_product.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_product.weight
        elif uom: # whether uos is set or not
            default_uom = product_product.uom_id and product_product.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_product.uos_id:
                result['product_uos'] = product_product.uos_id.id
                result['product_uos_qty'] = qty * product_product.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_product.weight        # Round the quantity up

        if not uom2:
            uom2 = product_product.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warn_msg = _("Couldn't find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
#            else:
#                result.update({'price_unit': price})
            else:
                #Developer Code Start
                product_customer_price_ids = product_customer_price.search(cr, uid, [('product_customer_id','=',product_customer_id),('effective_date','<=',effective_date)], order='effective_date DESC')
                if product_customer_price_ids:
                    product_customer_price_id = product_customer_price.browse(cr, uid, product_customer_price_ids[0], context=context)
                    company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
                    ptype_src = company.currency_id.id
                    currency_id = product_pricelist.browse(cr, uid, pricelist, context=context).currency_id.id
                    product_id = product_product_obj.browse(cr, uid, product, context=context)
                    product_uom_po_id = product_id.uom_po_id.id
                    if not uom:
                        uom = product_uom_po_id
                    if product_id.uom_id.category_id.id != product_uom_obj.browse(cr, uid, uom, context=context).category_id.id:
                        warn_msg = _("Selected UOM does not belong to the same category as the product UOM.")

                        warning_msgs += _("UOM Error ! :") + warn_msg +"\n\n"
                        uom = product_uom_po_id
                    default_uom = product_product_obj.browse(cr, uid, product, context=context).product_tmpl_id.uom_id.id
                    domain.update({'product_uom': [('category_id', '=', product_id.uom_id.category_id.id)]})
                    qty_overall = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
#                    raise osv.except_osv(_('Debug!'), _(str(qty_overall)))

                    product_customer_upper_limit_ids = product_customer_upper_limit_obj.search(cr, uid, [('product_customer_price_id','=',product_customer_price_id.id),('qty','<=',qty_overall)], order='qty DESC')
                    if product_customer_upper_limit_ids:
                        product_customer_upper_limit_id = product_customer_upper_limit_obj.browse(cr, uid, product_customer_upper_limit_ids[0], context=context)
                        price = currency_obj.compute(cr, uid, product_customer_val.pricelist_id.currency_id.id, ptype_src, product_customer_upper_limit_id.unit_cost, round=False)
                    else:
                        price = currency_obj.compute(cr, uid, product_customer_val.pricelist_id.currency_id.id, ptype_src, product_customer_price_id.unit_cost, round=False)
                    price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                    price = product_uom_obj._compute_price(cr, uid, default_uom, price, uom)
                    price = product_product_obj.round_p(cr, uid, price, 'Sale Price')
                else:
                    warn_msg = _("Couldn't find price unit at customer code.")

                    warning_msgs += _("No price unit found ! :") + warn_msg +"\n\n"

                    price = 0.00
                result.update({'price_unit': price})
#Developer Code Stop
#        raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(result,))
#Developer Code Start
        if product_customer_id:
            product_supplier_id = False
            product_customer_obj = self.pool.get('product.customer')
            product_customer = product_customer_obj.browse(cr, uid, product_customer_id, context=context)
            if product_customer.supplier_key_id:
                product_supplier_id = product_customer.supplier_key_id.id
            else:
                product_supplier_ids = product_supplier_obj.search(cr, uid, [('product_id','=',product),('default_key', '=', True)])
                if product_supplier_ids:
                    if len(product_supplier_ids) != 1:
                        product_supplier_id = False
                        warn_msg = _("Multiple Supplier Key found at Supplier Price Methodology.\n"
                                     "Please Select 1 Default Supplier Key only.")

                        warning_msgs += _("Multiple Supplier Key line found ! :") + warn_msg +"\n\n"
                    product_supplier_id = product_supplier_ids[0]
                else:
                    product_supplier_id = False
                    warn_msg = _("no supplier key found in both.\n"
                                  "(default supplier key at supplier price methodology and customer price methodology (supplier key)).")

                    warning_msgs += _("no supplier key found ! :") + warn_msg +"\n\n"
            if result.get('product_supplier_id'):
                result.update({'product_supplier_id2': product_supplier_id})
                result.update({'product_supplier_id': product_supplier_id})
            else:
                result['product_supplier_id2'] = product_supplier_id
                result['product_supplier_id'] = product_supplier_id
#Developer Code Stop

        if warning_msgs:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : warning_msgs
                    }
#        raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(result,))
        return {'value': result, 'domain': domain, 'warning': warning}

    def product_uom_change2(self, cursor, user, ids, company_id,
                            product_customer_id, effective_date,
                            pricelist, product, qty=0,
                            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                            lang=False, update_tax=True, date_order=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])

        res = self.product_id_change2(cursor, user, ids, company_id, product_customer_id,
                                      effective_date, pricelist, product,
                                      qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                                      partner_id=partner_id, lang=lang, update_tax=update_tax,
                                      date_order=date_order, context=context)
#        if 'product_uom' in res['value']:
#            del res['value']['product_uom']
        if not uom:
            res['value']['price_unit'] = 0.0
        return res

    def product_packaging_change2(self, cr, uid, ids, company_id, product_customer_id,
                                  effective_date, pricelist, product, qty=0, uom=False,
                                   partner_id=False, packaging=False, flag=False, context=None):
        if not product:
            return {'value': {'product_packaging': False}}
        product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')
        pack_obj = self.pool.get('product.packaging')
        warning = {}
        result = {}
        warning_msgs = ''
        if flag:
            res = self.product_id_change2(cr, uid, ids, company_id=company_id,
                                          product_customer_id=product_customer_id,
                                          effective_date=effective_date, pricelist=pricelist,
                                          product=product, qty=qty, uom=uom, partner_id=partner_id,
                                          packaging=packaging, flag=False, context=context)
            warning_msgs = res.get('warning') and res['warning']['message']

        products = product_obj.browse(cr, uid, product, context=context)
        if not products.packaging:
            packaging = result['product_packaging'] = False
        elif not packaging and products.packaging and not flag:
            packaging = products.packaging[0].id
            result['product_packaging'] = packaging

        if packaging:
            default_uom = products.uom_id and products.uom_id.id
            pack = pack_obj.browse(cr, uid, packaging, context=context)
            q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
#            qty = qty - qty % q + q
            if qty and (q and not (qty % q) == 0):
                ean = pack.ean or _('(n/a)')
                qty_pack = pack.qty
                type_ul = pack.ul
                if not warning_msgs:
                    warn_msg = _("You selected a quantity of %d Units.\n"
                                "But it's not compatible with the selected packaging.\n"
                                "Here is a proposition of quantities according to the packaging:\n"
                                "EAN: %s Quantity: %s Type of ul: %s") % \
                                    (qty, ean, qty_pack, type_ul.name)
                    warning_msgs += _("Picking Information ! : ") + warn_msg + "\n\n"
                warning = {
                       'title': _('Configuration Error !'),
                       'message': warning_msgs
                }
            result['product_uom_qty'] = qty

        return {'value': result, 'warning': warning}

    _defaults = {
        'effective_date': fields.date.context_today,
    }

    _columns = {
        'spq': fields.float('SPQ (*)', help="Standard Packaging Qty"),
        'moq': fields.float('MOQ (*)', help="Minimum Order Qty"),
#         'line_number': fields.function(_get_all_so, string='No', type='integer'),
        'product_id2': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)]),
        'product_customer_id':fields.many2one('product.customer', 'Customer Part No.', required=True, change_default=True, readonly=True, states={'draft':[('readonly',False)]}),
        'product_supplier_id':fields.many2one('product.supplier', 'Supplier Branch Name.', required=True, invisible=True),
        'product_supplier_id2':fields.many2one('product.supplier', 'Supplier Branch Name. (*)'),
        'effective_date': fields.date('Effective Date', required=True, help="Effective date is impact with the price of the product.", select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'customer_original_date': fields.date('Customer Original Date (COD)', required=True, select=True),
        'customer_rescheduled_date': fields.date('Customer Rescheduled Date (CRD) (*)', required=True, select=True),
        'save_done': fields.boolean('Save Done', invisible=True),
        'reschedule_ids': fields.one2many('change.cod', 'sale_order_line_id', 'Reschedule History', readonly=True,),
        #RT 20141021
        'confirmation_date': fields.date('Confirmation Date (ETD)', ),
    }

sale_order_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
