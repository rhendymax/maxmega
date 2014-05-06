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

class change_warehouse_qty(osv.osv_memory):
    _name = 'change.warehouse.qty'
    _description = 'Change Quantity'

    def default_get(self, cr, uid, fields, context=None):
        purchase_order_obj = self.pool.get('purchase.order')
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        sale_order_line_obj = self.pool.get('sale.order.line')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        result1 = []
        if context is None:
            context = {}
        res = super(change_warehouse_qty, self).default_get(cr, uid, fields, context=context)
        product_uom_qty = 0.00
        product_uom = False

        product_uom_qty2 = 0.00
        product_uom22 = False

        qty_delivery = 0.00
        product_uom2 = False
        
        qty_location = 0.00
        qty_onhand_count = 0.00
        product_uom3 = False

        move_id = False
        for moves in stock_move_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            move_id = moves.id
            if moves.picking_id.type == 'in':
                spq = moves.purchase_line_id.spq
                pol_id = moves.purchase_line_id.id
                pol = purchase_order_line_obj.browse(cr, uid, pol_id, context=context)
                product_uom_qty = pol.product_qty
                product_uom = pol.product_uom.id

                move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol_id),('state','!=','cancel')])
                if move_ids:
                    for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                        qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
    
                qty_delivery = qty_delivery - product_uom_obj._compute_qty(cr, uid, moves.product_uom.id, moves.product_qty, moves.product_id.uom_id.id)
                product_uom2 = pol.product_id.uom_id.id

            if moves.picking_id.type == 'out':
                sol_id = moves.sale_line_id.id
                sol = sale_order_line_obj.browse(cr, uid, sol_id, context=context)
                product_uom_qty2 = sol.product_uom_qty
                product_uom22 = sol.product_uom.id

                move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',sol_id),('state','!=','cancel')])
                if move_ids:
                    for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                        qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
                
                qty_delivery = qty_delivery - product_uom_obj._compute_qty(cr, uid, moves.product_uom.id, moves.product_qty, moves.product_id.uom_id.id)
                product_uom2 = sol.product_id.uom_id.id

                qty_onhand_count = moves.sale_line_id.qty_onhand_count
                product_uom3 = sol.product_id.uom_id.id

                cr.execute('''SELECT sum(AA.product_qty) as product_qty, aa.location_id FROM
                    (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
                    CASE when pt.uom_id = m.product_uom
                    THEN
                        coalesce(sum(-m.product_qty)::decimal, 0.0)
                    ELSE
                        coalesce(sum(-m.product_qty * pu.factor)::decimal, 0.0) END as product_qty
                    FROM
                        stock_move m
                        LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                        LEFT JOIN product_product pp ON (m.product_id=pp.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                        LEFT JOIN product_uom u ON (m.product_uom=u.id)
                        LEFT JOIN stock_location l ON (m.location_id=l.id)
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
                        m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                    UNION ALL
                    SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
                    CASE when pt.uom_id = m.product_uom
                    THEN
                        coalesce(sum(m.product_qty)::decimal, 0.0)
                    ELSE
                        coalesce(sum(m.product_qty * pu.factor)::decimal, 0.0) END as product_qty
                    FROM
                        stock_move m
                        LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                        LEFT JOIN product_product pp ON (m.product_id=pp.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                        LEFT JOIN product_uom u ON (m.product_uom=u.id)
                        LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
                        m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                    ) AS AA
                        INNER JOIN stock_location sl on sl.id = AA.location_id
                        LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
                        LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
                        LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
                        LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
                        LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
                        LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
                        LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
                        WHERE sl.usage = 'internal' AND AA.state in ('assigned','done') AND AA.product_id = ''' + str(moves.product_id.id) + ''' and AA.location_id = ''' + str(moves.location_id.id)
                        + '''GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                        HAVING sum(aa.product_qty) > 0''')

                for product_qty, loc in cr.fetchall():
                    qty_location = product_qty
#        raise osv.except_osv(_('Debug !'), _(' xxxxxxxxx '))
#        qty_location = 0.00
            qty_location = qty_location + product_uom_obj._compute_qty(cr, uid, moves.product_uom.id, moves.product_qty, moves.product_id.uom_id.id)
