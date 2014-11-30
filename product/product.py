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
import time
from osv import fields,osv
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
import decimal_precision as dp
import netsvc
import re

class product_category(osv.osv):
    _inherit = "product.category"
    _description = "Product Category"

    _columns = {
        'property_stock_opening_balance_categ': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Opening Balance Account', view_load=True,
            help="When doing Opening Balance inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
        'property_stock_physical_inventory_in_categ': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Physical Inventory Input Account', view_load=True,
            help="When doing Physical inventory IN valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
        'property_stock_physical_inventory_out_categ': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Physical Inventory Output Account', view_load=True,
            help="When doing Physical inventory Out valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
        'property_stock_physical_inventory_write_off_categ': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Physical Inventory Write Off Account', view_load=True,
            help="When doing Physical inventory Write Off valuation, counterpart journal items for all write off stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
    }

product_category()


class product_product(osv.osv):
    _inherit = "product.product"
    _description = "Product"
    _order = 'brand_id,name_template'

#RT
    def create(self, cr, user, vals, context=None):
        #RT
        name = ('name' in vals and vals['name']) or False
        default_code = ('default_code' in vals and vals['default_code']) or False
        spq = ('spq' in vals and vals['spq']) or False
        
        if ' ' in name:
            raise osv.except_osv(_('Error!'), _("No Space Allowed at Supplier Part No!"))
        if ' ' in default_code:
            raise osv.except_osv(_('Error!'), _("No Space Allowed at Internal Part No!"))
        
        last_char_name = name[-1]
        last_char_code = default_code[-1]
        if not last_char_name.isalnum():
            raise osv.except_osv(_('Error!'), _("You Can't Input Special Character at Last Character of Supplier Part No!"))
        if not last_char_code.isalnum():
            raise osv.except_osv(_('Error!'), _("You Can't Input Special Character at Last Character of Internal Part No!"))

        vals.update({'name':name.upper()})
        vals.update({'default_code':default_code.upper()})

#         if ' ' in spq:
#             raise osv.except_osv(_('Error!'), _("Standard Packaging Qty Can't Empty!"))
        if spq < 1:
            raise osv.except_osv(_('Error!'), _("Standard Packaging Qty Must More Than Zero!"))
        return super(product_product, self).create(cr, user, vals, context=context)
