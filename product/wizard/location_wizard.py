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

from osv import fields, osv
from tools.translate import _
import netsvc
import math
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare

class product_location_wizard(osv.osv_memory):
    _name = "product.location.wizard"
    _description = "Product Location Wizard"

    def stock_location_get(self, cr, uid, product_id, context=None):
        sale_order_obj = self.pool.get('sale.order')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        product_product_obj = self.pool.get('product.product')
        stock_location_obj = self.pool.get('stock.location')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        sale_allocated_obj = self.pool.get("sale.allocated")
        sale_order_line_obj = self.pool.get("sale.order.line")
        result1 = []
        if context is None:
            context = {}
        location_srch = context.get('location_id', False)
#         product = product_product_obj.browse(cr, uid, product_id, context=context)
        pp_qry = (product_id and ((len(product_id) == 1 and "AND pp_o.id = " + str(product_id[0]) + " ") or "AND pp_o.id IN " + str(tuple(product_id)) + " ")) or "AND pp_o.id IN (0) "

        if location_srch:
            location_qry = (location_srch and ((len(location_srch) == 1 and "AND id = " + str(location_srch[0]) + " ") or \
                    "AND id IN " + str(tuple(location_srch)) + " ")) or "AND id IN (0) "

            cr.execute("select id as sl_id, name as sl_name \
            from stock_location \
            where id not in (select distinct location_id from stock_location WHERE location_id IS NOT NULL) \
            and usage = 'internal' " + location_qry  + " \
            order by name")
        else:
            cr.execute("select id as sl_id, name as sl_name \
            from stock_location \
            where id not in (select distinct location_id from stock_location WHERE location_id IS NOT NULL) \
            and usage = 'internal' \
            order by name")
        qry2 = cr.dictfetchall()
        if qry2:
            for r in qry2:
                cr.execute("CREATE OR REPLACE FUNCTION qty_available(integer,integer) RETURNS numeric AS $$ \
                    SELECT sum(AA.product_qty) as sum_product_qty FROM \
                    (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id, \
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id, \
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value, \
                    CASE when pt.uom_id = m.product_uom \
                    THEN \
                    coalesce(sum(-m.product_qty)::decimal, 0.0) \
                    ELSE \
                    coalesce(sum(-m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty \
                    FROM \
                    stock_move m \
                    LEFT JOIN stock_picking p ON (m.picking_id=p.id) \
                    LEFT JOIN product_product pp ON (m.product_id=pp.id) \
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id) \
                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id) \
                    LEFT JOIN product_uom u ON (m.product_uom=u.id) \
                    LEFT JOIN stock_location l ON (m.location_id=l.id) \
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id, \
                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id \
                    UNION ALL \
                    SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id, \
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id, \
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value, \
                    CASE when pt.uom_id = m.product_uom \
                    THEN \
                    coalesce(sum(m.product_qty)::decimal, 0.0) \
                    ELSE \
                    coalesce(sum(m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty \
                    FROM \
                    stock_move m \
                    LEFT JOIN stock_picking p ON (m.picking_id=p.id) \
                    LEFT JOIN product_product pp ON (m.product_id=pp.id) \
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id) \
                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id) \
                    LEFT JOIN product_uom u ON (m.product_uom=u.id) \
                    LEFT JOIN stock_location l ON (m.location_dest_id=l.id) \
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id, \
                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id \
                    ) \
                    AS AA \
                    INNER JOIN stock_location sl on sl.id = AA.location_id \
                    LEFT JOIN stock_location sl1 on sl1.id = sl.location_id \
                    LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id \
                    LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id \
                    LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id \
                    LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id \
                    LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id \
                    LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id \
                    WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = $1 and aa.location_id = $2 \
                    GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id \
                    HAVING sum(AA.product_qty) > 0; \
                    $$ LANGUAGE SQL; \
                    CREATE OR REPLACE FUNCTION qty_incoming_booked(integer,integer) RETURNS numeric AS $$ \
                    select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty \
                    from sale_allocated sa \
                    inner join purchase_order_line pol on sa.purchase_line_id = pol.id \
                    where coalesce(sa.quantity,0) > coalesce(sa.received_qty,0) and pol.location_dest_id = $2 \
                    and sa.product_id = $1; \
                    $$ LANGUAGE SQL; \
                    CREATE OR REPLACE FUNCTION qty_incoming_non_booked(integer,integer) RETURNS numeric AS $$ \
                    select sum( \
                    (pol.product_qty -  \
                    coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id and sm.state = 'done'),0)) - \
                    coalesce((select sum(coalesce(sa.quantity,0) - coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                    where sa.purchase_line_id = pol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)) \
                    ,0)) \
                    from purchase_order_line pol \
                    where pol.product_id = $1 and state not in ('draft', 'cancel') and pol.location_dest_id = $2 \
                    $$ LANGUAGE SQL; \
                    CREATE OR REPLACE FUNCTION qty_booked(integer,integer) RETURNS numeric AS $$ \
                    select sum( \
                    (sol.product_uom_qty -  \
                    coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0))) \
                    from sale_order_line sol \
                    where sol.product_id = $1 and state not in ('draft', 'cancel') and sol.location_id = $2 \
                    $$ LANGUAGE SQL; \
                    CREATE OR REPLACE FUNCTION qty_allocated(integer,integer) RETURNS numeric AS $$ \
                    select sum( \
                    sol.qty_onhand_allocated +  \
                    coalesce((select sum(coalesce(sa.received_qty,0)) as qty from sale_allocated sa \
                    where sa.sale_line_id = sol.id and COALESCE(sa.quantity, 0) > COALESCE(sa.received_qty, 0)),0) -  \
                    coalesce((select sum(sm.product_qty) from stock_move sm where sm.sale_line_id = sol.id and sm.state = 'done'),0)) from sale_order_line sol \
                    where sol.product_id = $1 and state not in ('draft', 'cancel') and sol.location_id = $2 \
                    $$ LANGUAGE SQL; \
                    select coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) as qty_available, \
                    coalesce(qty_incoming_booked(pp_o.id," + str(r['sl_id']) + "),0) as qty_incoming_booked, \
                    coalesce(qty_incoming_non_booked(pp_o.id," + str(r['sl_id']) + "),0) as qty_incoming_non_booked, \
                    coalesce(qty_booked(pp_o.id," + str(r['sl_id']) + "),0) as qty_booked, \
                    coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) - coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) as qty_free, \
                    coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) as qty_allocated, \
                    coalesce(qty_incoming_non_booked(pp_o.id," + str(r['sl_id']) + "),0) + coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) - coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) as qty_free_balance, \
                    pt_o.name as prod_name from product_product pp_o \
                    inner join product_template pt_o on pp_o.id = pt_o.id where  \
                    (coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) > 0 or  \
                    coalesce(qty_incoming_booked(pp_o.id," + str(r['sl_id']) + "),0) > 0 or \
                    coalesce(qty_incoming_non_booked(pp_o.id," + str(r['sl_id']) + "),0) > 0 or \
                    coalesce(qty_booked(pp_o.id," + str(r['sl_id']) + "),0) > 0 or \
                    coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) - coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) > 0 or \
                    coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) > 0 or \
                    coalesce(qty_incoming_non_booked(pp_o.id," + str(r['sl_id']) + "),0) + coalesce(qty_available(pp_o.id," + str(r['sl_id']) + "),0) - coalesce(qty_allocated(pp_o.id," + str(r['sl_id']) + "),0) > 0 \
                    ) \
                    " + pp_qry + "order by pt_o.name")
                qry3 = cr.dictfetchall()
                if qry3:
                    for s in qry3:
                        result1.append({
                            'location_id': r['sl_id'],
                            'location_name': r['sl_name'],
                            'prod_name': s['prod_name'],
                            'qty_available' : s['qty_available'],
                            'qty_incoming_booked' : s['qty_incoming_booked'],
                            'qty_incoming_non_booked' : s['qty_incoming_non_booked'],
                            'qty_booked' : s['qty_booked'],
                            'qty_free' : s['qty_free'],
                            'qty_allocated': s['qty_allocated'],
                            'qty_free_balance' : s['qty_free_balance'],
                            })
        return result1

