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

    def _qty_booked(self, cr, uid, ids, name, arg, context=None):

        if not ids: return {}
        res = {}
        sale_order_line_obj = self.pool.get("sale.order.line")
        stock_move_obj = self.pool.get("stock.move")
        uom_obj = self.pool.get("product.uom")
        purchase_qty = 0.00
        for obj in self.browse(cr, uid, ids, context=context):
            cr.execute("select COALESCE(sum((sol.product_uom_qty / " \
                       "(CASE WHEN pu_sol.uom_type = 'reference' THEN pu_sol.factor " \
                       "WHEN pu_sol.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sol.category_id and uom_type = 'reference' limit 1) / pu_sol.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sol.category_id and uom_type = 'reference' limit 1) * pu_sol.factor) END) * " \
                       "(CASE WHEN pu_pt.uom_type = 'reference' THEN pu_pt.factor " \
                       "WHEN pu_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) / pu_pt.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) * pu_pt.factor) END)" \
                       ") - " \
                       "(COALESCE(" \
                       "(select sum((sm.product_qty / " \
                       "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
                       "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
                       "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
                       "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
                       "from stock_move sm " \
                       "left join product_template pt_sm on sm.product_id = pt_sm.id " \
                       "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
                       "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
                       "where sm.sale_line_id = sol.id and sm.state = 'done' " \
                       ") " \
                       ", 0))" \
                       "),0) as qtyp "\
                       "from sale_order_line sol " \
                       "left join product_template pt on sol.product_id = pt.id " \
                       "left join product_uom pu_sol on sol.product_uom = pu_sol.id " \
                       "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
                       "where sol.product_id = " + str(obj.id) + " and sol.state not in ('done', 'draft', 'cancel')")
            res_general = cr.dictfetchall()
            for val in res_general:
                purchase_qty = val['qtyp']
            res[obj.id] = purchase_qty
            
        return res

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

    def _qty_free(self, cr, uid, ids, name, arg, context=None):

        if not ids: return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            qty_p = 0.00
            cr.execute("select COALESCE(sum((sol.qty_onhand_allocated + " \
                       "COALESCE((select sum(COALESCE(received_qty, 0)) as qty_received from sale_allocated where sale_allocated.sale_line_id = sol.id), 0)" \
                        ") - " \
                       "(COALESCE(" \
                       "(select sum((sm.product_qty / " \
                       "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
                       "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
                       "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
                       "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
                       "from stock_move sm " \
                       "left join product_template pt_sm on sm.product_id = pt_sm.id " \
                       "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
                       "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
                       "where sm.sale_line_id = sol.id and sm.state = 'done' " \
                       ") " \
                       ", 0))" \
                       "),0) as qtyp "\
                       "from sale_order_line sol " \
                       "left join product_template pt on sol.product_id = pt.id " \
                       "left join product_uom pu_sol on sol.product_uom = pu_sol.id " \
                       "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
                       "where sol.product_id = " + str(obj.id) + " and sol.state not in ('done', 'draft', 'cancel')")
            res_general = cr.dictfetchall()
            for val in res_general:
                qty_p = val['qtyp']
            res[obj.id] = obj.qty_available - qty_p
        return res


    def _qty_allocated(self, cr, uid, ids, name, arg, context=None):

        if not ids: return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.qty_available - obj.qty_free
        return res

    def _qty_free_balance(self, cr, uid, ids, name, arg, context=None):

        if not ids: return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.qty_incoming_non_booked + obj.qty_free
        return res

    def _product_available2(self, cr, uid, ids, field_names=None, arg=False, context=None):
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
            #print f
            if f == 'qty_incoming_booked':
                stock = self.get_incoming_booked(cr, uid, ids, context=None)
                #print stock
            if f == 'qty_incoming_non_booked':
                stock = self.get_incoming_non_booked(cr, uid, ids, context=None)
            for id in ids:
                res[id][f] = stock.get(id, 0.0)
        #print res
        return res

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

    def get_incoming_non_booked(self, cr, uid, ids, context=None):
        context = None
        if not ids:
            ids = self.search(cr, uid, [])
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res
        purchase_qty = 0.00
        sale_allocated_obj = self.pool.get("sale.allocated")
#        purchase_order_line_obj = self.pool.get("purchase.order.line")
        for obj in self.browse(cr, uid, ids, context=context):