#END RT

    def write(self, cr, uid, ids, vals, context=None):
        product_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        name = ('name' in vals and vals['name']) or False
        default_code = ('default_code' in vals and vals['default_code']) or False
        spq = ('spq' in vals and vals['spq']) or False
        if not 'name' in vals:
            name = (self.pool.get('product.product').browse(cr, uid, product_id, context=None).name)
        if not 'default_code' in vals:
            default_code = (self.pool.get('product.product').browse(cr, uid, product_id, context=None).default_code)
        #RT
        if ' ' in name:
            raise osv.except_osv(_('Error!'), _("No Space Allowed at Supplier Part No!"))
        if ' ' in default_code:
            raise osv.except_osv(_('Error!'), _("No Space Allowed at Internal Part No!"))
        
        last_char_name = name[-1]
        last_char_code = default_code[-1]
        if not last_char_name.isalnum():
            raise osv.except_osv(_('Error!'), _("You Can't Input Special Character at Last Character of Supplier Part No!"))
        if not last_char_code.isalnum():
            raise osv.except_osv(_('Error!'), _("You Can't Input Special Character at Last Character of Internal Part No!"))
        vals.update({'name':name.upper()})
        vals.update({'default_code':default_code.upper()})

        if spq < 1:
            raise osv.except_osv(_('Error!'), _("Standard Packaging Qty Must More Than Zero!"))
        #end RT

        return super(product_product, self).write(cr, uid, ids, vals, context=context)


    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('brand_name',False)
            if code:
                name = '[%s] %s' % (code,name)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'brand_name': s.brand_name or product.brand_name,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'brand_name': product.brand_name,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('brand_name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('brand_name',operator,name)], limit=limit, context=context))
                if len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit-len(ids)), context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('brand_name','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result



#    def _qty_booked(self, cr, uid, ids, name, arg, context=None):
#
#        if not ids: return {}
#        res = {}
#        sale_order_line_obj = self.pool.get("sale.order.line")
#        stock_move_obj = self.pool.get("stock.move")
#        uom_obj = self.pool.get("product.uom")
#        for obj in self.browse(cr, uid, ids, context=context):
#            sale_qty = 0.00
#            do_qty = 0.00
#            product_id = obj.id
#            sale_order_line_ids = sale_order_line_obj.search(cr, uid, [('product_id','=',product_id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')])
#            if sale_order_line_ids:
#                for val in sale_order_line_ids:
#                    sol = sale_order_line_obj.browse(cr, uid, val, context=context)
#                    sale_qty = sale_qty + uom_obj._compute_qty(cr, uid, sol.product_uom.id, sol.product_uom_qty, obj.uom_id.id)
#                    stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',val),('state','=','done')])
#                    if stock_move_ids:
#                        for stock_move_id in stock_move_ids:
#                            stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
#                            do_qty = do_qty + uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, obj.uom_id.id)
#            res[obj.id] = sale_qty - do_qty
#        return res

#    def _qty_free(self, cr, uid, ids, name, arg, context=None):
#
#        if not ids: return {}
#        res = {}
#        sale_order_line_obj = self.pool.get("sale.order.line")
#        stock_move_obj = self.pool.get("stock.move")
#        uom_obj = self.pool.get("product.uom")
#        for obj in self.browse(cr, uid, ids, context=context):
#            product_id = obj.id
#            sale_order_line_ids = sale_order_line_obj.browse(cr, uid, sale_order_line_obj.search(cr, uid, [('product_id','=',product_id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')]), context=context)
#            allocated_onhand = 0.00
#            do_qty = 0.00
#            if sale_order_line_ids:
#                for val in sale_order_line_ids:
#                    allocated_onhand = allocated_onhand + val.qty_onhand_count
#                    stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',val.id),('state','=','done')])
#                    if stock_move_ids:
#                        for stock_move_id in stock_move_ids:
#                            stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
#                            do_qty = do_qty + uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, obj.uom_id.id)
#
#            res[obj.id] = obj.qty_available - (allocated_onhand - do_qty)
#        return res

#    def count_non_booked(self, cr, uid, pol, context=None):
##        product_uom_obj = self.pool.get("product.uom")
##        stock_move_obj = self.pool.get("stock.move")
##        sale_allocated_obj = self.pool.get("sale.allocated")
##        qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, obj.uom_id.id)
##        sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
##        qty_allocated = 0.00
##        qty_received = 0.00
##        incoming_qty = 0.00
##        if sale_allocated_ids:
##            for val in sale_allocated_ids:
##                qty_allocated = qty_allocated + val.quantity
##                qty_received = qty_received + val.received_qty
###        if pol.id == 46:
###            raise osv.except_osv(_('Debug !'), _(str(qty_allocated) + '----' + '' + '----' + ''))
##
##        if qtyp > 0:
##            stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
##            if stock_move_ids:
##                for stock_move_id in stock_move_ids:
##                    stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
##                    incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, obj.uom_id.id)
###        if pol.id == 46:
###            raise osv.except_osv(_('Debug !'), _(str(qtyp) + '----' + str(qty_allocated) + '----' + str(incoming_qty)))
##
##        qtyp = qtyp - (incoming_qty - qty_received) - qty_allocated
#
#        qtyp = 0.00
#        sale_allocated_obj = self.pool.get("sale.allocated")
#        sale_allocated_ids = sale_allocated_obj.search(cr, uid, [('receive','=',False)])
#        val_sale_allocated = ''
#        if sale_allocated_ids:
#            val_sale_allocated = ','.join(map(str, sale_allocated_ids))
#        cr.execute("select (pol.product_qty / " \
#                   "(CASE WHEN pu_po.uom_type = 'reference' THEN pu_po.factor " \
#                   "WHEN pu_po.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) / pu_po.factor) " \
#                   "ELSE ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) * pu_po.factor) END) * " \
#                   "(CASE WHEN pu_pt.uom_type = 'reference' THEN pu_pt.factor " \
#                   "WHEN pu_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) / pu_pt.factor) " \
#                   "ELSE ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) * pu_pt.factor) END)" \
#                   ") - (" \
#                   "(COALESCE(" \
#                   "(select sum((sm.product_qty / " \
#                   "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
#                   "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
#                   "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
#                   "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
#                   "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
#                   "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
#                   "from stock_move sm " \
#                   "left join product_template pt_sm on sm.product_id = pt_sm.id " \
#                   "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
#                   "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
#                   "where sm.purchase_line_id = pol.id and sm.state = 'done' " \
#                   ") " \
#                   ", 0)) - " \
#                   "COALESCE((select sum(COALESCE( received_qty, 0)) as qty_received from sale_allocated where sale_allocated.purchase_line_id = pol.id and id in (" + val_sale_allocated + ")), 0)" \
#                   ") - COALESCE((select sum(COALESCE( received_qty, 0)) as qty_received from sale_allocated where sale_allocated.purchase_line_id = pol.id and id in (" + val_sale_allocated + ")), 0) as qtyp " \
#                   "from purchase_order_line pol " \
#                   "left join product_template pt on pol.product_id = pt.id " \
#                   "left join product_uom pu_po on pol.product_uom = pu_po.id " \
#                   "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
#                   "where pol.id = " + str(pol.id) + " ")
#        res_general = cr.dictfetchall()
#        for val in res_general:
#            qtyp = val['qtyp']
#        return qtyp

    def button1(self, cr, uid, ids, context=None):
        
        product_ids = self.browse(cr, uid, self.search(cr, uid, []), context=context)
        if product_ids:
            num = 0
            for pp in product_ids:
                num = num + 1
                self.write(cr, uid, pp.id, {'product_temp1': pp.name,
                                            'product_temp2': pp.default_code,
                                            'name': str(num) + "yy1",
                                            'default_code': str(num) + "zz1",
                                            })
#                raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(pp.name, pp.default_code))
        return True

    def button2(self, cr, uid, ids, context=None):
        
        product_ids = self.browse(cr, uid, self.search(cr, uid, []), context=context)
        if product_ids:
            num = 0
            for pp in product_ids:
                num = num + 1
                self.write(cr, uid, pp.id, {'name': pp.product_temp2,
                                            'default_code': pp.product_temp1,
                                            'product_temp1': '',
                                            'product_temp2': '',
                                            })
#                raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(pp.name, pp.default_code))
        return True

    def _get_default_taxes_id(self, cr, uid, context):
        res_user_obj = self.pool.get("res.users")
        res_user = res_user_obj.browse(cr, uid, uid, context=context)
        tax_id = res_user and res_user.company_id and res_user.company_id.tax_id and res_user.company_id.tax_id.id or False
        ids = tax_id and self.pool.get('account.tax').search(cr, uid, [('id','=',tax_id)], context=context) or []
        return ids


    def _get_default_supplier_taxes_id(self, cr, uid, context):
        res_user_obj = self.pool.get("res.users")
        res_user = res_user_obj.browse(cr, uid, uid, context=context)
        tax_id = res_user and res_user.company_id and res_user.company_id.supplier_tax_id and res_user.company_id.supplier_tax_id.id or False
        ids = tax_id and self.pool.get('account.tax').search(cr, uid, [('id','=',tax_id)], context=context) or []
        return ids

    def _get_default_location(self, cr, uid, context=None):
        res = []
        res_user_obj = self.pool.get("res.users")
        res_user = res_user_obj.browse(cr, uid, uid, context=context)
        location_id = res_user and res_user.company_id and res_user.company_id.location_id and res_user.company_id.location_id.id or False
        if location_id:
            dct = {
                'stock_location_id': location_id,
                'default_key': True
            }
            res.append(dct)
        return res
#    c.update({ 'states': ('done',), 'what': ('in', 'out') })
    def get_product_available(self, cr, uid, ids, context=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')
        
        states = context.get('states',[])
        what = context.get('what',())
        if not ids:
            ids = self.search(cr, uid, [])
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res

        if context.get('shop', False):
            warehouse_id = shop_obj.read(cr, uid, int(context['shop']), ['warehouse_id'])['warehouse_id'][0]
            if warehouse_id:
                context['warehouse'] = warehouse_id

        if context.get('warehouse', False):
            lot_id = warehouse_obj.read(cr, uid, int(context['warehouse']), ['lot_stock_id'])['lot_stock_id'][0]
            if lot_id:
                context['location'] = lot_id

        if context.get('location', False):
            if type(context['location']) == type(1):
                location_ids = [context['location']]
            elif type(context['location']) in (type(''), type(u'')):
                location_ids = location_obj.search(cr, uid, [('name','ilike',context['location'])], context=context)
            else:
                location_ids = context['location']
        else:
            location_ids = []
            wids = warehouse_obj.search(cr, uid, [], context=context)
            for w in warehouse_obj.browse(cr, uid, wids, context=context):
                location_ids.append(w.lot_stock_id.id)

        # build the list of ids of children of the location given by id
        if context.get('compute_child',True):
            child_location_ids = location_obj.search(cr, uid, [('location_id', 'child_of', location_ids)])
            location_ids = child_location_ids or location_ids
        
        # this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id
        uoms_o = {}
        # this will be a dictionary of the product UoM by product id
        product2uom = {}
        for product in self.browse(cr, uid, ids, context=context):
            product2uom[product.id] = product.uom_id.id
            uoms_o[product.uom_id.id] = product.uom_id

        results = []
        results2 = []

        from_date = context.get('from_date',False)
        to_date = context.get('to_date',False)
        date_str = False
        date_values = False
        where = [tuple(location_ids),tuple(location_ids),tuple(ids),tuple(states)]
        if from_date and to_date:
            date_str = "date>=%s and date<=%s"
            where.append(tuple([from_date]))
            where.append(tuple([to_date]))
        elif from_date:
            date_str = "date>=%s"
            date_values = [from_date]
        elif to_date:
            date_str = "date<=%s"
            date_values = [to_date]

        prodlot_id = context.get('prodlot_id', False)

    # TODO: perhaps merge in one query.
        if date_values:
            where.append(tuple(date_values))
        if 'in' in what:
            # all moves from a location out of the set to a location in the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id NOT IN %s '\
                'and location_dest_id IN %s '\
                'and product_id IN %s '\
                '' + (prodlot_id and ('and prodlot_id = ' + str(prodlot_id)) or '') + ' '\
                'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
                'group by product_id,product_uom',tuple(where))
            results = cr.fetchall()
        if 'out' in what:
            # all moves from a location in the set to a location out of the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id IN %s '\
                'and location_dest_id NOT IN %s '\
                'and product_id  IN %s '\
                '' + (prodlot_id and ('and prodlot_id = ' + str(prodlot_id)) or '') + ' '\
                'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
                'group by product_id,product_uom',tuple(where))
            results2 = cr.fetchall()
            
        # Get the missing UoM resources
        uom_obj = self.pool.get('product.uom')
        uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2)
        if context.get('uom', False):
            uoms += [context['uom']]
        uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
        if uoms:
            uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
            for o in uoms:
                uoms_o[o.id] = o
                
        #TOCHECK: before change uom of product, stock move line are in old uom.
        context.update({'raise-exception': False})
        # Count the incoming quantities
        for amount, prod_id, prod_uom in results:
            amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                     uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
            res[prod_id] += amount
        # Count the outgoing quantities
        for amount, prod_id, prod_uom in results2:
            amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                    uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
            res[prod_id] -= amount
        return res

    def get_product_available2(self, cr, uid, ids, context=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}

        if not ids:
            ids = self.search(cr, uid, [])
        what = context.get('what',())
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res


        pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "

        results = results2 = []
        if 'incoming_booked' in what:
            cr.execute("select coalesce( \
                (select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty \
                from sale_allocated sa \
                inner join purchase_order_line pol on sa.purchase_line_id = pol.id \
                where coalesce(sa.quantity,0) > coalesce(sa.received_qty,0) \
                and sa.product_id = pp_o.id) \
                ,0) as qty_incoming_booked, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()

        if 'incoming_non_booked' in what:
        
            cr.execute("select coalesce( \
                (select sum( \
                (pol.product_qty -  \
                coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id and sm.state = 'done'),0)) - \
                coalesce((select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                where sa.purchase_line_id = pol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)) \
                ,0)) \
                from purchase_order_line pol \
                where pol.product_id = pp_o.id and state not in ('draft', 'cancel')) \
                ,0) as qty_incoming_non_booked, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()
        if 'booked' in what:
            cr.execute("select coalesce(( \
               select sum( \
               (sol.product_uom_qty -  \
               coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0))) \
               from sale_order_line sol \
               where sol.product_id = pp_o.id and state not in ('draft', 'cancel') \
               ),0) as qty_booked, \
               pp_o.id as prod_id from product_product pp_o \
               inner join product_template pt_o on pp_o.id = pt_o.id where  \
               " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()
        if 'allocated' in what:
            cr.execute("select coalesce(( \
                select sum( \
                sol.qty_onhand_allocated +  \
                coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
                coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
                where sol.product_id = pp_o.id and state not in ('draft', 'cancel') \
                ),0) as qty_allocated, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()
        for amount, prod_id in results:
            res[prod_id] += amount

        return res

    def get_product_available3(self, cr, uid, ids, context=None, context2=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if context2 is None:
            context2 = {}
        if not ids:
            ids = self.search(cr, uid, [])
        what = context.get('what',())
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res


        pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "

        results = results2 = []
        if 'incoming_non_booked' in what:
            cr.execute("select coalesce( \
                (select sum( \
                (pol.product_qty -  \
                coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id and sm.state = 'done'),0)) - \
                coalesce((select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                where sa.purchase_line_id = pol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)) \
                ,0)) \
                from purchase_order_line pol \
                where pol.product_id = pp_o.id and state not in ('draft', 'cancel')) \
                ,0) as qty_incoming_non_booked, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()
        if 'allocated' in what:
            cr.execute("select coalesce(( \
                select sum( \
                sol.qty_onhand_allocated +  \
                coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
                coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
                where sol.product_id = pp_o.id and state not in ('draft', 'cancel') \
                ),0) as qty_allocated, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results2 = cr.fetchall()
        for amount, prod_id in results:
            qty_available = self.browse(cr, uid, prod_id, context=None).qty_available
            res[prod_id] += (qty_available + amount)
        for amount, prod_id in results2:
            res[prod_id] -= amount
        return res

    def get_product_available4(self, cr, uid, ids, context=None, context2=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if context2 is None:
            context2 = {}
        if not ids:
            ids = self.search(cr, uid, [])
        what = context.get('what',())
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res


        pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "

        results = []
#         if 'booked' in what:
#             cr.execute("select coalesce(( \
#                select sum( \
#                (sol.product_uom_qty -  \
#                coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0))) \
#                from sale_order_line sol \
#                where sol.product_id = pp_o.id and state not in ('draft', 'cancel') \
#                ),0) as qty_booked, \
#                pp_o.id as prod_id from product_product pp_o \
#                inner join product_template pt_o on pp_o.id = pt_o.id where  \
#                " + pp_qry + "order by pt_o.name")
        if 'allocated' in what:
            cr.execute("select coalesce(( \
                select sum( \
                sol.qty_onhand_allocated +  \
                coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
                coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
                where sol.product_id = pp_o.id and state not in ('draft', 'cancel') \
                ),0) as qty_allocated, \
                pp_o.id as prod_id from product_product pp_o \
                inner join product_template pt_o on pp_o.id = pt_o.id where  \
                " + pp_qry + "order by pt_o.name")
            results = cr.fetchall()

        for amount, prod_id in results:
            qty_available = self.browse(cr, uid, prod_id, context=None).qty_available
            res[prod_id] += (qty_available - amount)
        return res

    def get_product_available5(self, cr, uid, ids, context=None, context2=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if context2 is None:
            context2 = {}
        if not ids:
            ids = self.search(cr, uid, [])
        
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res


        pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "

        results = []
        cr.execute("select coalesce((select sum(sm.product_qty) from stock_move sm inner join " \
            "stock_picking sp on sp.id = sm.picking_id where sm.picking_id is not null and sp.type='out' and sp.state <> 'done' " \
            "),0) as qty_do, " \
            "pp_o.id as prod_id from product_product pp_o " \
            "inner join product_template pt_o on pp_o.id = pt_o.id where " \
            + pp_qry + "order by pt_o.name")

        results = cr.fetchall()

        for amount, prod_id in results:
             res[prod_id] += amount
        return res

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
        for f in field_names:
            c = context.copy()
            d = context.copy()
            if f == 'qty_available':
                c.update({ 'states': ('done',), 'what': ('in', 'out') })
                stock = self.get_product_available(cr, uid, ids, context=c)
            if f == 'virtual_available':
                c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
                stock = self.get_product_available(cr, uid, ids, context=c)
            if f == 'incoming_qty':
                c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
                stock = self.get_product_available(cr, uid, ids, context=c)
            if f == 'outgoing_qty':
                c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
                stock = self.get_product_available(cr, uid, ids, context=c)
            if f == 'qty_incoming_booked':
                d.update({'what': ('incoming_booked',) })
                stock = self.get_product_available2(cr, uid, ids, context=d)
            if f == 'qty_incoming_non_booked':
                d.update({'what': ('incoming_non_booked',) })
                stock = self.get_product_available2(cr, uid, ids, context=d)
            if f == 'qty_booked':
                d.update({'what': ('booked',) })
                stock = self.get_product_available2(cr, uid, ids, context=d)
            if f == 'qty_free':
                d.update({'what': ('allocated',) })
                stock = self.get_product_available4(cr, uid, ids, context=d)
            if f == 'qty_allocated':
                d.update({'what': ('allocated',) })
                stock = self.get_product_available2(cr, uid, ids, context=d)
            if f == 'qty_free_balance':
                d.update({'what': ('incoming_non_booked','allocated',) })
                c.update({ 'states': ('done',), 'what': ('in', 'out') })
                stock =  self.get_product_available3(cr, uid, ids, context=d, context2=c)
            if f == 'qty_do':
                stock = self.get_product_available5(cr, uid, ids, context=None)
            for id in ids:
                res[id][f] = stock.get(id, 0.0)
            
        return res

#     def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
#         """ Finds the incoming and outgoing quantity of product.
#         @return: Dictionary of values
#         """
#         if not field_names:
#             field_names = []
#         if context is None:
#             context = {}
#         res = {}
#         for id in ids:
#             res[id] = {}.fromkeys(field_names, 0.0)
# 
# 
#         for f in field_names:
#             c = context.copy()
#             if f == 'qty_available':
#                 c.update({ 'states': ('done',), 'what': ('in', 'out') })
#                 stock = self.get_product_available(cr, uid, ids, context=c)
#             if f == 'virtual_available':
#                 c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
#                 stock = self.get_product_available(cr, uid, ids, context=c)
#             if f == 'incoming_qty':
#                 c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
#                 stock = self.get_product_available(cr, uid, ids, context=c)
#             if f == 'outgoing_qty':
#                 c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
#                 stock = self.get_product_available(cr, uid, ids, context=c)
#             if f == 'qty_incoming_booked':
#                 stock = self.get_incoming_booked(cr, uid, ids, context=None)
#             if f == 'qty_incoming_non_booked':
#                 stock = self.get_incoming_non_booked(cr, uid, ids, context=None)
#             if f == 'qty_booked':
#                 stock = self._qty_booked(cr, uid, ids, context=None)
#             if f == 'qty_free':
#                 stock = self._qty_free(cr, uid, ids, context=None)
#             if f == 'qty_allocated':
#                 stock = self._qty_allocated(cr, uid, ids, context=None)
#             if f == 'qty_free_balance':
#                 stock = self._qty_free_balance(cr, uid, ids, context=None)
#             for id in ids:
#                 res[id][f] = stock.get(id, 0.0)
#         return res

#     def get_incoming_booked(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
# 
#         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
# 
#         cr.execute("CREATE OR REPLACE FUNCTION qty_incoming_booked_p(integer) RETURNS numeric AS $$ \
#             select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty \
#             from sale_allocated sa \
#             inner join purchase_order_line pol on sa.purchase_line_id = pol.id \
#             where coalesce(sa.quantity,0) > coalesce(sa.received_qty,0) \
#             and sa.product_id = $1; \
#             $$ LANGUAGE SQL; \
#             select coalesce(qty_incoming_booked_p(pp_o.id),0) as qty_incoming_booked, \
#             pp_o.id as prod_id from product_product pp_o \
#             inner join product_template pt_o on pp_o.id = pt_o.id where  \
#             " + pp_qry + "order by pt_o.name")
#         qry3 = cr.dictfetchall()
#         if qry3:
#             for s in qry3:
#                 res[s['prod_id']] = s['qty_incoming_booked']
#         return res
# 
#     def get_incoming_non_booked(self, cr, uid, ids, context=None):
#         context = None
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
#         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
#  
#         cr.execute("CREATE OR REPLACE FUNCTION qty_incoming_non_booked_p(integer) RETURNS numeric AS $$ \
#             select sum( \
#             (pol.product_qty -  \
#             coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id and sm.state = 'done'),0)) - \
#             coalesce((select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
#             where sa.purchase_line_id = pol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)) \
#             ,0)) \
#             from purchase_order_line pol \
#             where pol.product_id = $1 and state not in ('draft', 'cancel') \
#             $$ LANGUAGE SQL; \
#             select coalesce(qty_incoming_non_booked_p(pp_o.id),0) as qty_incoming_non_booked, \
#             pp_o.id as prod_id from product_product pp_o \
#             inner join product_template pt_o on pp_o.id = pt_o.id where  \
#             " + pp_qry + "order by pt_o.name")
#         qry3 = cr.dictfetchall()
#         if qry3:
#             for s in qry3:
#                 res[s['prod_id']] = s['qty_incoming_non_booked']
#         return res
# 
#     def _qty_booked(self, cr, uid, ids, context=None):
# 
#         context = None
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
# 
#         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
#         cr.execute("CREATE OR REPLACE FUNCTION qty_booked_p(integer) RETURNS numeric AS $$ \
#            select sum( \
#            (sol.product_uom_qty -  \
#            coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0))) \
#            from sale_order_line sol \
#            where sol.product_id = $1 and state not in ('draft', 'cancel') \
#            $$ LANGUAGE SQL; \
#            select coalesce(qty_booked_p(pp_o.id),0) as qty_booked, \
#            pp_o.id as prod_id from product_product pp_o \
#            inner join product_template pt_o on pp_o.id = pt_o.id where  \
#            " + pp_qry + "order by pt_o.name")
#         qry3 = cr.dictfetchall()
#         if qry3:
#             for s in qry3:
#                 res[s['prod_id']] = s['qty_booked']
# 
#         return res
# 
#     def _qty_free(self, cr, uid, ids, context=None):
# 
#         context = None
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
# 
#         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
#  
#         cr.execute("CREATE OR REPLACE FUNCTION qty_allocated_p(integer) RETURNS numeric AS $$ \
#             select sum( \
#             sol.qty_onhand_allocated +  \
#             coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
#             where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
#             coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
#             where sol.product_id = $1 and state not in ('draft', 'cancel') \
#             $$ LANGUAGE SQL; \
#             select coalesce(qty_allocated_p(pp_o.id),0) as qty_allocated, \
#             pp_o.id as prod_id from product_product pp_o \
#             inner join product_template pt_o on pp_o.id = pt_o.id where  \
#             " + pp_qry + "order by pt_o.name")
#         qry3 = cr.dictfetchall()
#         if qry3:
#             for s in qry3:
#                 qty_avb = self.browse(cr, uid, s['prod_id'], context=context).qty_available
#                 res[s['prod_id']] = qty_avb - s['qty_allocated']
#         return res
# 
#     def _qty_allocated(self, cr, uid, ids, context=None):
# 
#         context = None
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
# 
#         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
#  
#         cr.execute("CREATE OR REPLACE FUNCTION qty_allocated_p(integer) RETURNS numeric AS $$ \
#             select sum( \
#             sol.qty_onhand_allocated +  \
#             coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
#             where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
#             coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
#             where sol.product_id = $1 and state not in ('draft', 'cancel') \
#             $$ LANGUAGE SQL; \
#             select coalesce(qty_allocated_p(pp_o.id),0) as qty_allocated, \
#             pp_o.id as prod_id from product_product pp_o \
#             inner join product_template pt_o on pp_o.id = pt_o.id where  \
#             " + pp_qry + "order by pt_o.name")
#         qry3 = cr.dictfetchall()
#         if qry3:
#             for s in qry3:
#                 res[s['prod_id']] = s['qty_allocated']
#         return res
# 
#     def _qty_free_balance(self, cr, uid, ids, context=None):
#  
#         context = None
#         if not ids:
#             ids = self.search(cr, uid, [])
#         res = {}.fromkeys(ids, 0.0)
#         if not ids:
#             return res
#  
# #         pp_qry = (ids and ((len(ids) == 1 and "pp_o.id = " + str(ids[0]) + " ") or "pp_o.id IN " + str(tuple(ids)) + " ")) or "pp_o.id IN (0) "
# # 
# #         cr.execute("CREATE OR REPLACE FUNCTION qty_incoming_non_booked_p(integer) RETURNS numeric AS $$ \
# #             select sum( \
# #             (pol.product_qty -  \
# #             coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id and sm.state = 'done'),0)) - \
# #             coalesce((select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
# #             where sa.purchase_line_id = pol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)) \
# #             ,0)) \
# #             from purchase_order_line pol \
# #             where pol.product_id = $1 and state not in ('draft', 'cancel') \
# #             $$ LANGUAGE SQL; \
# #             CREATE OR REPLACE FUNCTION qty_allocated_p(integer) RETURNS numeric AS $$ \
# #             select sum( \
# #             sol.qty_onhand_allocated +  \
# #             coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
# #             where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
# #             coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
# #             where sol.product_id = $1 and state not in ('draft', 'cancel') \
# #             $$ LANGUAGE SQL; \
# #             select coalesce(qty_incoming_non_booked_p(pp_o.id),0) - coalesce(qty_allocated_p(pp_o.id),0) as qty_free_balance, \
# #             pp_o.id as prod_id from product_product pp_o \
# #             inner join product_template pt_o on pp_o.id = pt_o.id where  \
# #             " + pp_qry + "order by pt_o.name")
# # 
# #         qry3 = cr.dictfetchall()
# #         if qry3:
# #             for s in qry3:
#         for prod in ids:
#             pp = self.browse(cr, uid, prod, context=context)
#             qty_avb = pp.qty_available
#             qty_incoming_non_booked = pp.qty_incoming_non_booked
#             qty_allocated = pp.qty_allocated
#             res[prod] = qty_avb + (qty_incoming_non_booked - qty_allocated)
#         return res
#  
# #     def get_incoming_booked(self, cr, uid, ids, context=None):
# #         if context is None:
# #             context = {}
# #         if not ids:
# #             ids = self.search(cr, uid, [])
# #         res = {}.fromkeys(ids, 0.0)
# #         if not ids:
# #             return res
# # 
# #         sale_allocated_obj = self.pool.get("sale.allocated")
# #         purchase_line_ids = []
# #         qty_purchases = {}
# #         qty_arrives = {}
# # 
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             purchase_qty = 0.00
# # #            product_id = obj.id
# # #            sale_allocated_ids = sale_allocated_obj.search(cr, uid, [('product_id','=',product_id),('receive','=',False)], order='purchase_line_id ASC')
# # #            val_sale_allocated = ''
# # #            if sale_allocated_ids:
# # #                val_sale_allocated = ','.join(map(str, sale_allocated_ids))
# #             cr.execute("select coalesce(sum(COALESCE( quantity, 0) - COALESCE( received_qty, 0)),0) as purchase_qty " \
# #                             "from sale_allocated where COALESCE( quantity, 0) > COALESCE(received_qty, 0) " \
# #                             "and product_id = " + str(obj.id))
# #             res_general = cr.dictfetchall()
# #             if res_general:
# #                 for val in res_general:
# #                     purchase_qty = val['purchase_qty']
# #             res[obj.id] = purchase_qty
# #         return res
#  
# #     def get_incoming_non_booked(self, cr, uid, ids, context=None):
# #         context = None
# #         if not ids:
# #             ids = self.search(cr, uid, [])
# #         res = {}.fromkeys(ids, 0.0)
# #         if not ids:
# #             return res
# #         purchase_qty = 0.00
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             cr.execute("select COALESCE(sum((pol.product_qty / " \
# #                        "(CASE WHEN pu_po.uom_type = 'reference' THEN pu_po.factor " \
# #                        "WHEN pu_po.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) / pu_po.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) * pu_po.factor) END) * " \
# #                        "(CASE WHEN pu_pt.uom_type = 'reference' THEN pu_pt.factor " \
# #                        "WHEN pu_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) / pu_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) * pu_pt.factor) END)" \
# #                        ") - (" \
# #                        "(COALESCE(" \
# #                        "(select sum((sm.product_qty / " \
# #                        "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
# #                        "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
# #                        "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
# #                        "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
# #                        "from stock_move sm " \
# #                        "left join product_template pt_sm on sm.product_id = pt_sm.id " \
# #                        "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
# #                        "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
# #                        "where sm.purchase_line_id = pol.id and sm.state = 'done' " \
# #                        ") " \
# #                        ", 0)) - " \
# #                        "COALESCE((select sum(COALESCE(received_qty, 0)) as qty_received from sale_allocated where sale_allocated.purchase_line_id = pol.id and id in (select id from sale_allocated so where so.product_id = " + str(obj.id) + " and (coalesce(so.quantity,0) - coalesce(so.received_qty,0)) != 0)), 0)" \
# #                        ")),0) as qtyp " \
# #                        "from purchase_order_line pol " \
# #                        "left join product_template pt on pol.product_id = pt.id " \
# #                        "left join product_uom pu_po on pol.product_uom = pu_po.id " \
# #                        "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
# #                        "where pol.product_id = " + str(obj.id) + " and pol.state not in ('done', 'draft', 'cancel')")
# #             res_general = cr.dictfetchall()
# #             if res_general:
# #                 for val in res_general:
# #                     purchase_qty = val['qtyp']
# #             res[obj.id] = purchase_qty
# #         return res
#  
# #     def _qty_booked(self, cr, uid, ids, context=None):
# # 
# #         if not ids: return {}
# #         res = {}
# #         sale_order_line_obj = self.pool.get("sale.order.line")
# #         stock_move_obj = self.pool.get("stock.move")
# #         uom_obj = self.pool.get("product.uom")
# #         purchase_qty = 0.00
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             cr.execute("select COALESCE(sum((sol.product_uom_qty / " \
# #                        "(CASE WHEN pu_sol.uom_type = 'reference' THEN pu_sol.factor " \
# #                        "WHEN pu_sol.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sol.category_id and uom_type = 'reference' limit 1) / pu_sol.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sol.category_id and uom_type = 'reference' limit 1) * pu_sol.factor) END) * " \
# #                        "(CASE WHEN pu_pt.uom_type = 'reference' THEN pu_pt.factor " \
# #                        "WHEN pu_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) / pu_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) * pu_pt.factor) END)" \
# #                        ") - " \
# #                        "(COALESCE(" \
# #                        "(select sum((sm.product_qty / " \
# #                        "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
# #                        "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
# #                        "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
# #                        "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
# #                        "from stock_move sm " \
# #                        "left join product_template pt_sm on sm.product_id = pt_sm.id " \
# #                        "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
# #                        "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
# #                        "where sm.sale_line_id = sol.id and sm.state = 'done' " \
# #                        ") " \
# #                        ", 0))" \
# #                        "),0) as qtyp "\
# #                        "from sale_order_line sol " \
# #                        "left join product_template pt on sol.product_id = pt.id " \
# #                        "left join product_uom pu_sol on sol.product_uom = pu_sol.id " \
# #                        "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
# #                        "where sol.product_id = " + str(obj.id) + " and sol.state not in ('done', 'draft', 'cancel')")
# #             res_general = cr.dictfetchall()
# #             if res_general:
# #                 for val in res_general:
# #                     purchase_qty = val['qtyp']
# #             res[obj.id] = purchase_qty
# #         return res
#  
# #     def _qty_free(self, cr, uid, ids, context=None):
# # 
# #         if not ids: return {}
# #         res = {}
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             qty_p = 0.00
# #             cr.execute("select COALESCE(sum((sol.qty_onhand_allocated + " \
# #                        "COALESCE((select sum(COALESCE(received_qty, 0)) as qty_received from sale_allocated where sale_allocated.sale_line_id = sol.id), 0)" \
# #                         ") - " \
# #                        "(COALESCE(" \
# #                        "(select sum((sm.product_qty / " \
# #                        "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
# #                        "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
# #                        "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
# #                        "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
# #                        "from stock_move sm " \
# #                        "left join product_template pt_sm on sm.product_id = pt_sm.id " \
# #                        "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
# #                        "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
# #                        "where sm.sale_line_id = sol.id and sm.state = 'done' " \
# #                        ") " \
# #                        ", 0))" \
# #                        "),0) as qtyp "\
# #                        "from sale_order_line sol " \
# #                        "left join product_template pt on sol.product_id = pt.id " \
# #                        "left join product_uom pu_sol on sol.product_uom = pu_sol.id " \
# #                        "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
# #                        "where sol.product_id = " + str(obj.id) + " and sol.state not in ('done', 'draft', 'cancel')")
# #             res_general = cr.dictfetchall()
# #             for val in res_general:
# #                 qty_p = val['qtyp']
# #             res[obj.id] = obj.qty_available - qty_p
# #         return res
#  
# #     def _qty_allocated(self, cr, uid, ids, context=None):
# # 
# #         if not ids: return {}
# #         res = {}
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             qty_p = 0.00
# #             cr.execute("select COALESCE(sum((sol.qty_onhand_allocated + " \
# #                        "COALESCE((select sum(COALESCE(received_qty, 0)) as qty_received from sale_allocated where sale_allocated.sale_line_id = sol.id), 0)" \
# #                         ") - " \
# #                        "(COALESCE(" \
# #                        "(select sum((sm.product_qty / " \
# #                        "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
# #                        "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
# #                        "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
# #                        "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
# #                        "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
# #                        "from stock_move sm " \
# #                        "left join product_template pt_sm on sm.product_id = pt_sm.id " \
# #                        "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
# #                        "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
# #                        "where sm.sale_line_id = sol.id and sm.state = 'done' " \
# #                        ") " \
# #                        ", 0))" \
# #                        "),0) as qtyp "\
# #                        "from sale_order_line sol " \
# #                        "left join product_template pt on sol.product_id = pt.id " \
# #                        "left join product_uom pu_sol on sol.product_uom = pu_sol.id " \
# #                        "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
# #                        "where sol.product_id = " + str(obj.id) + " and sol.state not in ('done', 'draft', 'cancel')")
# #             res_general = cr.dictfetchall()
# #             for val in res_general:
# #                 qty_p = val['qtyp']
# #             res[obj.id] = qty_p
# #         return res
#  
# #     def _qty_free_balance(self, cr, uid, ids, context=None):
# # 
# #         if not ids: return {}
# #         res = {}
# #         for obj in self.browse(cr, uid, ids, context=context):
# #             res[obj.id] = obj.qty_incoming_non_booked + obj.qty_free
# #         return res
#  
# #    def _product_available2(self, cr, uid, ids, field_names=None, arg=False, context=None):
# #        """ Finds the incoming and outgoing quantity of product.
# #        @return: Dictionary of values
# #        """
# #        if not field_names:
# #            field_names = []
# #        if context is None:
# #            context = {}
# #        res = {}
# #        for id in ids:
# #            res[id] = {}.fromkeys(field_names, 0.0)
# #        for f in field_names:
# #            c = context.copy()
# #            #print f
# #            if f == 'qty_incoming_booked':
# #                stock = self.get_incoming_booked(cr, uid, ids, context=None)
# #                #print stock
# #            if f == 'qty_incoming_non_booked':
# #                stock = self.get_incoming_non_booked(cr, uid, ids, context=None)
# #            for id in ids:
# #                res[id][f] = stock.get(id, 0.0)
# #        print 'res'
# #        return res

    _columns = {
        'product_temp1': fields.char('Temporary 1', size=128),
        'product_temp2': fields.char('Temporary 2', size=128),
        'spq': fields.float('Standard Packaging Qty', required=True),
        'inventory_price': fields.float('Inventory Cost', digits_compute=dp.get_precision('Purchase Price')),
        'lead_time': fields.float('Lead Time',),
        'qty_available': fields.function(_product_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product UoM'),
            string='Quantity On Hand',
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "typed as 'internal'."),
        'qty_incoming_booked': fields.function(_product_available, multi='qty_available',
            type='float', string='Quantity PO Allocated',
            help='the incoming quantity which not arrived at warehouse and has been allocated by sales order'),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product UoM'),
            string='Quantity Available',
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "typed as 'internal'."),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product UoM'),
            string='Incoming',
            help="Quantity of products that are planned to arrive.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods arriving to this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods arriving to the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "arriving to the Stock Location of the Warehouse of this "
                 "Shop, or any of its children.\n"
                 "Otherwise, this includes goods arriving to any Stock "
                 "Location typed as 'internal'."),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            type='float',  digits_compute=dp.get_precision('Product UoM'),
            string='Outgoing',
            help="Quantity of products that are planned to leave.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods leaving from this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods leaving from the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "In a context with a single Shop, this includes goods "
                 "leaving from the Stock Location of the Warehouse of this "
                 "Shop, or any of its children.\n"
                 "Otherwise, this includes goods leaving from any Stock "
                 "Location typed as 'internal'."),
        'qty_incoming_non_booked': fields.function(_product_available, multi='qty_available',
            type='float', string='Quantity PO Un-Allocated',
            help='the incoming quantity which not arrived at warehouse and not been allocated by sales order'),
        'qty_booked': fields.function(_product_available, multi='qty_available',
            type='float', string='Total SO Quantity',
            help='the quantity which allocated by sales order'),
        'qty_free': fields.function(_product_available, multi='qty_available',
            type='float', string='Quantity On Hand Free',
            help='the quantity in warehouse which not been allocated by sales order'),
        'qty_allocated': fields.function(_product_available, multi='qty_available',
            type='float', string='Quantity On Hand Allocated',
            help='the quantity in warehouse which has been allocated by sales order'),
        'qty_free_balance': fields.function(_product_available, multi='qty_available',
            type='float', string='Quantity Free Balance',
            help='the summary of quantity Incoming Un-Allocated plus Quantity on Hand Free'),
        # RT
        'qty_do': fields.function(_product_available, multi='qty_available',
            type='float', string='Do Quantity',
            help='the summary of Do Quantity'),
        'location_ids' : fields.one2many('product.location', 'product_id', 'Location Detail'),
        'brand_id': fields.many2one('product.brand','Product Brand', required=True),
        'brand_name': fields.related('brand_id','name', type='char', readonly=True, size=64, relation='product.brand', string='Brand Name'),
        'max_categ_id': fields.many2one('product.categ.max','Product Category', required=True),
    }

    _defaults = {
        'type': lambda *a: 'product',
        'procure_method': lambda *a: 'make_to_order',
        'cost_method': lambda *a: 'average',
        'valuation': lambda *a: 'real_time',
        'taxes_id': _get_default_taxes_id,
        'supplier_taxes_id': _get_default_supplier_taxes_id,
        'location_ids' : _get_default_location,
    }

product_product()

class product_location(osv.osv):
    _name = "product.location"
    _description = "Product Location"

    _columns = {
        'stock_location_id' : fields.many2one('stock.location', 'Location', select=1, required=True),
        'product_id' : fields.many2one('product.product', 'Product', select=1, ondelete='cascade', required=True),
        'default_key' : fields.boolean('Default location'),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(stock_location_id, product_id)', 'Location must be unique per Product!'),
    ]

product_location()

class product_brand(osv.osv):
    _name = "product.brand"
    _description = "Product Brand"

    def create(self, cr, user, vals, context=None):
        #RT
        name = ('name' in vals and vals['name']) or False
        

        vals.update({'name':name.strip().upper()})

        return super(product_brand, self).create(cr, user, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        brand_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        name = ('name' in vals and vals['name']) or False
        if not 'name' in vals:
            name = (self.pool.get('product.brand').browse(cr, uid, brand_id, context=None).name)
        vals.update({'name':name.strip().upper()})
        #end RT

        return super(product_brand, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(name)', 'Product Brand must be unique!'),
    ]

product_brand()

class product_categ_max(osv.osv):
    _name = "product.categ.max"
    _description = "Product Category Max"

#RT
    def create(self, cr, user, vals, context=None):
        #RT
        name = ('name' in vals and vals['name']) or False
        

        vals.update({'name':name.strip().upper()})

        return super(product_categ_max, self).create(cr, user, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        product_categ_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        name = ('name' in vals and vals['name']) or False
        if not 'name' in vals:
            name = (self.pool.get('product.categ.max').browse(cr, uid, product_categ_id, context=None).name)
        vals.update({'name':name.strip().upper()})
        #end RT

        return super(product_categ_max, self).write(cr, uid, ids, vals, context=context)

#END RT

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(name)', 'Product Category must be unique!'),
    ]

product_categ_max()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

