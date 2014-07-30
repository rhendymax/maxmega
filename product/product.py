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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import re
import decimal_precision as dp

class product_template(osv.osv):
    _inherit = "product.template"
    _description = "Product Template"

    _columns = {
        'name': fields.char('Supplier Part No', size=128, required=True, translate=True, select=True),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(name)', 'Supplier Part No must be unique per Product!'),
    ]

product_template()


class product_product(osv.osv):
    _inherit = "product.product"
    _description = "Product"

    def _get_supplier_lines(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for prod in self.browse(cr, uid, ids, context=context):
            id = prod.id
            res[id] = []
            price_ids = []
            if prod.supplierm_ids:
                for supplierm_ids in prod.supplierm_ids:
                     if supplierm_ids.supplierprice_ids:
                         for supplierprice_ids in supplierm_ids.supplierprice_ids:
                             price_ids.append(supplierprice_ids.id)
                res[id] = price_ids
        return res

    def _get_customer_lines(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for prod in self.browse(cr, uid, ids, context=context):
            id = prod.id
            res[id] = []
            price_ids = []
            if prod.customerm_ids:
                for customerm_ids in prod.customerm_ids:
                     if customerm_ids.customerprice_ids:
                         for customerprice_ids in customerm_ids.customerprice_ids:
                             price_ids.append(customerprice_ids.id)
                res[id] = price_ids
        return res

    _columns = {
        'default_code' : fields.char('Internal Part No', size=64, select=True, required=True),
        'supplierm_ids' : fields.one2many('product.supplier', 'product_id', 'Supplier Detail'),
        'customerm_ids' : fields.one2many('product.customer', 'product_id', 'Customer Detail'),
        'suppplier_methodology_ids':fields.function(_get_supplier_lines, type='many2many', relation='product.supplier.price', string='Supplier Price Methodology'),
        'customer_methodology_ids':fields.function(_get_customer_lines, type='many2many', relation='product.customer.price', string='Customer Price Methodology'),
    }

    def round_p(self, cr, uid, move_price, name, context=None):
        decimal_precision_obj = self.pool.get('decimal.precision')
        decimal_precision_id = decimal_precision_obj.browse(cr, uid, decimal_precision_obj.search(cr, uid, [('name','=',name)]), context=None)
        if decimal_precision_id:
            decimal_precision_id = decimal_precision_id[0]
            return round(move_price, decimal_precision_id.digits)
        else:
            return round(move_price)
    
    def create(self, cr, uid, data, context=None):
        product_supplier_obj = self.pool.get('product.supplier')
        res_partner_child_obj = self.pool.get('res.partner.child')
        if 'supplierm_ids' in data:
            recordcount = 0
            default_k = 0
            branchname = []
            for lines in data['supplierm_ids']:
                recordcount = recordcount + 1
                if lines[2]['default_key'] == True:
                    default_k = default_k + 1
                if 'supplierprice_ids' in lines[2]:
                    recordcount2 = 0
                    for lines2 in lines[2]['supplierprice_ids']:
                        if lines2[0] == 0:
                            recordcount2 = recordcount2 + 1
                    if recordcount2 < 1:
                        branchname.append(str(res_partner_child_obj.browse(cr, uid, lines[2]['partner_child_id'], context=context).name))
            if branchname:
                raise osv.except_osv(_('No Supplier Price detail Added'), _("the following is the supplier price which don't have the Supplier Price Detail : \n" + str(branchname)))
#            if recordcount < 1:
#                raise osv.except_osv(_('No Supplier Price Added!'), _('You have to input at least one Supplier Price at product !'))
            if recordcount > 0:
                if default_k < 1:
                    raise osv.except_osv(_('No Default Supplier Key Found!'), _('You have to select one Default Supplier Key at product !'))
                else:
                    if default_k > 1:
                        raise osv.except_osv(_('Multiple Default Supplier Key Found!'), _('You have select more than one Default Supplier Key at product, please just select one Default Supplier Key!'))
        if 'customerm_ids' in data:
            recordcount = 0
            for lines in data['customerm_ids']:
                recordcount = recordcount + 1
                if 'customerprice_ids' in lines[2]:
                    recordcount2 = 0
                    for lines2 in lines[2]['customerprice_ids']:
                        if lines2[0] == 0:
                            recordcount2 = recordcount2 + 1
                    if recordcount2 < 1:
                        branchname.append(str(lines[2]['name']))
                if 'supplier_key_id' in lines[2]:
                    lines[2].update({'supplier_key_id': []})
            if branchname:
                raise osv.except_osv(_('No Supplier Customer detail Added'), _("the following is the Customer Part No which don't have the Customer Price Detail : \n" + str(branchname)))
#            if recordcount < 1:
#                raise osv.except_osv(_('No Customer Part No Added!'), _('You have to input at least one Customer Part No at product !'))

        return super(product_product, self).create(cr, uid, data, context)

    def unlink(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order.line')
        purchase_obj = self.pool.get('purchase.order.line')
        inventory_obj = self.pool.get('stock.inventory.line')
        move_obj = self.pool.get('stock.move')
        invoice_obj = self.pool.get('account.invoice.line')
        product_ids = self.search(cr, uid, [('id', 'in', ids)])

        if sale_obj.search(cr, uid, [('product_id', 'in', product_ids)]):
            raise osv.except_osv(_('Error !'), _('You can not remove an product containing sales line items.'))

        if purchase_obj.search(cr, uid, [('product_id', 'in', product_ids)]):
            raise osv.except_osv(_('Error !'), _('You can not remove an product containing product lines items.'))

        if inventory_obj.search(cr, uid, [('product_id', 'in', product_ids)]):
            raise osv.except_osv(_('Error !'), _('You can not remove an product containing stock inventory lines items.'))

        if move_obj.search(cr, uid, [('product_id', 'in', product_ids)]):
            raise osv.except_osv(_('Error !'), _('You can not remove an product containing stock moves items.'))

        if invoice_obj.search(cr, uid, [('product_id', 'in', product_ids)]):
            raise osv.except_osv(_('Error !'), _('You can not remove an product containing invoices lines items.'))
        return super(product_product, self).unlink(cr, uid, ids, context=context)


    def write(self, cr, uid, ids, vals, context=None):

        #Load the required Object
        product_product_obj = self.pool.get('product.product')
        product_supplier_obj = self.pool.get('product.supplier')
        product_customer_obj = self.pool.get('product.customer')
        res_partner_child_obj = self.pool.get('res.partner.child')

#2 = Delete
#4 = no change
#0 = add
#1 = edit
        if 'supplierm_ids' in vals:
#            raise osv.except_osv(_('No Customer Part No Added!'), _(str(vals['supplierm_ids'])))
#             print vals['supplierm_ids']
#            vehicle_ids = []
#            vehicle_time = {}
#            so_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
#            rental = self.pool.get('rental.order').browse(cr, uid, so_id, context=None)
#            date_order = ('date_order_dummy' in vals and vals['date_order_dummy']) or rental.date_order_dummy
            branchname = []
            supplier_key = 0
            for lines in vals['supplierm_ids']:
                if lines[0] == 2:
                    continue
                if lines[0] == 4:
                    prod_supp = self.pool.get('product.supplier').browse(cr, uid, lines[1], context=None)
                    val_supplierprice_ids = prod_supp.supplierprice_ids
                    val_supplier_key = prod_supp.default_key
                    val_branch_name = prod_supp.partner_child_id.name
#                    raise osv.except_osv(_('No Customer Part No Added!'), _(str(val_supplierprice_ids)))
                if lines[0] == 1:
                    prod_supp = self.pool.get('product.supplier').browse(cr, uid, lines[1], context=None)
                    if 'supplierprice_ids' in lines[2]:
                        val_supplierprice_ids = []
                        for supp_price_ids in lines[2]['supplierprice_ids']:
                            if supp_price_ids[0] == 2:
                                continue
                            if supp_price_ids[0] == 4:
                                val_supplierprice_ids.append("got")
                            if supp_price_ids[0] == 1:
                                val_supplierprice_ids.append("got")
                            if lines[0] == 0:
                                val_supplierprice_ids.append("got")
                    else:
                        val_supplierprice_ids = prod_supp.supplierprice_ids
                    if 'default_key' in lines[2]:
                        val_supplier_key = lines[2]['default_key']
                    else:
                        val_supplier_key = prod_supp.default_key
                    val_branch_name = ('partner_child_id' in lines[2] and self.pool.get('res.partner.child').browse(cr, uid, lines[2]['partner_child_id'], context=None).name) or prod_supp.partner_child_id.name
                if lines[0] == 0:
                    if 'supplierprice_ids' in lines[2]:
                        val_supplierprice_ids = []
                        for supp_price_ids in lines[2]['supplierprice_ids']:
                            if supp_price_ids[0] == 2:
                                continue
                            if supp_price_ids[0] == 4:
                                val_supplierprice_ids.append("got")
                            if supp_price_ids[0] == 1:
                                val_supplierprice_ids.append("got")
                            if lines[0] == 0:
                                val_supplierprice_ids.append("got")
                    else:
                        val_supplierprice_ids = []
                    val_supplier_key = ('default_key' in lines[2] and lines[2]['default_key'])
                    val_branch_name = ('partner_child_id' in lines[2] and self.pool.get('res.partner.child').browse(cr, uid, lines[2]['partner_child_id'], context=None).name)
                if not val_supplierprice_ids:
                    branchname.append(val_branch_name)
#                 print val_supplier_key
                if val_supplier_key == True:
                    supplier_key += 1
            if supplier_key == 0:
                raise osv.except_osv(_('No Default Supplier Key Found!'), _('You have to select one Default Supplier Key at product !'))
            if supplier_key > 1:
                raise osv.except_osv(_('Multiple Default Supplier Key Found!'), _('You have select more than one Default Supplier Key at product, please just select one Default Supplier Key!'))
            if branchname:
                raise osv.except_osv(_('No Supplier Price detail Added'), _("the following is the supplier price which don't have the Supplier Price Detail : \n" + str(branchname)))

        if 'customerm_ids' in vals:
            customerm_ids2 = []
            record_delete = []
            recordcount = 0
            branchname = []
            branchname2 = []
            for lines in vals['customerm_ids']:
                if lines[0] == 0:
                    recordcount = recordcount + 1

                    if 'customerprice_ids' in lines[2]:
                        recordcount2 = 0
                        for lines2 in lines[2]['customerprice_ids']:
                            if lines2[0] == 0:
                                recordcount2 = recordcount2 + 1
                        if recordcount2 < 1:
                            branchname.append(str(lines[2]['name']))

                    if 'supplier_key_id' in lines[2]:
                        if lines[2]['supplier_key_id'] != False:
                            product_id = product_supplier_obj.browse(cr, uid, lines[2]['supplier_key_id'], context=context).product_id.id
                            if product_id != ids[0]:
                                branchname2.append(str(lines[2]['name']))
                if lines[0] == 1:
                    recordcount2 = 0
                    if 'customerprice_ids' in lines[2]:
                        for lines2 in lines[2]['customerprice_ids']:
                            if lines2[0] == 0:
                                recordcount2 = recordcount2 + 1
                            if lines2[0] == 2:
                                recordcount2 = recordcount2 - 1

                    product_customer = product_customer_obj.browse(cr, uid, lines[1], context=context)
                    for lines3 in product_customer.customerprice_ids:
                        recordcount2 = recordcount2 + 1

                    if recordcount2 < 1:
                        if 'name' in lines[2]:
                            branchname.append(str(lines[2]['name']))
                        else:
                            branchname.append(str(product_customer.name))

                    if 'supplier_key_id' in lines[2]:
                        if lines[2]['supplier_key_id'] != False:
                            product_id = product_supplier_obj.browse(cr, uid, lines[2]['supplier_key_id'], context=context).product_id.id
                            if product_id != ids[0]:
                                if 'name' in lines[2]:
                                    branchname2.append(str(lines[2]['name']))
                                else:
                                    branchname2.append(str(product_customer.name))

                if lines[0] == 2:
                    record_delete.append(lines[1])

            if branchname:
                raise osv.except_osv(_('No Supplier Customer detail Added'), _("the following is the customer Part No which don't have the Customer Price Detail : \n" + str(branchname)))

            if branchname2:
                raise osv.except_osv(_('Wrong Supplier Key Added'), _("the following is the customer Part No which input the wrong Supplier Key : \n" + str(branchname2)))

            customerm_ids = product_product_obj.browse(cr, uid, ids[0], context=context).customerm_ids

            for item in customerm_ids:
                if item.id not in record_delete:
                    customerm_ids2.append(item.id)

            for m in customerm_ids2:
                recordcount = recordcount + 1

#            if recordcount < 1:
#                raise osv.except_osv(_('No Customer Part No Added!'), _('You have to input at least one Customer Part No at product !'))

        return super(product_product, self).write(cr, uid, ids, vals, context=context)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', 'Internal Part No must be unique per Product!'),
    ]

product_product()

class product_customer(osv.osv):
    _name = "product.customer"
    _description = "Customer Price Methodology"

    def onchange_name(self, cr, uid, ids, product_name, supplier_key_id, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        product_product_obj = self.pool.get('product.product')
        product_ids = product_product_obj.search(cr, uid, [('name','=',product_name)])
        rate_id = False
        product_id = False
        if product_ids:
            product_id = product_ids[0]
        res = {'domain': {'supplier_key_id': [('product_id','=',product_id)]}}
        if not product_id:
            return res

        return res

    def onchange_product_id(self, cr, uid, ids, product_id, supplier_key_id, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        
        res = {'value': {'supplier_key_id': False}}
        res['domain'] = {'supplier_key_id': [('product_id','=',product_id)]}
        if not product_id:
            return res

        product_supplier_obj = self.pool.get('product.supplier')

        product_supplier_key_ids = product_supplier_obj.search(cr, uid, [('product_id','=',product_id)], order='name ASC')
        if product_supplier_key_ids:
            product_supplier_key_id = product_supplier_key_ids[0]
        else:
            res['warning'] = {'title': _('Warning'), 'message': _('cannot find the supplier key in the selected product')}
            return res

        if not supplier_key_id:
            supplier_key_id = product_supplier_key_id

        if product_id != product_supplier_obj.browse(cr, uid, supplier_key_id, context=context).product_id.id:
            res['warning'] = {'title': _('Warning'), 'message': _('Selected Supplier Key does not belong to the selected product')}
            res['value'].update({'supplier_key_id': product_supplier_key_id})
            return res

        res['value'].update({'supplier_key_id': supplier_key_id})
        return res

    def _get_supplier_key(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a voucher line. It's either the currency of the 
        associated move line (if any) or the currency of the voucher or the company currency.
        '''
        res = {}
        prod_supp_obj = self.pool.get('product.supplier')
        for prod_cust in self.browse(cr, uid, ids, context=context):
            if prod_cust.supplier_key_id:
                res[prod_cust.id] = prod_cust.supplier_key_id.id
            else:
                prod_supp_ids = False
                if prod_cust.product_id:
                    prod_supp_ids = prod_supp_obj.search(cr, uid, [('product_id','=',prod_cust.product_id.id),('default_key','=',True)])
                res[prod_cust.id] = prod_supp_ids and prod_supp_ids[0] or None
        return res

    _columns = {
        'moq': fields.float('Minimum Order Qty',required=True),
        'pricelist_id' : fields.related('partner_id', 'property_product_pricelist', type='many2one', relation="product.pricelist",
                                        string="Pricelist",
                                        store=False, readonly=True, invisible=True),
        'currency_id' : fields.related('pricelist_id', 'currency_id', type='many2one', relation="res.currency",
                                        string="Currency",
                                        store=False, readonly=True),
        'name': fields.char('Customer Part No.', size=64),
        'product_id' : fields.many2one('product.product', 'Product', select=1, ondelete='cascade'),
        'partner_id':fields.many2one('res.partner', 'Customer', required=True),
        'supplier_key_id':fields.many2one('product.supplier', 'Supplier Key'),
        'customerprice_ids' : fields.one2many('product.customer.price', 'product_customer_id', 'Customer Price'),
        'sale_ok': fields.related('product_id', 'sale_ok', type='boolean', relation='product.template', readonly=True),
        'supplier_key_funct': fields.function(_get_supplier_key, string='Supplier Key', type='many2one', relation='product.supplier', readonly=True),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(name, product_id, partner_id)', 'Customer Part No must be unique per Product!'),
    ]

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_customer = self.read(cr, uid, ids, ['name'], context=context)
        unlink_ids = []
        sale_order_line_obj = self.pool.get('sale.order.line')
        for t in product_customer:
            product_customer_id = t['id']
            sale_order_line_ids = sale_order_line_obj.search(cr, uid, [('product_customer_id','=',product_customer_id)])
            if sale_order_line_ids:
                raise osv.except_osv(_('Invalid action in Customer Price Methodology!'), _('You can not delete an customer Part No : ' + str(t['name']) + ',\n which has transaction in sale order'))
            else:
                unlink_ids.append(t['id'])
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True

product_customer()

class product_customer_price(osv.osv):
    _name = "product.customer.price"
    _description = "Product Customer Price"

    _columns = {
        'header_name': fields.related('product_customer_id', 'name', type='char', relation='product.customer', readonly=True, string="Customer Part No.",),
        'partner_id' : fields.related('product_customer_id', 'partner_id', type='many2one', relation="res.partner",
                                        string="Customer",
                                        store=False, readonly=True),
        'supplier_key_id' : fields.related('product_customer_id', 'supplier_key_id', type='many2one', relation="product.supplier",
                                        string="Supplier Key",store=False, readonly=True),
        'currency_id' : fields.related('product_customer_id', 'currency_id', type='many2one', relation="res.currency",
                                        string="Currency",
                                        store=False, readonly=True),
        'name': fields.char('Remark', size=64),
        'product_customer_id' : fields.many2one('product.customer', 'Product Customer Id', select=1, required=True, ondelete='cascade'),
        'effective_date': fields.date('Effective Date', help="Date of Effective", select=True),
        'unit_cost': fields.float('Unit Price', digits_compute=dp.get_precision('Purchase Price')),
        'upper_limit_ids' : fields.one2many('product.customer.upper.limit', 'product_customer_price_id', 'Customer Price Upper Limit'),
    }

    _defaults = {
        'effective_date': fields.date.context_today,
    }

product_customer_price()

class product_customer_upper_limit(osv.osv):
    _name = "product.customer.upper.limit"
    _description = "Product Customer Upper Limit"

    _columns = {
        'product_customer_price_id' : fields.many2one('product.customer.price', 'Product Customer Price Id', required=True, ondelete='cascade'),
        'qty': fields.float('Qty Limit'),
        'unit_cost': fields.float('Unit Cost', digits_compute=dp.get_precision('Purchase Price')),
    }
    _defaults = {
        'qty': 2.00,
    }
    def onchange_qty(self, cr, uid, ids, qty, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        
        res = {}
        if qty < 2:
            qty = 2
        res['value'] = {'qty': qty}
        return res

product_customer_upper_limit()

class product_supplier(osv.osv):
    _name = "product.supplier"
    _description = "Supplier Price Methodology"
    _rec_name = 'partner_child_name'

    def onchange_partner_id(self, cr, uid, ids ,partner_id2, partner_child_id):
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        if not partner_id2:
            return res
        partner_child_ids = []
        partner = res_partner_obj.browse(cr, uid, partner_id2, context=None)
        partner_child = partner.pchild_ids

        for pc in partner_child:
            partner_child_ids.append(pc.id)

        res['domain'] = {'partner_child_id': [('id','in',partner_child_ids)]}

        if partner_child_id:
            if partner_child_id not in partner_child_ids:
                res['value'] = {'partner_child_id': False}
                res['warning'] = {'title': _('Warning'), 'message': _('The selected Supplier Branch is not belong to Supplier ' + str(partner.name) + ' !')}
                return res

        return res

    _columns = {
        'moq': fields.float('Minimum Order Qty', required=True),
        'partner_id' : fields.related('partner_child_id', 'partner_id', type='many2one', relation="res.partner",
                                        string="Partner",
                                        store=False,invisible=True),
        'pricelist_id' : fields.related('partner_id', 'property_product_pricelist_purchase', type='many2one', relation="product.pricelist",
                                        string="Pricelist",
                                        store=False, readonly=True, invisible=True),
        'currency_id' : fields.related('pricelist_id', 'currency_id', type='many2one', relation="res.currency",
                                        string="Currency",
                                        store=False, readonly=True),
        'partner_id2' : fields.many2one('res.partner', 'Supplier', select=1, required=True),
        'partner_child_id' : fields.many2one('res.partner.child', 'Supplier Branch', select=1, required=True),
        'partner_child_name': fields.related('partner_child_id', 'name', type='char', relation='res.partner.child', readonly=True),
        'product_id' : fields.many2one('product.product', 'Product', select=1, ondelete='cascade', required=True),
        'product_name': fields.related('product_id', 'name', type='char', relation='product.product', readonly=True),
        'supplierprice_ids' : fields.one2many('product.supplier.price', 'product_supplier_id', 'Supplier Price'),
        'purchase_ok': fields.related('product_id', 'purchase_ok', type='boolean', relation='product.template', readonly=True),
        'default_key' : fields.boolean('Default Supplier Key'),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(partner_child_id, product_id)', 'Supplier Branch must be unique per Product!'),
    ]

product_supplier()

class product_supplier_price(osv.osv):
    _name = "product.supplier.price"
    _description = "Product Supplier Price"

    _columns = {
        'partner_child_id' : fields.related('product_supplier_id', 'partner_child_id', type='many2one', relation="res.partner.child",
                                        string="Supplier Branch",
                                        store=False, readonly=True),
        'default_key': fields.related('product_supplier_id', 'default_key', type='boolean', relation='product.supplier', readonly=True, string="Default Supplier Key"),
        'currency_id' : fields.related('product_supplier_id', 'currency_id', type='many2one', relation="res.currency",
                                        string="Currency",
                                        store=False, readonly=True),
        'name': fields.char('Remark', size=64),
        'product_supplier_id' : fields.many2one('product.supplier', 'Product Supplier Id', select=1, required=True, ondelete='cascade'),
        'effective_date': fields.date('Effective Date', help="Date of Effective", select=True),
        'unit_cost': fields.float('Unit Cost', digits_compute=dp.get_precision('Purchase Price')),
        'upper_limit_ids' : fields.one2many('product.supplier.upper.limit', 'product_supplier_price_id', 'Supplier Price Upper Limit'),
    }

    _defaults = {
        'effective_date': fields.date.context_today,
    }

product_supplier_price()

class product_supplier_upper_limit(osv.osv):
    _name = "product.supplier.upper.limit"
    _description = "Product Supplier Upper Limit"

    _columns = {
        'product_supplier_price_id' : fields.many2one('product.supplier.price', 'Product Supplier Price Id', required=True, ondelete='cascade'),
        'qty': fields.float('Qty Limit'),
        'unit_cost': fields.float('Unit Cost', digits_compute=dp.get_precision('Purchase Price')),
    }

    _defaults = {
        'qty': 2.00,
    }

    def onchange_qty(self, cr, uid, ids, qty, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        
        res = {}
        if qty < 2:
            qty = 2
        res['value'] = {'qty': qty}
        return res

product_supplier_upper_limit()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