#        raise osv.except_osv(_('Debug !'), _(str(move_id)))
        if 'stock_move_id' in fields:
            res.update({'stock_move_id': move_id})
        if 'qty_onhand_count' in fields:
            res.update({'qty_onhand_count': qty_onhand_count})
        if 'product_uom3' in fields:
            res.update({'product_uom3': product_uom3})

        if 'location_id' in fields:
            res.update({'location_id': moves.location_id.id})
        if 'qty_location' in fields:
            res.update({'qty_location': qty_location})
        if 'location_uom' in fields:
            res.update({'location_uom': moves.product_id.uom_id.id})

        if 'type' in fields:
            res.update({'type': moves.picking_id.type})
        if 'product_id' in fields:
            res.update({'product_id': moves.product_id.id})
        if 'product_uom_qty' in fields:
            res.update({'product_uom_qty': product_uom_qty})
        if 'product_uom' in fields:
            res.update({'product_uom': product_uom})
        if 'product_uom_qty2' in fields:
            res.update({'product_uom_qty2': product_uom_qty2})
        if 'product_uom22' in fields:
            res.update({'product_uom22': product_uom22})
        if 'qty_delivery' in fields:
            res.update({'qty_delivery': qty_delivery})
        if 'product_uom2' in fields:
            res.update({'product_uom2': product_uom2})
        if 'qty_reinput' in fields:
            res.update({'qty_reinput': moves.product_qty})
        if 'uom_id' in fields:
            res.update({'uom_id': moves.product_uom.id})
        if 'spq' in fields:
            res.update({'spq': spq})
        return res

    def onchange_qty_reinput(self, cr, uid, ids, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_reinput, uom_id, product_uom_qty2, product_uom_id2, type, qty_onhand_count, product_uom3,
             qty_location, spq, context=None):
        res= {}
