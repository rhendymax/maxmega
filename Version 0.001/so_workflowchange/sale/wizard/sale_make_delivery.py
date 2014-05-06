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

class sale_make_delivery(osv.osv_memory):
    _name = "sale.make.delivery"
    _description = "Sales Make Deliveries"
    _columns = {
        'delivery_date': fields.date('Prepared Date'),
        'do_date': fields.date('DO Date'),
        'delivery_lines_ids' : fields.one2many('delivery.lines', 'wizard_id2', 'Delivery Lines'),
        'desc': fields.text('Description'),
        'country_org_id': fields.many2one('res.country', 'Country of Origin'),
        'country_des_id': fields.many2one('res.country', 'Country of Destination'),
    }

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        order = self.pool.get('sale.order').browse(cr, uid, record_id, context=context)
        if order.state == 'draft':
            raise osv.except_osv(_('Warning !'),'You can not create deliveries when sales order is not confirmed.')
        return False

    def default_get(self, cr, uid, fields, context=None):
        sale_order_obj = self.pool.get('sale.order')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        result1 = []

        if context is None:
            context = {}
        res = super(sale_make_delivery, self).default_get(cr, uid, fields, context=context)

        for order in sale_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            for lines in order.order_line:
                location_id = False
                qty_delivery = 0.00
                move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',lines.id),('state','!=','cancel')])
                if move_ids:
                    for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                        qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
                qty_sales = product_uom_obj._compute_qty(cr, uid, lines.product_uom.id, lines.product_uom_qty, lines.product_id.uom_id.id)

                qty_order = qty_sales - qty_delivery
                qty_onhand_count = lines.qty_onhand_count
                if qty_order > qty_onhand_count - qty_delivery:
                    qty_order = qty_onhand_count - qty_delivery


                qty_unit_sale = qty_sales / lines.product_uom_qty
                qty_order = math.floor(qty_order / qty_unit_sale)