#     def stock_location_get(self, cr, uid, product_id, context=None):
#         sale_order_obj = self.pool.get('sale.order')
#         stock_move_obj = self.pool.get('stock.move')
#         product_uom_obj = self.pool.get('product.uom')
#         product_product_obj = self.pool.get('product.product')
#         stock_location_obj = self.pool.get('stock.location')
#         purchase_order_line_obj = self.pool.get('purchase.order.line')
#         sale_allocated_obj = self.pool.get("sale.allocated")
#         sale_order_line_obj = self.pool.get("sale.order.line")
#         result1 = []
#         if context is None:
#             context = {}
#         location_srch = context.get('location_id', False)
#         product = product_product_obj.browse(cr, uid, product_id, context=context)
#         cr.execute('''SELECT sum(AA.product_qty) as sum_product_qty, aa.location_id FROM
#             (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
#             m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
#             m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
#             CASE when pt.uom_id = m.product_uom
#             THEN
#                 coalesce(sum(-m.product_qty)::decimal, 0.0)
#             ELSE
#                 coalesce(sum(-m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
#             FROM
#                 stock_move m
#                 LEFT JOIN stock_picking p ON (m.picking_id=p.id)
#                 LEFT JOIN product_product pp ON (m.product_id=pp.id)
#                 LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
#                 LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
#                 LEFT JOIN product_uom u ON (m.product_uom=u.id)
#                 LEFT JOIN stock_location l ON (m.location_id=l.id)
#             GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
#                 m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
#             UNION ALL
#             SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
#             m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
#             m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
#             CASE when pt.uom_id = m.product_uom
#             THEN
#                 coalesce(sum(m.product_qty)::decimal, 0.0)
#             ELSE
#                 coalesce(sum(m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
#             FROM
#                 stock_move m
#                 LEFT JOIN stock_picking p ON (m.picking_id=p.id)
#                 LEFT JOIN product_product pp ON (m.product_id=pp.id)
#                 LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
#                 LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
#                 LEFT JOIN product_uom u ON (m.product_uom=u.id)
#                 LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
#             GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
#                 m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
#             ) AS AA
#                 INNER JOIN stock_location sl on sl.id = AA.location_id
#                 LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
#                 LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
#                 LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
#                 LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
#                 LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
#                 LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
#                 LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
#                 WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = ''' + str(product.id)
#                 + '''GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
#                 HAVING sum(AA.product_qty) > 0''')
# 
#         for product_qty, location_id in cr.fetchall():
#             record_found = False
#             for liv in result1:
#                 if liv['location_id'] == location_id:
#                     record_found = True
#                     liv['qty_available'] = liv['qty_available'] + product_qty
#                     liv['qty_free'] = liv['qty_free'] + product_qty
#             if record_found == False:
#                 record_found = True
#                 location_ids_vals = {
#                     'location_id': location_id,
#                     'qty_available' : product_qty,
#                     'qty_incoming_booked' : 0.00,
#                     'qty_incoming_non_booked' : 0.00,
#                     'qty_booked' : 0.00,
#                     'qty_free' : product_qty,
#                     'qty_free_balance' : 0.00,
#                     }
#                 result1.append(location_ids_vals)
# 
#         sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('product_id','=',product.id),('receive','=',False)], order='purchase_line_id ASC'), context=context)
#         if sale_allocated_ids:
#             for val in sale_allocated_ids:
#                 if val.quantity > val.received_qty:
#                     pol_location_id = purchase_order_line_obj.browse(cr, uid, val.purchase_line_id.id, context=context).location_dest_id.id
#                     record_found = False
#                     for liv in result1:
#                         if liv['location_id'] == pol_location_id:
#                             record_found = True
#                             liv['qty_incoming_booked'] = liv['qty_incoming_booked'] + (val.quantity - val.received_qty)
# 
#                     if record_found == False:
#                         record_found = True
#                         location_ids_vals = {
#                             'location_id': pol_location_id,
#                             'qty_available' : 0.00,
#                             'qty_incoming_booked' : (val.quantity - val.received_qty),
#                             'qty_incoming_non_booked' : 0.00,
#                             'qty_booked' : 0.00,
#                             'qty_free' : 0.00,
#                             'qty_free_balance' : 0.00,
#                             }
#                         result1.append(location_ids_vals)
# 
#         purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',product.id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])
#         if purchase_order_line_ids:
# #                raise osv.except_osv(_('Debug !'), _(str(purchase_order_line_ids) + '----' + '' + '----' + ''))
#             for val in purchase_order_line_ids:
#                 pol = purchase_order_line_obj.browse(cr, uid, val, context=context)
#                 qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, product.uom_id.id)
#                 sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
#                 qty_allocated = 0.00
#                 qty_received = 0.00
#                 incoming_qty = 0.00
#                 if sale_allocated_ids:
#                     for val in sale_allocated_ids:
#                         qty_allocated = qty_allocated + val.quantity
#                         qty_received = qty_received + val.received_qty
#                 if qtyp > 0:
#                     stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
#                     if stock_move_ids:
#                         for stock_move_id in stock_move_ids:
#                             stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
#                             incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, product.uom_id.id)
#                 qtyp = qtyp - (incoming_qty - qty_received) - qty_allocated
# #                    raise osv.except_osv(_('Debug !'), _(str(qtyp) + '----' + '' + '----' + ''))
#                 if qtyp > 0:
#                     record_found = False
#                     for liv in result1:
#                         if liv['location_id'] == pol.location_dest_id.id:
#                             record_found = True
#                             liv['qty_incoming_non_booked'] = liv['qty_incoming_non_booked'] + qtyp
#                             
#                     if record_found == False:
#                         record_found = True
#                         location_ids_vals = {
#                             'location_id': pol.location_dest_id.id,
#                             'qty_available' : 0.00,
#                             'qty_incoming_booked' : 0.00,
#                             'qty_incoming_non_booked' : qtyp,
#                             'qty_booked' : 0.00,
#                             'qty_free' : 0.00,
#                             'qty_free_balance' : 0.00,
#                             }
#                         result1.append(location_ids_vals)
# 
#         sale_order_line_ids = sale_order_line_obj.search(cr, uid, [('product_id','=',product.id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')])
#         if sale_order_line_ids:
#             for val in sale_order_line_ids:
#                 sol = sale_order_line_obj.browse(cr, uid, val, context=context)
#                 sale_qty = product_uom_obj._compute_qty(cr, uid, sol.product_uom.id, sol.product_uom_qty, product.uom_id.id)
#                 stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',val),('state','=','done')])
#                 do_qty = 0.00
#                 if stock_move_ids:
#                     for stock_move_id in stock_move_ids:
#                         stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
#                         do_qty = do_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, product.uom_id.id)
#                 if sale_qty - do_qty > 0:
#                     record_found = False
#                     for liv in result1:
#                         if liv['location_id'] == sol.location_id.id:
#                             record_found = True
#                             liv['qty_booked'] = liv['qty_booked'] + (sale_qty - do_qty)
# 
#                     if record_found == False:
#                         record_found = True
#                         location_ids_vals = {
#                             'location_id': sol.location_id.id,
#                             'qty_available' : 0.00,
#                             'qty_incoming_booked' : 0.00,
#                             'qty_incoming_non_booked' : 0.00,
#                             'qty_booked' : sale_qty - do_qty,
#                             'qty_free' : 0.00,
#                             'qty_free_balance' : 0.00,
#                             }
#                         result1.append(location_ids_vals)
# 
#         sale_order_line_ids = sale_order_line_obj.browse(cr, uid, sale_order_line_obj.search(cr, uid, [('product_id','=',product.id),('state','<>','draft'),('state','<>','done'),('state','<>','cancel')]), context=context)
#         allocated_onhand = 0.00
#         if sale_order_line_ids:
#             loc_vals = []
#             loc_qty = {}
# #                raise osv.except_osv(_('Debug !'), _(str(sale_order_line_ids)))
#             for val in sale_order_line_ids:
#                 allocated_onhand = val.qty_onhand_count
#                 stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',val.id),('state','=','done')])
#                 do_qty = 0.00
#                 if stock_move_ids:
#                     for stock_move_id in stock_move_ids:
#                         stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
#                         do_qty = do_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, product.uom_id.id)
# 
#                 record_found = False
#                 for liv in loc_vals:
#                     if liv == val.location_id.id:
#                         record_found = True
# #                            raise osv.except_osv(_('Debug !'), _(str(liv['qty_available']) + str(allocated_onhand) + 'qq' + '----' + str(do_qty)))
#                         loc_qty[liv] = loc_qty[liv] + (allocated_onhand - do_qty)
# #                            raise osv.except_osv(_('Debug !'), _(str(liv['qty_free'])))
#                 if record_found == False:
#                     record_found = True
#                     loc_vals.append(val.location_id.id)
#                     loc_qty[val.location_id.id] = allocated_onhand - do_qty
# 
#             for liv in result1:
#                 for liv2 in loc_vals:
#                     if liv['location_id'] == liv2:
#                         liv['qty_free'] = liv['qty_free'] - loc_qty[liv2]
# 
#         for liv in result1:
#             liv['qty_allocated'] = liv['qty_available'] - liv['qty_free']
#             liv['qty_free_balance'] = liv['qty_incoming_non_booked'] + liv['qty_free']
#         if location_srch:
#             res_serc = []
#             for srch in result1:
#                 if srch['location_id'] == location_srch:
#                     res_serc.append({
#                         'location_id': srch['location_id'],
#                         'qty_available' : srch['qty_available'],
#                         'qty_incoming_booked' : srch['qty_incoming_booked'],
#                         'qty_incoming_non_booked' : srch['qty_incoming_non_booked'],
#                         'qty_booked' : srch['qty_booked'],
#                         'qty_free' : srch['qty_free'],
#                         'qty_allocated': srch['qty_allocated'],
#                         'qty_free_balance' : srch['qty_free_balance'],
#                         })
#             return res_serc
#         return result1

    def default_get(self, cr, uid, fields, context=None):
        product_product_obj = self.pool.get('product.product')
        result1 = []
        if context is None:
            context = {}
        res = super(product_location_wizard, self).default_get(cr, uid, fields, context=context)
        for product in product_product_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            result1 = self.stock_location_get(cr, uid, [product.id], context=context)
        if 'location_ids' in fields:
            res.update({'location_ids': result1})
        return res

    _columns = {
        'location_ids' : fields.one2many('product.location.lines', 'wizard_id', 'Locations', readonly=True),
    }

product_location_wizard()

class product_location_lines(osv.osv_memory):
    _name = 'product.location.lines'
    _description = 'Product Location'

    _columns = {
        'wizard_id': fields.many2one('product.location.wizard', 'wizard id', ondelete='cascade',),
        'location_id': fields.many2one('stock.location', 'Location', ondelete='cascade', readonly=True),
        'qty_available' : fields.float('Quantity on Hand', readonly=True),
        'qty_incoming_booked': fields.float('Quantity Incoming Allocated', readonly=True),
        'qty_incoming_non_booked': fields.float('Quantity Incoming Un-Allocated', readonly=True),
        'qty_booked': fields.float('Total SO Quantity', readonly=True),
        'qty_free': fields.float('Quantity On Hand Free', readonly=True),
        'qty_allocated': fields.float('Quantity On Hand Allocated', readonly=True),
        'qty_free_balance': fields.float('Quantity Free Balance', readonly=True),
    }

product_location_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