#            purchase_qty = 0.00
#            product_id = obj.id
#            purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',product_id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])
#            if purchase_order_line_ids:
##                raise osv.except_osv(_('Debug !'), _(str(purchase_order_line_ids) + '----' + '' + '----' + ''))
#                for val in purchase_order_line_ids:
#                    pol = purchase_order_line_obj.browse(cr, uid, val, context=context)
#                    qtyp = self.count_non_booked(cr, uid, pol, context=context)
#                    purchase_qty = purchase_qty + qtyp
#                    
#            res[obj.id] = purchase_qty
##            purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',product_id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])

            sale_allocated_ids = sale_allocated_obj.search(cr, uid, [('receive','=',False)])
            val_sale_allocated = ''
            if sale_allocated_ids:
                val_sale_allocated = ','.join(map(str, sale_allocated_ids))
                val_sale_allocated =  " and id in (" + val_sale_allocated + ")"
            cr.execute("select COALESCE(sum((pol.product_qty / " \
                       "(CASE WHEN pu_po.uom_type = 'reference' THEN pu_po.factor " \
                       "WHEN pu_po.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) / pu_po.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_po.category_id and uom_type = 'reference' limit 1) * pu_po.factor) END) * " \
                       "(CASE WHEN pu_pt.uom_type = 'reference' THEN pu_pt.factor " \
                       "WHEN pu_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) / pu_pt.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_pt.category_id and uom_type = 'reference' limit 1) * pu_pt.factor) END)" \
                       ") - (" \
                       "(COALESCE(" \
                       "(select sum((sm.product_qty / " \
                       "(CASE WHEN pu_sm.uom_type = 'reference' THEN pu_sm.factor " \
                       "WHEN pu_sm.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) / pu_sm.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm.category_id and uom_type = 'reference' limit 1) * pu_sm.factor) END) * " \
                       "(CASE WHEN pu_sm_pt.uom_type = 'reference' THEN pu_sm_pt.factor " \
                       "WHEN pu_sm_pt.uom_type = 'bigger' THEN ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) / pu_sm_pt.factor) " \
                       "ELSE ((select factor from product_uom where category_id = pu_sm_pt.category_id and uom_type = 'reference' limit 1) * pu_sm_pt.factor) END))) " \
                       "from stock_move sm " \
                       "left join product_template pt_sm on sm.product_id = pt_sm.id " \
                       "left join product_uom pu_sm on sm.product_uom = pu_sm.id " \
                       "left join product_uom pu_sm_pt on pt_sm.uom_id = pu_sm_pt.id " \
                       "where sm.purchase_line_id = pol.id and sm.state = 'done' " \
                       ") " \
                       ", 0)) - " \
                       "COALESCE((select sum(COALESCE( received_qty, 0)) as qty_received from sale_allocated where sale_allocated.purchase_line_id = pol.id" + val_sale_allocated + "), 0)" \
                       ") - COALESCE((select sum(COALESCE( received_qty, 0)) as qty_received from sale_allocated where sale_allocated.purchase_line_id = pol.id" + val_sale_allocated + "), 0)),0) as qtyp " \
                       "from purchase_order_line pol " \
                       "left join product_template pt on pol.product_id = pt.id " \
                       "left join product_uom pu_po on pol.product_uom = pu_po.id " \
                       "left join product_uom pu_pt on pt.uom_id = pu_pt.id " \
                       "where pol.product_id = " + str(obj.id) + " and pol.state not in ('done', 'draft', 'cancel')")
            res_general = cr.dictfetchall()
            for val in res_general:
                purchase_qty = val['qtyp']
            res[obj.id] = purchase_qty
            
        return res

    def get_incoming_booked(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            ids = self.search(cr, uid, [])
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res

        
        #print purchase_qty
        sale_allocated_obj = self.pool.get("sale.allocated")
        purchase_line_ids = []
        qty_purchases = {}
        qty_arrives = {}
        
        for obj in self.browse(cr, uid, ids, context=context):
            purchase_qty = 0.00
            product_id = obj.id
#            sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('product_id','=',product_id),('receive','=',False)], order='purchase_line_id ASC'), context=context)
#            if sale_allocated_ids:
#                for val in sale_allocated_ids:
#                    if val.quantity > val.received_qty:
#                        purchase_qty = purchase_qty + (val.quantity - val.received_qty)
#                    raise osv.except_osv(_('Debug !'), _(str(purchase_qty) + '----' + '' + '----' + ''))
#            res[obj.id] = purchase_qty

            sale_allocated_ids = sale_allocated_obj.search(cr, uid, [('product_id','=',product_id),('receive','=',False)], order='purchase_line_id ASC')
            val_sale_allocated = ''
            if sale_allocated_ids:
                val_sale_allocated = ','.join(map(str, sale_allocated_ids))
#                print purchase_qty
                cr.execute("select sum(COALESCE( quantity, 0) - COALESCE( received_qty, 0)) as purchase_qty " \
                                "from sale_allocated where COALESCE( quantity, 0) > COALESCE(received_qty, 0) " \
                                "and id in (" + val_sale_allocated + ")")
                res_general = cr.dictfetchall()
                for val in res_general:
                    purchase_qty = val['purchase_qty']
#                print val_sale_allocated
#                print purchase_qty
#                raise osv.except_osv(_('Debug !'), _(str(purchase_qty) + '----' + '' + '----' + ''))
            res[obj.id] = purchase_qty
        #print res
        return res


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

    _columns = {
        'product_temp1': fields.char('Temporary 1', size=128),
        'product_temp2': fields.char('Temporary 2', size=128),
        'spq': fields.float('Standard Packaging Qty', required=True),
        'inventory_price': fields.float('Inventory Cost', digits_compute=dp.get_precision('Purchase Price')),
        'lead_time': fields.float('Lead Time',),
        'qty_incoming_booked': fields.function(_product_available2, multi='qty_incoming_booked',
            type='float', string='Quantity PO Allocated',
            help='the incoming quantity which not arrived at warehouse and has been allocated by sales order'),
        'qty_incoming_non_booked': fields.function(_product_available2, multi='qty_incoming_non_booked',
            type='float', string='Quantity PO Un-Allocated',
            help='the incoming quantity which not arrived at warehouse and not been allocated by sales order'),
        'qty_booked': fields.function(_qty_booked, type='float', string='Total SO Quantity',
            help='the quantity which allocated by sales order'),
        'qty_free': fields.function(_qty_free, type='float', string='Quantity On Hand Free',
            help='the quantity in warehouse which not been allocated by sales order'),
        'qty_allocated': fields.function(_qty_allocated, type='float', string='Quantity On Hand Allocated',
            help='the quantity in warehouse which has been allocated by sales order'),
        'qty_free_balance': fields.function(_qty_free_balance, type='float', string='Quantity Free Balance',
            help='the summary of quantity Incoming Un-Allocated plus Quantity on Hand Free'),
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

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
    }

    _sql_constraints = [
        ('number_uniq', 'unique(name)', 'Product Category must be unique!'),
    ]

product_categ_max()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