#        raise osv.except_osv(_('Debug !'), _(' xxxxxxxxx '))
        product_uom_obj = self.pool.get('product.uom')
        product_product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        product_uom = product_uom_obj.browse(cr, uid, product_uom2, context=context)
        res['value'] = {'qty_reinput': qty_reinput or 1.00, 'uom_id' : uom_id or False}
        if not uom_id:
            return res
        qty_delivery = product_uom_obj._compute_qty(cr, uid, product_uom2, qty_delivery, product_product.uom_id.id)
        qty_reinput = product_uom_obj._compute_qty(cr, uid, uom_id, qty_reinput, product_product.uom_id.id)
        if type == 'out':
            res['value'].update({'qty_location': qty_location or 0.00})
            qty_sale = product_uom_obj._compute_qty(cr, uid, product_uom_id2, product_uom_qty2, product_product.uom_id.id)
            qty_onhand_count = product_uom_obj._compute_qty(cr, uid, product_uom3, qty_onhand_count, product_product.uom_id.id)
            if qty_reinput > 1.00:
                if qty_reinput > qty_onhand_count - qty_delivery:
                    res['warning'] = {'title': _('Warning'), 'message': _('The Qty entered cannot more than ' + str(qty_onhand_count - qty_delivery) + ' ' + product_uom.name + ',because the qty onhand is not enough.')}
                    res['value'].update({'qty_reinput': 1.00})
                else:
                    if qty_reinput > qty_location:
                        res['warning'] = {'title': _('Warning'), 'message': _('The Qty entered cannot more than ' + str(qty_location) + ' ' + product_uom.name +',because the qty location is not enough.')}
                        res['value'].update({'qty_reinput': 1.00})
                    else:
                        if qty_reinput > qty_sale - qty_delivery:
                            res['warning'] = {'title': _('Warning'), 'message': _('The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name + ',because the qty entered is more than qty can order.')}
                            res['value'].update({'qty_reinput': 1.00})
            else:
                res['value'].update({'qty_reinput': 1.00})


        if type == 'in':
            qty_purchase = product_uom_obj._compute_qty(cr, uid, product_uom_id, product_uom_qty, product_product.uom_id.id)
            if qty_reinput > 0:
                if qty_reinput%spq != 0:
                    qty_reinput = 0
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'the input quantity is not in spq multiplication \n (spq = ' + str(spq) + ')'
                                   }
                        res['warning'] = warning

                if qty_reinput > qty_purchase - qty_delivery:
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n The Qty entered cannot more than ' + str(qty_purchase - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'The Qty entered cannot more than ' + str(qty_purchase - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'The Qty entered cannot more than ' + str(qty_purchase - qty_delivery) + ' ' + product_uom.name
                                   }
                        res['warning'] = warning

                    qty_reinput = 0
            else:
                 qty_reinput = 0
            res['value'].update({'qty_reinput': qty_reinput})
        return res

    def onchange_location_id(self, cr, uid, ids, move_id, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_reinput, uom_id, product_uom_qty2, product_uom_id2, type, qty_onhand_count, product_uom3,
             location_id, spq, context=None):
        qty_location = 0.00
        if type == 'out':
            if not product_id:
                return {}
            res= {}
            stock_move_obj = self.pool.get('stock.move')
            product_uom_obj = self.pool.get('product.uom')
            location_ids = []
            location_qty = {}
            cr.execute('''SELECT sum(AA.product_qty) as product_qty, aa.location_id FROM
                (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
                m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
                CASE when pt.uom_id = m.product_uom
                THEN
                    coalesce(sum(-m.product_qty)::decimal, 0.0)
                ELSE
                    coalesce(sum(-m.product_qty * pu.factor)::decimal, 0.0) END as product_qty
                FROM
                    stock_move m
                    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                    LEFT JOIN product_product pp ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                    LEFT JOIN product_uom u ON (m.product_uom=u.id)
                    LEFT JOIN stock_location l ON (m.location_id=l.id)
                GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                UNION ALL
                SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
                m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
                CASE when pt.uom_id = m.product_uom
                THEN
                    coalesce(sum(m.product_qty)::decimal, 0.0)
                ELSE
                    coalesce(sum(m.product_qty * pu.factor)::decimal, 0.0) END as product_qty
                FROM
                    stock_move m
                    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                    LEFT JOIN product_product pp ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                    LEFT JOIN product_uom u ON (m.product_uom=u.id)
                    LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                ) AS AA
                    INNER JOIN stock_location sl on sl.id = AA.location_id
                    LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
                    LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
                    LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
                    LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
                    LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
                    LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
                    LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
                    WHERE sl.usage = 'internal' AND AA.state in ('assigned','done') AND AA.product_id = ''' + str(product_id)
                    + '''GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                    HAVING sum(aa.product_qty) > 0''')
            for product_qty, location_id2 in cr.fetchall():
                location_ids.append(location_id2)
                location_qty[location_id2] = product_qty
            res = {'value': {'qty_location': qty_location}}
            res['domain'] = {'location_id': [('id','in',location_ids)]}
            if not location_id:
                return res
    
            if location_id not in location_ids:
                res['value'].update({'location_id': False})
                res['warning'] = {'title': _('Warning'), 'message': _('The selected Location is not belong to this product or the qty of the location equal to zero!')}
                return res
    
            qty_location = location_qty[location_id]
    
            if move_id:
                moves = stock_move_obj.browse(cr, uid, move_id, context=context)
                qty_location = qty_location + product_uom_obj._compute_qty(cr, uid, moves.product_uom.id, moves.product_qty, moves.product_id.uom_id.id)

        return self.onchange_qty_reinput(cr, uid, ids, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_reinput, uom_id, product_uom_qty2, product_uom_id2, type, qty_onhand_count, product_uom3,
            qty_location, spq, context=context)

    def edit_quantity(self, cr, uid, ids, context=None):
        stock_move_obj = self.pool.get('stock.move')

        for obj in self.browse(cr, uid, ids, context=context):
            if obj.qty_reinput == 0:
                raise osv.except_osv(
                _('Error !'),
                _('Zero Value Cannot Process.'))
            for moves in stock_move_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
                stock_move_obj.write(cr, uid, moves.id,
                    {'product_qty': obj.qty_reinput}, context=context)

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'stock_move_id': fields.many2one('stock.move', 'Stock Move', ondelete='cascade',),
        'product_uom_qty2': fields.float('Qty (Sale Order)', readonly=True),
        'product_uom22': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True,),
        'product_uom_qty': fields.float('Qty (Purchase Order)', readonly=True),
        'product_uom': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_delivery': fields.float('has generate Qty', readonly=True),
        'product_uom2': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_reinput': fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'), select=True,),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'location_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', required=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'qty_location': fields.float('Location Qty', readonly=True),
        'location_uom': fields.many2one('product.uom', 'UoM', readonly=True),
        'qty_onhand_count' : fields.float("On Hand Allocated Qty", readonly=True),
        'product_uom3': fields.many2one('product.uom', 'UoM', readonly=True),
    }

change_warehouse_qty()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