#                raise osv.except_osv(_('Debug'), _('Product is' + str(qty_location) + '----'))
                delivery_lines_vals = {
                    'order_id' : order.id,
                    'uom_id' : lines.product_uom.id,
                    'product_uom3' : lines.product_id.uom_id.id,
                    'product_uom2' : lines.product_id.uom_id.id,
                    'product_uom' : lines.product_uom.id,
                    'qty_delivery' : qty_delivery,
                    'product_uom_qty' : lines.product_uom_qty,
                    'product_id' : lines.product_id.id,
                    'qty_onhand_count' : lines.qty_onhand_count,
                    'order_line_id' : lines.id,
                    'spq' : lines.product_id.spq,
                    'qty_order' : qty_order,
                    'location_id' : lines.location_id.id,
                    }
                result1.append(delivery_lines_vals)
        if 'delivery_lines_ids' in fields:
            res.update({'delivery_lines_ids': result1})

        return res

    def _prepare_stock_move(self, cr, uid, moves, picking_id, context=None):
        res_partner_obj = self.pool.get('res.partner')
        account_tax_obj = self.pool.get('account.tax')
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        taxes = account_tax_obj.browse(cr, uid, map(lambda x: x.id, moves.order_line_id.tax_id))
        fpos = moves.order_id.fiscal_position or False
        taxes_ids = fiscal_position_obj.map_tax(cr, uid, fpos, taxes)
        addr = moves.order_id.partner_id and res_partner_obj.address_get(cr, uid, [moves.order_id.partner_id.id], ['delivery', 'invoice', 'contact'])

        move_vals = {
             'name': moves.order_id.name + ': ' + (moves.order_line_id.name or ''),
             'picking_id': picking_id,
             'product_id': moves.order_line_id.product_id.id,
             'product_qty': moves.qty_order,
             'product_uom': moves.order_line_id.product_uom.id,
             'product_uos': moves.order_line_id.product_uom.id,
             'date': moves.order_line_id.customer_original_date or time.strftime('%Y-%m-%d'),
             'date_expected': moves.order_line_id.customer_original_date or time.strftime('%Y-%m-%d'),
             'location_id': moves.location_id.id,
             'location_dest_id': moves.order_id.partner_id.property_stock_customer.id,
             'address_id': addr and addr['delivery'] or False,
             'state': 'assigned',
             'sale_line_id': moves.order_line_id.id,
             'company_id': (moves.order_id.company_id and moves.order_id.company_id.id) or False,
             'price_unit': moves.order_line_id.price_unit,
             'price_currency_id': moves.order_id.pricelist_id.currency_id.id,
             'taxes_id': [(6,0,taxes_ids)],
             'note': moves.order_line_id.notes,
             }
        return move_vals

    def _prepare_picking(self, cr, uid, generated, so_vals, context=None):
        res_partner_obj = self.pool.get('res.partner')
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        if so_vals.order_policy == 'picking':
            invoice_state = '2binvoiced'
        else:
            invoice_state = 'none'
        addr = so_vals.partner_id and res_partner_obj.address_get(cr, uid, [so_vals.partner_id.id], ['delivery', 'invoice', 'contact'])
        partner_val = so_vals.partner_id or False

        picking_vals = {
                        'name': sequence,
                        'date': generated.delivery_date or time.strftime('%Y-%m-%d'),
                        'do_date': generated.do_date or time.strftime('%Y-%m-%d'),
                        'type': 'out',
                        'state': 'draft',
                        'invoice_state': invoice_state,
                        'company_id': (so_vals.company_id and so_vals.company_id.id) or False,
                        'pricelist_id': (so_vals.pricelist_id and so_vals.pricelist_id.id) or False,
                        'partner_order_id' : addr and addr['contact'] or False,
                        'partner_shipping_id' : addr and addr['delivery'] or False,
                        'partner_invoice_id' : addr and addr['invoice'] or False,
                        'partner_id': (so_vals.partner_id and so_vals.partner_id.id) or False,
                        'ship_method_id' : (partner_val and partner_val.ship_method_id and partner_val.ship_method_id.id) or False,
                        'fob_id' : (partner_val and partner_val.fob_id and partner_val.fob_id.id) or False,
                        'sales_zone_id' : (partner_val and partner_val.sales_zone_id and partner_val.sales_zone_id.id) or False,
                        'sale_term_id' : (partner_val and partner_val.sale_term_id and partner_val.sale_term_id.id) or False,
                        'fiscal_position' : (so_vals.fiscal_position and so_vals.fiscal_position.id) or False,
                        'country_org_id' : generated.country_org_id.id,
                        'country_des_id' : generated.country_des_id.id,
                        'note' : generated.desc,
                        'user_id': so_vals.user_id.id,
                        }
        return picking_vals


    def generated_do(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        assert len(ids) == 1
        picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        picking_group = {}
        newinv = []
        generated = self.browse(cr, uid, ids[0], context=context)
        move_ids = generated.delivery_lines_ids
        if move_ids:
            for moves in move_ids:
                if moves.qty_order < 1:
                    continue
                so_vals = moves.order_id
                if (str(so_vals.partner_id.id) + '--' + str(so_vals.pricelist_id.id) + '--' + str((so_vals.fiscal_position and so_vals.fiscal_position.id) or False) + '--' + str((so_vals.sales_zone_id and so_vals.sales_zone_id.id) or False)+ '--' + str((so_vals.user_id and so_vals.user_id.id) or False)) in picking_group:
                    picking_id = picking_group[(str(so_vals.partner_id.id) + '--' + str(so_vals.pricelist_id.id) + '--' + str((so_vals.fiscal_position and so_vals.fiscal_position.id) or False) + '--' + str((so_vals.sales_zone_id and so_vals.sales_zone_id.id) or False)+ '--' + str((so_vals.user_id and so_vals.user_id.id) or False))]
                else:
                    picking_vals = self._prepare_picking(cr, uid, generated, so_vals, context=context)
                    picking_id = picking_obj.create(cr, uid, picking_vals, context=context)
                    newinv.append(picking_id)
                    cr.execute('insert into sale_order_picking_rel (order_id,picking_id) values (%s,%s)', (moves.order_id.id, picking_id))
                    picking_group[(str(so_vals.partner_id.id) + '--' + str(so_vals.pricelist_id.id) + '--' + str((so_vals.fiscal_position and so_vals.fiscal_position.id) or False) + '--' + str((so_vals.sales_zone_id and so_vals.sales_zone_id.id) or False)+ '--' + str((so_vals.user_id and so_vals.user_id.id) or False))] = picking_id
                if moves.order_line_id.state == 'cancel':
                    continue

                vals = self._prepare_stock_move(cr, uid, moves, picking_id, context=context)
                if vals:
                    stock_move_id = stock_move_obj.create(cr, uid, vals, context=context)

        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', ["+','.join(map(str,newinv))+"])]"
        result['context'] = "{'search_default_available':0}"

        return result

sale_make_delivery()

class delivery_lines(osv.osv_memory):
    _name = 'delivery.lines'
    _description = 'Delivery Lines'

    def onchange_qty_order(self, cr, uid, ids, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_onhand_count, product_uom3, qty_order, uom_id, spq, order_id, context=None):
        res= {}
        if not product_id:
            return {}
        product_uom_obj = self.pool.get('product.uom')
        product_product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        spq_approve = False
        if order_id:
            spq_approve = self.pool.get('sale.order').browse(cr, uid, order_id, context=context).spq_approve

        product_uom = product_uom_obj.browse(cr, uid, product_uom2, context=context)
        res['value'] = {'qty_order': qty_order or 0.0, 'uom_id' : uom_id or False,}
        res['domain'] = {'uom_id': [('category_id','=',product_product.uom_id.category_id.id)]}
        if not uom_id:
            return res
        qty_sale = product_uom_obj._compute_qty(cr, uid, product_uom_id, product_uom_qty, product_product.uom_id.id)
        qty_delivery = product_uom_obj._compute_qty(cr, uid, product_uom2, qty_delivery, product_product.uom_id.id)
        qty_onhand_count = product_uom_obj._compute_qty(cr, uid, product_uom3, qty_onhand_count, product_product.uom_id.id)
        qty_order = product_uom_obj._compute_qty(cr, uid, uom_id, qty_order, product_product.uom_id.id)
        if qty_order > 0:
            if spq_approve == False and qty_order%spq != 0:
                qty_order= spq * ((qty_order-(qty_order%spq))/spq)
                res['value'].update({'qty_order': qty_order})
            if qty_order > qty_onhand_count - qty_delivery:
                res['warning'] = {'title': _('Warning'), 'message': _('The Qty entered cannot more than ' + str(qty_onhand_count - qty_delivery) + ' ' + product_uom.name + ',because the qty onhand is not enough.')}
                res['value'].update({'qty_order': 0.00})
            else:
                if qty_order > qty_sale - qty_delivery:
                    res['warning'] = {'title': _('Warning'), 'message': _('The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name + ',because the qty entered is more than qty can order.')}
                    res['value'].update({'qty_order': 0.00})
        else:
            res['value'].update({'qty_order': 0.00})
        return res

    _columns = {
        'wizard_id2': fields.many2one('sale.make.delivery', 'Generated Delivery', ondelete='cascade',),
        'order_id' : fields.many2one('sale.order', 'Order', ondelete='cascade', required=True, readonly=True,),
        'order_line_id' : fields.many2one('sale.order.line', 'Order Line', ondelete='cascade', required=True,),
        'product_id': fields.many2one('product.product', 'Supplier Part No', readonly=True,),
        'product_uom_qty': fields.float('Qty (Sales Order)', readonly=True),
        'product_uom': fields.many2one('product.uom', 'UoM', readonly=True),
        'qty_delivery': fields.float('has generate Qty', readonly=True),
        'product_uom2': fields.many2one('product.uom', 'UoM', readonly=True),
        'qty_onhand_count' : fields.float("On Hand Allocated Qty", readonly=True),
        'product_uom3': fields.many2one('product.uom', 'UoM', readonly=True),
        'qty_order': fields.float('Qty (Delivery Order)',),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True),
        'location_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', readonly=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
    }

delivery_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
