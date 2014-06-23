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
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp
import netsvc

class sale_order(osv.osv):
    _inherit = "sale.order"
    _description = "Sales Order"

    def _shipped_rate2(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        res2 = {}
        picking_ids = []
        stock_move_obj = self.pool.get('stock.move')

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = [0.0,0.0]
            sale_id = obj.id
            for line in obj.order_line:
                res[sale_id][1] += line.product_uom_qty or 0.0
                cr.execute('Select coalesce(sum(product_qty)::decimal, 0.0) as total from stock_move where sale_line_id=%s', (line.id,))
                res[sale_id][0] += cr.fetchone()[0]
#            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(line.id, total))
            if res[obj.id][0] == 0:
                res2[obj.id] = 0.0
            else:
                res2[obj.id] = 100.0 * res[obj.id][0] / res[obj.id][1]
        return res2

    def create(self, cr, user, vals, context=None):
#        raise osv.except_osv(_('Debug!'), _(' \'%s\' \'%s\'!') %(vals, ''))
        if 'partner_shipping_id' in vals:
            shipping_addr = self.pool.get('res.partner.address').browse(cr, user, vals['partner_shipping_id'], context=None)
            partner_id2 = vals['partner_id2'] or False
            if ((shipping_addr.partner_id and shipping_addr.partner_id.id) or False) != partner_id2:
                raise osv.except_osv(_('Invalid action !'), _('Cannot process because the Shipping Address Selected is not matches with the Customer!'))
        if 'order_line' in vals:
            product_customer_name = ''
            qty_name = ''
            price_name = ''
            for lines in vals['order_line']:
                product_customer_id = lines[2]['product_customer_id'] or False
                if product_customer_id:
                    product_customer = self.pool.get('product.customer').browse(cr, user, product_customer_id, context=None)
                    customer_partner_id = product_customer.partner_id
                    if lines[2]['product_uom_qty'] == 0:
                        qty_name += (str(product_customer.name) + ' \n')
                    if lines[2]['price_unit'] == 0:
                        price_name += (str(product_customer.name) + ' \n')
                    if customer_partner_id.id != vals['partner_id2']:
                        product_customer_name += (str(product_customer.name) + ' (' + str(customer_partner_id.name) + ')\n')
            if product_customer_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Following Customer Part No is not matches with the Customer: \n' + product_customer_name))
            if qty_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Qty of The Following Customer Part No is Zero: \n' + qty_name))
            if price_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Price Unit of The Following Customer Part No is Zero: \n' + price_name))

        if 'partner_id2' in vals:
            partner_id22 = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, user, partner_id22, context=None)
            addr = self.pool.get('res.partner').address_get(cr, user, [vals['partner_id2']], ['delivery', 'invoice', 'contact'])
            if not partner.property_product_pricelist.currency_id.so_sequence_id.id:
                raise osv.except_osv(_('Invalid action !'), _('not so sequence defined in currency ' + str(partner.property_product_pricelist.currency_id.name)))
            obj_sequence = self.pool.get('ir.sequence')
            seq_id = partner.property_product_pricelist.currency_id.so_sequence_id.id
            new_name = obj_sequence.next_by_id(cr, user, seq_id, None)
            vals.update({
                         'name' : new_name,
                         })
            vals.update({'partner_invoice_id': addr['invoice'],
                         'partner_order_id': addr['contact'],
                         'user_id': (partner.user_id and partner.user_id.id) or False,
                         'pricelist_id': (partner.property_product_pricelist and partner.property_product_pricelist.id) or False,
                         'fiscal_position' : (partner.property_account_position and partner.property_account_position.id) or False,
                         'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
                         'fob_id' : (partner.fob_id and partner.fob_id.id) or False,
                         'sales_zone_id' : (partner.sales_zone_id and partner.sales_zone_id.id) or False,
                         'sale_term_id' : (partner.sale_term_id and partner.sale_term_id.id) or False,
                         })
        new_id = super(sale_order, self).create(cr, user, vals, context)

        return new_id

    def write(self, cr, uid, ids, vals, context=None):
#        raise osv.except_osv(_('Debug'), _(str(vals) + ' ' + str(ids)))

        so_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        partner_id2 = ('partner_id2' in vals and vals['partner_id2']) or (self.pool.get('sale.order').browse(cr, uid, so_id, context=None).partner_id.id) or False
        if 'partner_shipping_id' in vals:
            shipping_addr = self.pool.get('res.partner.address').browse(cr, uid, vals['partner_shipping_id'], context=None)
            if (shipping_addr.partner_id and shipping_addr.partner_id.id or False) != partner_id2:
                raise osv.except_osv(_('Invalid action !'), _('Cannot process because the Shipping Address Selected is not matches with the Customer!'))
        if 'order_line' in vals:
            product_customer_name = ''
            qty_name = ''
            price_name = ''
            for lines in vals['order_line']:
                if lines[0] == 0:
                    product_customer_id = ('product_customer_id' in lines[2] and lines[2]['product_customer_id']) or False
                    if product_customer_id:
                        product_customer = self.pool.get('product.customer').browse(cr, uid, product_customer_id, context=None)
                        customer_partner_id = product_customer.partner_id
                        if lines[2]['product_uom_qty'] == 0:
                            qty_name += (str(product_customer.name) + ' \n')
                        if lines[2]['price_unit'] == 0:
                            price_name += (str(product_customer.name) + ' \n')
                        if customer_partner_id.id != partner_id2:
                            product_customer_name += (str(product_customer.name) + ' (' + str(customer_partner_id.name) + ')\n')

                if lines[0] == 1:
                    product_customer_id2 =  ('product_customer_id' in lines[2] and lines[2]['product_customer_id']) or self.pool.get('sale.order.line').browse(cr, uid, lines[1], context=None).product_customer_id.id  or False
                    if product_customer_id2:
                        product_customer2 = self.pool.get('product.customer').browse(cr, uid, product_customer_id2, context=None)
                        customer_partner_id2 = product_customer2.partner_id
                        if 'product_uom_qty' in lines[2]:
                            product_uom_qty = lines[2]['product_uom_qty']
                        else:
                            product_uom_qty = -1
                        if product_uom_qty == 0:
                            qty_name += (str(product_customer2.name) + ' \n')

                        if 'price_unit' in lines[2]:
                            price_unit = lines[2]['price_unit']
                        else:
                            price_unit = -1
                        if price_unit == 0:
                            price_name += (str(product_customer2.name) + ' \n')

                        if customer_partner_id2.id != partner_id2:
                            product_customer_name += (str(product_customer2.name) + ' (' + str(customer_partner_id2.name) + ')\n')
            if product_customer_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Following Customer Part No is not matches with the Customer: \n' + product_customer_name))
            if qty_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Qty of The Following Customer Part No is Zero: \n' + qty_name))
            if price_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Price Unit of The Following Customer Part No is Zero: \n' + price_name))
        if 'partner_id2' in vals:
            partner_id22 = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id22, context=None)
            addr = self.pool.get('res.partner').address_get(cr, uid, [vals['partner_id2']], ['delivery', 'invoice', 'contact'])
            vals.update({'partner_invoice_id': addr['invoice'],
                         'partner_order_id': addr['contact'],
                         'user_id': (partner.user_id and partner.user_id.id) or False,
                         'pricelist_id': (partner.property_product_pricelist and partner.property_product_pricelist.id) or False,
                         'fiscal_position' : (partner.property_account_position and partner.property_account_position.id) or False,
                         'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
                         'fob_id' : (partner.fob_id and partner.fob_id.id) or False,
                         'sales_zone_id' : (partner.sales_zone_id and partner.sales_zone_id.id) or False,
                         'sale_term_id' : (partner.sale_term_id and partner.sale_term_id.id) or False,
                         })
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def onchange_pricelist_id2(self, cr, uid, ids, partner_id):
        if partner_id:
            pricelist_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context=None).property_product_pricelist.id
            return {'value':{'pricelist_id': pricelist_id}}
        return {'value':{'pricelist_id': False}}

    def onchange_partner_id(self, cr, uid, ids, part, part2, order_line):
        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, part2, order_line)
        if part:
            partner_id = self.pool.get('res.partner').browse(cr, uid, part, context=None)
            result['value']['ship_method_id'] = (partner_id.ship_method_id and partner_id.ship_method_id.id) or False
            result['value']['sales_zone_id'] = (partner_id.sales_zone_id and partner_id.sales_zone_id.id) or False
            result['value']['fob_id'] = (partner_id.fob_id and partner_id.fob_id.id) or False
            result['value']['sale_term_id'] = (partner_id.sale_term_id and partner_id.sale_term_id.id) or False
            result['value']['user_id'] = (partner_id.user_id and partner_id.user_id.id) or False

        return result

    def act_approve_spq(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'spq_approve': True, 'spq_approve_user': uid, 'spq_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        return True

    def act_undo_approve_spq(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'spq_approve': False, 'spq_approve_user': False, 'spq_date':False})
        return True

    _columns = {
        'spq_approve': fields.boolean('approved SPQ', invisible=True),
        'spq_approve_user':fields.many2one('res.users', 'SPQ Approved By'),
        'spq_date': fields.datetime('SPQ Approved Date'),
        'header_so': fields.text('Header'),
        'footer_so': fields.text('Footer'),
        'name': fields.char('Order Reference', size=64,
            select=True),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', required=True, readonly=True, help="Pricelist for current sales order."),
        'user_id': fields.many2one('res.users', 'Salesman', select=True, readonly=True,),
        'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', readonly=True, required=True, help="Invoice address for current sales order."),
        'partner_order_id': fields.many2one('res.partner.address', 'Ordering Contact', readonly=True, required=True, help="The name and address of the contact who requested the order or quotation."),
        'ship_method_id': fields.many2one('shipping.method','Ship Method', readonly=True),
        'fob_id': fields.many2one('fob.point.key', 'FOB Point Key', select=True, readonly=True,),
        'sales_zone_id': fields.many2one('res.partner.sales.zone','Sales Zone',readonly=True),
        'sale_term_id': fields.many2one('sale.payment.term', 'Sale Payment Term', select=True, readonly=True,),
        'client_order_ref': fields.char('Customer PO', size=64, required=True),
        'picking_ids2': fields.many2many('stock.picking', 'sale_order_picking_rel', 'order_id', 'picking_id', 'Related Picking', readonly=True, help="This is the list of deliveries that have been generated for this sale order. The same sale order may have been invoiced in several times (by line for example)."),
        'picked_rate': fields.function(_shipped_rate2, string='Picked', type='float'),
    }

    def _check_name_partner(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            duplicate_ids = self.search(cr, uid, [('partner_id','=',record.partner_id.id),
                  ('client_order_ref','=',record.client_order_ref),
                  ('id','!=',record.id)])
            if duplicate_ids:
                return False
        return True

    _constraints = [
        (_check_name_partner,
            'Duplicate Sale Order that have same Customer or Customer PO',
            ['partner_id','client_order_ref']),
    ]

#    def copy(self, cr, uid, id, default=None, context=None):
#        if not default:
#            default = {}
#        sale_order_obj = self.pool.get('sale.order')
#        obj_sequence = self.pool.get('ir.sequence')
#        sale_order_id = sale_order_obj.browse(cr, uid, id, context=None)
#        seq_id = sale_order_id.pricelist_id.currency_id.so_sequence_id.id
#        default.update({
#            'origin':'',
#            'picking_ids2':[],
#            'client_order_ref': sale_order_id.client_order_ref + '-2',
#            })
#
#        return super(sale_order, self).copy(cr, uid, id, default, context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        raise osv.except_osv(_('Error!'), _('cannot duplicate sale order'))
        return super(sale_order, self).copy(cr, uid, id, default, context)

    _defaults = {
        'order_policy': 'picking',
        'name': '',
    }

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_allocated_obj = self.pool.get("sale.allocated")
        for rec in self.browse(cr, uid, ids, context=context):
            productname = ''
            for line in rec.order_line:
                if line.qty_onhand_count > 0:
                    productname = line.name + ", "
                else:
                    sale_order_line_id = line.id
                    sale_allocated_ids = sale_allocated_obj.browse(cr, uid,
                        sale_allocated_obj.search(cr, uid, [('sale_line_id', '=', sale_order_line_id)]),
                        context=context)
                    if sale_allocated_ids:
                        productname = line.name + ", "
            if productname != '':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sale order line which is being allocated \'%s\'!') %(productname,))
        return super(sale_order, self).unlink(cr, uid, ids, context=context)

    def button_dummy2(self, cr, uid, ids, context=None):
        return True

    def button_check_done(self, cr, uid, ids, context=None):
#        for rec in self.browse(cr, uid, self.pool.get('sale.order').search(cr, uid, [('state', '=', 'progress')], context=None), context=None):
#            if rec.picked_rate == 100:
#                self.write(cr, uid, [rec.id], {'state': 'done'})
#                for lines in rec.order_line:
#                    self.pool.get('sale.order.line').write(cr, uid, [lines.id], {'state': 'done'})
##            raise osv.except_osv(_('XXNo Unit Cost Price!'), _('cannot find unit cost at supplier code ' +str(rec.picked_rate)))
        fifo_control_obj = self.pool.get('fifo.control')
        move_allocated_control_obj = self.pool.get('move.allocated.control')
        internal_move_control_obj = self.pool.get('internal.move.control')
#product name = '0251.500NRT1LI'
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':3462,
#            'quantity': 30000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2158,
#            'out_move_id':3462,
#            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2158,
#            'out_move_id':3692,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2185,
#            'out_move_id':3692,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2185,
#            'out_move_id':5524,
#            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':5525,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':5631,
#            'quantity': 25000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':7999,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':9706,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':1868,
#            'out_move_id':10259,
#            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7736,
#            'out_move_id':12090,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2968,
#            'out_move_id':12091,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':13018,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#             'out_move_id':13847,
#             'quantity': 20000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':14783,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':15702,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':17234,
#            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':2385,
#            'out_move_id':2751,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':17235,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':17554,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':18408,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':18932,
#            'quantity': 10000},context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 7887,
#                                                    'so_line_id': 12,
#                                                    'quantity': 45000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 7888,
#                                                    'so_line_id': 12,
#                                                    'quantity': 15000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 8321,
#                                                    'so_line_id': 12,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':10260,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':10172,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7887,
#            'out_move_id':11061,
#            'quantity': 15000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7888,
#            'out_move_id':11161,
#            'quantity': 10000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':7888,
#            'out_move_id':11992,
#            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {'in_move_id':8321,
#            'out_move_id':11992,
#            'quantity': 5000},context=context)
#
#delete from move_allocated_control where id = 3125
#delete from fifo_control where id = 4247
#update move_allocated_control set quantity = 3000 where id = 3126
##update fifo_control set quantity = 3000 where id = 4248
#
#
##so_line_id = 4911
##out_move_id = 7568
##internal_move_id = 3974 in_move_id/move_id
##pi_move_id = 1877 int_in_move_id/int_move_id
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1877,
#                                                    'move_id': 3974,
#                                                    'so_line_id': 4911,
#                                                    'quantity': 500,
#                                                    }, context=context)
##        
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 1877,
#                                          'in_move_id':3974,
#                                            'out_move_id':7568,
#                                            'quantity': 500},context=context)

#        internal_move_control_obj.create(cr, uid, {
#            'internal_move_id': 3974,
#            'other_move_id': 1876,
#            'quantity': 500,
#            },
#            context=context)

#        fifo_control_obj.create(cr, uid, {  'in_move_id':14752,
#                                            'out_move_id':3840,
#                                            'quantity': 10000},context=context)
#        internal_move_control_obj.create(cr, uid, {
#            'internal_move_id': 3840,
#            'other_move_id': 14752,
#            'quantity': 10000,
#            },
#            context=context)

#fifo_control
#in_move_id = 15489
#out_move_id = 3840
#quantity = 5000
#in_move_id = 15489
#out_move_id = 9611
#quantity = 7500
#internal_move_control
#internal_move_id = 9611
#in_move_id = 15489
#quantity = 7500
#internal_move_id = 3840
#in_move_id = 15489
#quantity = 5000

#        fifo_control_obj.create(cr, uid, {  'in_move_id':15489,
#                                            'out_move_id':3840,
#                                            'quantity': 5000},context=context)
#
#        fifo_control_obj.create(cr, uid, {  'in_move_id':15489,
#                                            'out_move_id':9611,
#                                            'quantity': 7500},context=context)
#
#        internal_move_control_obj.create(cr, uid, {
#            'internal_move_id': 9611,
#            'other_move_id': 15489,
#            'quantity': 7500,
#            },
#            context=context)
#
#        internal_move_control_obj.create(cr, uid, {
#            'internal_move_id': 3840,
#            'other_move_id': 15489,
#            'quantity': 5000,
#            },
#            context=context)

#move_allocated_control
#so_line_id 3853
#move_id = 5867
#int_move_id = 2953
#quantity = 2500
#
#fifo_control
#out_move_id = 6279
#in_move_id 5867
#int_in_move_id = 2953
#quantity = 2500
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2953,
#                                                    'move_id': 5867,
#                                                    'so_line_id': 3853,
#                                                    'quantity': 2500,
#                                                    }, context=context)
##        
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2953,
#                                          'in_move_id':5867,
#                                            'out_move_id':6279,
#                                            'quantity': 2500},context=context)

#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2163,
#                                          'in_move_id':3716,
#                                            'out_move_id':8162,
#                                            'quantity': 4000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2163,
#                                          'in_move_id':3716,
#                                            'out_move_id':7058,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2163,
#                                          'in_move_id':3716,
#                                            'out_move_id':8137,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2163,
#                                          'in_move_id':3716,
#                                            'out_move_id':8138,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2163,
#                                          'in_move_id':3716,
#                                            'out_move_id':8139,
#                                            'quantity': 3000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3716,
#                                            'out_move_id':8139,
#                                            'quantity': 6000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3716,
#                                            'out_move_id':8140,
#                                            'quantity': 10000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3716,
#                                            'out_move_id':8141,
#                                            'quantity': 8000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8141,
#                                            'quantity': 2000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8142,
#                                            'quantity': 9000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8143,
#                                            'quantity': 10000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8151,
#                                            'quantity': 9000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8152,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8153,
#                                            'quantity': 2000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8154,
#                                            'quantity': 8000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8155,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':8156,
#                                            'quantity': 4000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3882,
#                                            'out_move_id':6720,
#                                            'quantity': 4000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3989,
#                                            'out_move_id':6720,
#                                            'quantity': 6000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3989,
#                                            'out_move_id':6721,
#                                            'quantity': 5000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3989,
#                                            'out_move_id':6730,
#                                            'quantity': 5000},context=context)
#
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3989,
#                                            'out_move_id':6731,
#                                            'quantity': 5000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2595,
#                                          'in_move_id':3989,
#                                            'out_move_id':7059,
#                                            'quantity': 5000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':3989,
#                                            'out_move_id':7060,
#                                            'quantity': 5000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':3989,
#                                            'out_move_id':7064,
#                                            'quantity': 10000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':3989,
#                                            'out_move_id':7081,
#                                            'quantity': 5000},context=context)
#
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':3989,
#                                            'out_move_id':7086,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':3989,
#                                            'out_move_id':7072,
#                                            'quantity': 3000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':4118,
#                                            'out_move_id':7072,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':4118,
#                                            'out_move_id':7073,
#                                            'quantity': 1000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 2783,
#                                          'in_move_id':4118,
#                                            'out_move_id':7087,
#                                            'quantity': 4000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 11827,
#                                          'in_move_id':16110,
#                                            'out_move_id':7087,
#                                            'quantity': 2000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 11829,
#                                          'in_move_id':16110,
#                                            'out_move_id':7087,
#                                            'quantity': 1000},context=context)
#
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 11829,
#                                          'in_move_id':16110,
#                                            'out_move_id':7078,
#                                            'quantity': 1000},context=context)
#
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 11829,
#                                          'in_move_id':16110,
#                                            'out_move_id':8161,
#                                            'quantity': 3000},context=context)
#
#        fifo_control_obj.create(cr, uid, {'int_in_move_id': 11829,
#                                          'in_move_id':16110,
#                                            'out_move_id':8162,
#                                            'quantity': 2000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2163,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4330,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2163,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4331,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2163,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4332,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2163,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4336,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4336,
#                                                    'quantity': 6000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4498,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3716,
#                                                    'so_line_id': 4499,
#                                                    'quantity': 8000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4499,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4504,
#                                                    'quantity': 9000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4507,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4512,
#                                                    'quantity': 9000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4513,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4684,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4685,
#                                                    'quantity': 8000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4694,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4695,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3882,
#                                                    'so_line_id': 4912,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4912,
#                                                    'quantity': 6000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4913,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4914,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4915,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2595,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4916,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4917,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4918,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4926,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4927,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 3989,
#                                                    'so_line_id': 4928,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 4118,
#                                                    'so_line_id': 4928,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 4118,
#                                                    'so_line_id': 4929,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2783,
#                                                    'move_id': 4118,
#                                                    'so_line_id': 4930,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 11827,
#                                                    'move_id': 16110,
#                                                    'so_line_id': 4930,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 11829,
#                                                    'move_id': 16110,
#                                                    'so_line_id': 4930,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 11829,
#                                                    'move_id': 16110,
#                                                    'so_line_id': 4931,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 11829,
#                                                    'move_id': 16110,
#                                                    'so_line_id': 4936,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 11829,
#                                                    'move_id': 16110,
#                                                    'so_line_id': 4937,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#1599 - 3500
#9916 - 3500
#5416
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 5416,
#                                                    'so_line_id': 1599,
#                                                    'quantity': 3500,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':5416,
#                                            'out_move_id':9916,
#                                            'quantity': 3500},context=context)
#8218;4089 4000.000
#8219;4090 4000.000
#7484;4420 4000.000
#7485;4421 8000.000
#7486;4422 4000.000
#in_move_id 3977 int_in_move_id 2417
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2417,
#                                                    'move_id': 3977,
#                                                    'so_line_id': 4089,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2417,
#                                                    'move_id': 3977,
#                                                    'so_line_id': 4090,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2417,
#                                                    'move_id': 3977,
#                                                    'so_line_id': 4420,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2417,
#                                                    'move_id': 3977,
#                                                    'so_line_id': 4421,
#                                                    'quantity': 8000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2417,
#                                                    'move_id': 3977,
#                                                    'so_line_id': 4422,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2417,
#                                          'in_move_id':3977,
#                                            'out_move_id':8218,
#                                            'quantity': 4000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2417,
#                                          'in_move_id':3977,
#                                            'out_move_id':8219,
#                                            'quantity': 4000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2417,
#                                          'in_move_id':3977,
#                                            'out_move_id':7484,
#                                            'quantity': 4000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2417,
#                                          'in_move_id':3977,
#                                            'out_move_id':7485,
#                                            'quantity': 8000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2417,
#                                          'in_move_id':3977,
#                                            'out_move_id':7486,
##                                            'quantity': 4000},context=context)
#13622 move 3945 - 2500
#13622 so 1337 - 5000

#
#1110;10829,9000.000
#4941 1500
#9217 4500
#9218 3000
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 4941,
#                                                    'so_line_id': 1110,
#                                                    'quantity': 1500,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':4941,
#                                            'out_move_id':10829,
#                                            'quantity': 1500},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 9217,
#                                                    'so_line_id': 1110,
#                                                    'quantity': 4500,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':9217,
#                                            'out_move_id':10829,
#                                            'quantity': 4500},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 9218,
#                                                    'so_line_id': 1110,
#                                                    'quantity': 3000,
#                                                    }, context=context)

#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':9218,
#                                            'out_move_id':10829,
#                                            'quantity': 3000},context=context)

#

#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4919,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':8144,
#                                            'quantity': 1800},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4922,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':8147,
#                                            'quantity': 1800},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4932,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':8157,
#                                            'quantity': 1800},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4688,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':6724,
#                                            'quantity': 1800},context=context)
#
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4509,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':7083,
#                                            'quantity': 1800},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3228,
#                                                    'move_id': 3988,
#                                                    'so_line_id': 4505,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3228,
#                                          'in_move_id':3988,
#                                            'out_move_id':7079,
#                                            'quantity': 1800},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 4146,
#                                                    'so_line_id': 3896,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':4146,
#                                            'out_move_id':6230,
#                                            'quantity': 3000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4729,
#                                                    'move_id': 5886,
#                                                    'so_line_id': 3980,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4729,
#                                          'in_move_id':5886,
#                                            'out_move_id':6523,
#                                            'quantity': 3000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4729,
#                                                    'move_id': 5886,
#                                                    'so_line_id': 3881,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4729,
#                                          'in_move_id':5886,
#                                            'out_move_id':6212,
#                                            'quantity': 3000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4729,
#                                                    'move_id': 5886,
#                                                    'so_line_id': 3979,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4729,
#                                          'in_move_id':5886,
#                                            'out_move_id':6522,
#                                            'quantity': 3000},context=context)

## 11-11-2013
##
###EMK212BJ106KG-T
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 15542,
#                                                    'so_line_id': 379,
#                                                    'quantity': 3000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':15542,
#                                            'out_move_id':3644,
#                                            'quantity': 3000
#                                            },context=context)
###complete
#
##IR7-22R0-J, T/R (RoHS Compliant,Pb Free)
###HK Location
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':11150,
#                                            'out_move_id':10000,
#                                            'quantity': 3500
#                                            },context=context)
####complete
##JABIL GZ location
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5860,
#                                                    'so_line_id': 3858,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5860,
#                                            'out_move_id':7382,
#                                            'quantity': 700},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5861,
#                                                    'so_line_id': 3864,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5861,
#                                                    'so_line_id': 3865,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5861,
#                                                    'so_line_id': 3866,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5861,
#                                                    'so_line_id': 3867,
#                                                    'quantity': 1400,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5861,
#                                            'out_move_id':7388,
#                                            'quantity': 700},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5861,
#                                            'out_move_id':7389,
#                                            'quantity': 700},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5861,
#                                            'out_move_id':7390,
#                                            'quantity': 700},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5861,
#                                            'out_move_id':7391,
#                                            'quantity': 1400},context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 1662,
#                                                    'move_id': 5862,
#                                                    'so_line_id': 3867,
#                                                    'quantity': 1400,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 1662,
#                                          'in_move_id':5862,
#                                            'out_move_id':7391,
#                                            'quantity': 1400},context=context)
##complete
#
##IR7-6R8-JI
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3481,
#                                                    'move_id': 5863,
#                                                    'so_line_id': 4479,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3481,
#                                                    'move_id': 5863,
#                                                    'so_line_id': 4811,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4816,
#                                                    'move_id': 8740,
#                                                    'so_line_id': 4820,
#                                                    'quantity': 700,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3481,
#                                                    'move_id': 5841,
#                                                    'so_line_id': 4826,
#                                                    'quantity': 2,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3481,
#                                          'in_move_id':5863,
#                                            'out_move_id':7109,
#                                            'quantity': 700},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3481,
#                                          'in_move_id':5863,
#                                            'out_move_id':8027,
#                                            'quantity': 700},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4816,
#                                          'in_move_id':8740,
#                                            'out_move_id':8036,
#                                            'quantity': 700},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3481,
#                                          'in_move_id':5841,
#                                            'out_move_id':8042,
#                                            'quantity': 2},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4817,
#                                                    'move_id': 8750,
#                                                    'so_line_id': 6268,
#                                                    'quantity': 700,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4817,
#                                          'in_move_id':8750,
#                                            'out_move_id':10662,
#                                            'quantity': 700},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4817,
#                                                    'move_id': 8750,
#                                                    'so_line_id': 6820,
#                                                    'quantity': 700,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4817,
#                                          'in_move_id':8750,
#                                            'out_move_id':12401,
#                                            'quantity': 700},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 4817,
#                                                    'move_id': 8750,
#                                                    'so_line_id': 6822,
#                                                    'quantity': 700,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 4817,
#                                          'in_move_id':8750,
#                                            'out_move_id':12403,
#                                            'quantity': 700},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 9124,
#                                                    'move_id': 17474,
#                                                    'so_line_id': 6822,
#                                                    'quantity': 700,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 9124,
#                                          'in_move_id':17474,
#                                            'out_move_id':12403,
#                                            'quantity': 700},context=context)
##
##JMK105BJ105KV-F
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 17299,
#                                                    'so_line_id': 1882,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':17299,
#                                            'out_move_id':3771,
#                                            'quantity': 10000},context=context)
##JMK316BJ107ML-T
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 16717,
#                                                    'so_line_id': 626,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':16717,
#                                            'out_move_id':4018,
#                                            'quantity': 2000},context=context)
#
##JR100
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 9339,
#                                                    'so_line_id': 5634,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':9339,
#                                            'out_move_id':16379,
#                                            'quantity': 4000},context=context)
#
##LMK212BJ106KD-T
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 14407,
#                                                    'so_line_id': 7064,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':14407,
#                                            'out_move_id':11724,
#                                            'quantity': 4000},context=context)
#
##LOB-3-R100-H-LF-LT
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 15645,
#                                                    'so_line_id': 2214,
#                                                    'quantity': 1250,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':15645,
#                                            'out_move_id':14552,
#                                            'quantity': 1250},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 18382,
#                                                    'so_line_id': 2214,
#                                                    'quantity': 2500,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':18382,
#                                            'out_move_id':14552,
#                                            'quantity': 2500},context=context)
#
##LRC-LR1206LF-01-R050-F
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 18287,
#                                                    'so_line_id': 2541,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':18287,
#                                            'out_move_id':3696,
#                                            'quantity': 4000},context=context)
#
##LRC-LR1206LF-01-R100-F
##special - case(cannot find problem)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':2069,
#                                            'out_move_id':10110,
#                                            'quantity': 4000},context=context)
#
##LRC-LR2010LF-01-R033-F
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':13604,
#                                            'out_move_id':4114,
#                                            'quantity': 2000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':14702,
#                                            'out_move_id':4114,
#                                            'quantity': 2000},context=context)
#
##LRC-LR2010LF-01-R200-F
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 2640,
#                                                    'so_line_id': 5126,
#                                                    'quantity': 20000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':2640,
#                                            'out_move_id':11881,
#                                            'quantity': 20000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 2640,
#                                                    'so_line_id': 5662,
#                                                    'quantity': 8000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':2640,
#                                            'out_move_id':11922,
#                                            'quantity': 8000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 2646,
#                                                    'so_line_id': 5662,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':2646,
#                                            'out_move_id':11922,
#                                            'quantity': 2000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 3076,
#                                                    'so_line_id': 5662,
#                                                    'quantity': 28000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':3076,
#                                            'out_move_id':11922,
#                                            'quantity': 28000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 3150,
#                                                    'so_line_id': 5662,
#                                                    'quantity': 58000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':3150,
#                                            'out_move_id':11922,
#                                            'quantity': 58000},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':3150,
#                                            'out_move_id':9401,
#                                            'quantity': 44000},context=context)
#
### 11-12-2013
##LRC-LRF1206LF-01-R020-F
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 7784,
#                                                    'so_line_id': 5851,
#                                                    'quantity': 14000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':7784,
#                                            'out_move_id':9618,
#                                            'quantity': 14000},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':7784,
#                                            'out_move_id':8796,
#                                            'quantity': 4000},context=context)
#
##LRC-LRF2010LF-01-R018-F
##Hk Location
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':14717,
#                                            'out_move_id':3711,
#                                            'quantity': 4000},context=context)
##Jabil GZ Location
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3301,
#                                                    'move_id': 5853,
#                                                    'so_line_id': 3825,
#                                                    'quantity': 2000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3301,
#                                          'in_move_id':5853,
#                                            'out_move_id':6331,
#                                            'quantity': 2000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3301,
#                                                    'move_id': 5853,
#                                                    'so_line_id': 3831,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3301,
#                                          'in_move_id':5853,
#                                            'out_move_id':6337,
#                                            'quantity': 1000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3303,
#                                                    'move_id': 9449,
#                                                    'so_line_id': 3831,
#                                                    'quantity': 1000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3303,
#                                          'in_move_id':9449,
#                                            'out_move_id':6337,
#                                            'quantity': 1000},context=context)
##LRC-LRZ1206LF-R000
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 1797,
#                                                    'so_line_id': 8282,
#                                                    'quantity': 4000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':1797,
#                                            'out_move_id':13514,
#                                            'quantity': 4000},context=context)
#
##MC0805-R050-FTW
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 5836,
#                                                    'move_id': 5837,
#                                                    'so_line_id': 4819,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 5836,
#                                          'in_move_id':5837,
#                                            'out_move_id':8035,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 5836,
#                                                    'move_id': 8747,
#                                                    'so_line_id': 6769,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 5836,
#                                          'in_move_id':8747,
#                                            'out_move_id':12372,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 5836,
#                                                    'move_id': 8747,
#                                                    'so_line_id': 6786,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 5836,
#                                          'in_move_id':8747,
#                                            'out_move_id':12385,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 5836,
#                                                    'move_id': 8747,
#                                                    'so_line_id': 6809,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 5836,
#                                          'in_move_id':8747,
#                                            'out_move_id':12390,
#                                            'quantity': 5000},context=context)
#
###MP2130DG-LF-Z(case error)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':16922,
#                                            'out_move_id':3863,
#                                            'quantity': 100000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':1678,
#                                            'out_move_id':13049,
#                                            'quantity': 50000},context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':16922,
#                                            'out_move_id':11658,
#                                            'quantity': 15000},context=context)
#
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8546,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14182,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8556,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14192,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8557,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14193,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8565,
#                                                    'quantity': 15000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14201,
#                                            'quantity': 15000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8566,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14202,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8567,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14203,
#                                            'quantity': 10000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2192,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8578,
#                                                    'quantity': 30000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2192,
#                                          'in_move_id':3876,
#                                            'out_move_id':14214,
#                                            'quantity': 30000},context=context)
#
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2445,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8578,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2445,
#                                          'in_move_id':3876,
#                                            'out_move_id':14214,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2445,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8578,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2445,
#                                          'in_move_id':3876,
#                                            'out_move_id':14214,
#                                            'quantity': 5000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2445,
#                                                    'move_id': 3876,
#                                                    'so_line_id': 8579,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2445,
#                                          'in_move_id':3876,
#                                            'out_move_id':14215,
#                                            'quantity': 5000},context=context)
#
##MP5000DQ-LF-Z
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2511,
#                                                    'move_id': 3868,
#                                                    'so_line_id': 4164,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2511,
#                                                    'move_id': 3958,
#                                                    'so_line_id': 4780,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2908,
#                                                    'move_id': 4122,
#                                                    'so_line_id': 4972,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3022,
#                                                    'move_id': 4122,
#                                                    'so_line_id': 4980,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2511,
#                                          'in_move_id':3868,
#                                            'out_move_id':7221,
#                                            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2511,
#                                          'in_move_id':3958,
#                                            'out_move_id':7005,
#                                            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 2908,
#                                          'in_move_id':4122,
#                                            'out_move_id':10501,
#                                            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3022,
#                                          'in_move_id':4122,
#                                            'out_move_id':10509,
#                                            'quantity': 5000},context=context)
#Closed

##MP5000DQ-LF-Z
#7957    18762    20000
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':18762,
#                                            'out_move_id':7957,
#                                            'quantity': 20000},context=context)

################################################ closed #############
#MP2130DG-LF-Z

#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 14437,
#                                                    'move_id': 15255,
#                                                    'so_line_id': 8578,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 16922,
#                                                    'move_id': 17460,
#                                                    'so_line_id': 8578,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 14437,
#                                          'in_move_id':15255,
#                                            'out_move_id':14214,
#                                            'quantity': 5000},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 16922,
#                                          'in_move_id':17460,
#                                            'out_move_id':14214,
#                                            'quantity': 10000},context=context)
#
##MP5010DQ-LF-Z
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':19543,
#                                            'out_move_id':8731,
#                                            'quantity': 100000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 3001,
#                                                    'move_id': 4191,
#                                                    'so_line_id': 3196,
#                                                    'quantity': 5000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                          'int_in_move_id': 3001,
#                                          'in_move_id':4191,
#                                            'out_move_id':6105,
#                                            'quantity': 5000},context=context)
###################################################
#PWC2512-1K0-J
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 4718,
#                                                    'so_line_id': 6919,
#                                                    'quantity': 7200,
#                                                    }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#                                          'in_move_id':4718,
#                                            'out_move_id':11508,
#                                            'quantity': 7200},context=context)
#
###PWC2512-2R2-J
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2426,
#                                                    'move_id': 3982,
#                                                    'so_line_id': 4437,
#                                                    'quantity': 1800,
#                                                    }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'int_move_id': 2426,
#                                                    'move_id': 3983,
#                                                    'so_line_id': 4437,
#                                                    'quantity': 5400,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                            'int_in_move_id': 2426,
#                                            'in_move_id':3982,
#                                            'out_move_id':7491,
#                                            'quantity': 1800},context=context)
#        fifo_control_obj.create(cr, uid, {
#                                            'int_in_move_id': 2426,
#                                            'in_move_id':3983,
#                                            'out_move_id':7491,
#                                            'quantity': 5400},context=context)
#
##S4025L
#
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 18368,
#                                                    'so_line_id': 2970,
#                                                    'quantity': 500,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                            'in_move_id':18368,
#                                            'out_move_id':14542,
#                                            'quantity': 500},context=context)
##ULW3-100R-J
#        move_allocated_control_obj.create(cr, uid, {
#                                                    'move_id': 15601,
#                                                    'so_line_id': 1000,
#                                                    'quantity': 10000,
#                                                    }, context=context)
#        fifo_control_obj.create(cr, uid, {
#                                            'in_move_id':15601,
#                                            'out_move_id':5672,
#                                            'quantity': 10000},context=context)

####################################################
#ULW3-22R0-J

#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 8111,'move_id': 8926,
#            'so_line_id': 9373,'quantity': 3000,
#            }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 8499,'move_id': 9455,
#            'so_line_id': 9368,'quantity': 1000,
#            }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 11144,'move_id': 17463,
#            'so_line_id': 9368,'quantity': 4000,
#            }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 14137,'move_id': 18814,
#            'so_line_id': 11803,'quantity': 3000,
#            }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 8499,'in_move_id':9455,
#            'out_move_id':15182,'quantity': 1000},context=context)
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 11144,'in_move_id':17463,
#            'out_move_id':15182,'quantity': 4000},context=context)
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 8111,'in_move_id':8926,
#            'out_move_id':15187,'quantity': 3000},context=context)
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 14137,'in_move_id':18814,
#            'out_move_id':19124,'quantity': 3000},context=context)
#
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 14137,'move_id': 18814,
#            'so_line_id': 3837,'quantity': 5000,
#            }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 14137,'in_move_id':18814,
#            'out_move_id':6343,'quantity': 5000},context=context)

####################################
##ULW3-33R0-J
#        move_allocated_control_obj.create(cr, uid, {
#            'move_id': 9143,
#            'so_line_id': 2714,'quantity': 19000,
#            }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#            'move_id': 14672,
#            'so_line_id': 2714,'quantity': 1000,
#            }, context=context)
#        fifo_control_obj.create(cr, uid, {
#            'in_move_id':9143,
#            'out_move_id':17624,'quantity': 19000},context=context)
#        fifo_control_obj.create(cr, uid, {
#            'in_move_id':14672,
#            'out_move_id':17624,'quantity': 1000},context=context)
#
##ULW5-4R7-J
##HK
#
#        fifo_control_obj.create(cr, uid, {
#            'in_move_id':9018,
#            'out_move_id':5859,'quantity': 19500},context=context)
##jabil
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 3229,'move_id': 8925,
#            'so_line_id': 3819,'quantity': 750,
#            }, context=context)
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 8498,'move_id': 16362,
#            'so_line_id': 3819,'quantity': 750,
#            }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 3229,'in_move_id':8925,
#            'out_move_id':6326,'quantity': 750},context=context)
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 8498,'in_move_id':16362,
#            'out_move_id':6326,'quantity': 750},context=context)
##UMK325C7106KM-T
##
#        move_allocated_control_obj.create(cr, uid, {
#            'int_move_id': 7946,'move_id': 8911,
#            'so_line_id': 10056,'quantity': 500,
#            }, context=context)
#
#        fifo_control_obj.create(cr, uid, {
#            'int_in_move_id': 7946,'in_move_id':8911,
#            'out_move_id':16318,'quantity': 500},context=context)
###################################################################
        return True

    def _prepare_so_to_po(self, cr, uid, sale_id, context=None):
        so_to_po_vals = {
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'allocated_onhand_all': True,
            'allocated_all': True,
            'sale_id': sale_id,
            }
        return so_to_po_vals

    def _prepare_wizard_stock_view(self, cr, uid, wizard_id, moves, sale_qty, onhand_allocated_qty, non_inc_qty, context=None):
        order_vals = {
            'wizard_id': wizard_id,
            'product_id': moves.product_id.id,
            'spq': moves.product_id.spq,
            'qty_order': sale_qty,
            'onhand_allocated_qty': onhand_allocated_qty,
            'allocated_qty': non_inc_qty,
            'product_supplier_id': moves.product_supplier_id.id,
            'move_id': moves.id,
        }
        return order_vals


    def _prepare_po_value(self, cr, uid, wizard_id, sale_id, partner_child_id,
                          partner_id, pricelist_id, moves, qty,
                          price_unit, context=None):
        order_line_vals = {
            'wizard_id': wizard_id,
            'sale_id': sale_id,
            'partner_child_id': partner_child_id,
            'partner_id': partner_id,
            'pricelist_id' : pricelist_id,
            'product_id': moves.product_id.id,
            'quantity': qty,
            'real_quantity': qty,
            'product_uom': moves.product_id.product_tmpl_id.uom_id.id,
            'price_unit': price_unit,
            'move_id': moves.id,
            'quantity_order': qty,
            'original_request_date': time.strftime('%Y-%m-%d'),
            'location_dest_id' : moves.location_id.id,
        }

        return order_line_vals

    def action_approval(self, cr, uid, ids, context=None):

#Decralation
#################################
        so_to_po_obj = self.pool.get("so.to.po")
        po_value_obj = self.pool.get("po.value")
        product_supplier_upper_limit_obj = self.pool.get("product.supplier.upper.limit")
        wizard_stock_view_obj = self.pool.get("wizard.stock.view")
        product_detail_obj = self.pool.get("product.detail")
        fifo_product_detail_obj = self.pool.get("fifo.product.detail")
        cost_price_fifo_obj = self.pool.get("cost.price.fifo")
        product_product_obj = self.pool.get("product.product")
        uom_obj = self.pool.get('product.uom')
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price_obj = self.pool.get('product.supplier.price')
        product_pricelist_obj = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        partner = self.pool.get('res.partner')
###################################


        for o in self.browse(cr, uid, ids):
            if context is None: context = {}
            context = dict(context, active_ids=ids, active_model=self._name)

            so_to_po_vals = self._prepare_so_to_po(cr, uid, o.id, context=context)
            wizard_id = so_to_po_obj.create(cr, uid, so_to_po_vals, context=context)

            prod_loc_vals_ori = []
            prod_loc_vals = []
            prod_loc_vals2 = []
            prod_loc_ori_sale_qty = {}
            prod_loc_qty_onhand_free = {}
            prod_loc_qty_incoming_free = {}

            move_id_vals = []
            move_vals = []
            move_qty = {}
            product_supplier_id = []
            product_ids = []

            for m_l in o.order_line:
                inputplori = 'p' + str(m_l.product_id.id) + 'l' + str(m_l.location_id.id)
                s_qty = uom_obj._compute_qty(cr, uid, m_l.product_uom.id, m_l.product_uom_qty, m_l.product_id.uom_id.id)
                if inputplori in prod_loc_vals_ori:
                    prod_loc_ori_sale_qty[inputplori] = prod_loc_ori_sale_qty[inputplori] + s_qty
                else:
                    prod_loc_vals_ori.append(inputplori)
                    prod_loc_ori_sale_qty[inputplori] = s_qty

#####################################
            for move_line in o.order_line:
                qty_free = 0.00
                qty_inc_non = 0.00
# Product
                product = product_product_obj.browse(cr, uid, move_line.product_id.id)

# Qty Sales For the product
                

############################################
# Create The Product Detail
                if move_line.product_id.id not in product_ids:
                    product_ids.append(move_line.product_id.id)
                    result1 = product_location_wizard_obj.stock_location_get(cr, uid, [product.id], context=context)
                    for rs in result1:
                        product_detail_obj.create(cr, uid, {
                            'wizard_id': wizard_id,
                            'product_id': product.id,
                            'location_id': rs['location_id'],
                            'qty_available': rs['qty_available'],
                            'qty_incoming_booked': rs['qty_incoming_booked'],
                            'qty_incoming_non_booked': rs['qty_incoming_non_booked'],
                            'qty_booked': rs['qty_booked'],
                            'qty_free': rs['qty_free'],
                            'qty_allocated': rs['qty_allocated'],
                            'qty_free_balance': rs['qty_free_balance'],
                            },
                            context=context)
                        inputpl = 'p'+ str(product.id) + 'l' + str(rs['location_id'])
                        prod_loc_vals.append(inputpl)
                        if inputpl in prod_loc_vals_ori:
                            sale_o = prod_loc_ori_sale_qty[inputpl]
                        else:
                            sale_o = 0.00
                        
                        if sale_o < rs['qty_free']:
                            qty_free_ori = sale_o
                        else:
                            qty_free_ori = rs['qty_free']

                        if sale_o > rs['qty_free'] + rs['qty_incoming_non_booked']:
                            qty_non_input_ori = rs['qty_incoming_non_booked']
                        else:
                            if sale_o > rs['qty_free']:
                                qty_non_input_ori = sale_o - rs['qty_free']
                            else:
                                qty_non_input_ori = 0.00
                        prod_loc_qty_onhand_free[inputpl] = qty_free_ori
                        prod_loc_qty_incoming_free[inputpl] = qty_non_input_ori


###############################################################

############################################


                inputpl2 = 'p'+ str(product.id) + 'l' + str(move_line.location_id.id)
                if inputpl2 not in prod_loc_vals2:
                    prod_loc_vals2.append(inputpl2)
                    res_fifo = cost_price_fifo_obj.stock_move_get(cr, uid, product.id, move_line.location_id.id, context=context)
                    if res_fifo:
                        if inputpl2 in prod_loc_vals:
                            loc_qty_free_input = prod_loc_qty_onhand_free[inputpl2]
                        else:
                            loc_qty_free_input = 0.00
                        for res_f1 in res_fifo:
                            if res_f1['qty_onhand_free'] > loc_qty_free_input:
                                loc_qty_alloc = loc_qty_free_input
                                loc_qty_free_input = 0.00
                            else:
                                loc_qty_alloc = res_f1['qty_onhand_free']
                                loc_qty_free_input = loc_qty_free_input - res_f1['qty_onhand_free']
                            fifo_product_detail_obj.create(cr, uid, {
                                                                     'wizard_id': wizard_id,
                                                                     'product_id': product.id,
                                                                     'int_move_id': res_f1['int_move_id'],
                                                                     'int_doc_no': res_f1['int_doc_no'],
                                                                     'move_id': res_f1['move_id'],
                                                                     'document_no': res_f1['document_no'],
                                                                     'document_date': res_f1['document_date'],
                                                                     'location_id': res_f1['location_id'],
                                                                     'product_qty': res_f1['product_qty'],
                                                                     'product_uom': res_f1['product_uom'],
                                                                     'qty_allocated': res_f1['qty_allocated'],
                                                                     'qty_onhand_free': res_f1['qty_onhand_free'],
                                                                     'onhand_allocated_qty': loc_qty_alloc,
                                                                     },
                                                                     context=context)

###################################
            wizard_qty_onhand_free = prod_loc_qty_onhand_free.copy()
            wizard_qty_incoming_free = prod_loc_qty_incoming_free.copy()
            
            for m_l2 in o.order_line:
                sale_qty = uom_obj._compute_qty(cr, uid, m_l2.product_uom.id, m_l2.product_uom_qty, m_l2.product_id.uom_id.id)
                wizardinputpl = 'p'+ str(m_l2.product_id.id) + 'l' + str(m_l2.location_id.id)
                if wizardinputpl in prod_loc_vals:
                    
                    qty_loc = wizard_qty_onhand_free[wizardinputpl]
                    qty_non = wizard_qty_incoming_free[wizardinputpl]
                    if qty_loc > 0:
                        if sale_qty > qty_loc:
                            wizard_qty_onhand_free[wizardinputpl] = 0.00
                            qty_free_input = qty_loc
                        else:
                            wizard_qty_onhand_free[wizardinputpl] = wizard_qty_onhand_free[wizardinputpl] - sale_qty
                            qty_free_input = sale_qty
                    else:
                        qty_free_input = 0.00
                    if qty_non > 0:
                        if sale_qty > qty_free_input:
                            if qty_non > (sale_qty - qty_free_input):
                                qty_non_input = sale_qty - qty_free_input
                                wizard_qty_incoming_free[wizardinputpl] =  wizard_qty_incoming_free[wizardinputpl] - (sale_qty - qty_free_input)
                            else:
                                qty_non_input = qty_non
                                wizard_qty_incoming_free[wizardinputpl] = 0.00
                        else:
                            qty_non_input = 0.00
                    else:
                        qty_non_input = 0.00

                else:
                    qty_free_input = 0.00
                    qty_non_input = 0.00

                wizard_stock_view_vals = self._prepare_wizard_stock_view(cr, uid, wizard_id, m_l2, sale_qty, qty_free_input, qty_non_input, context=context)
                wizard_stock_view_id = wizard_stock_view_obj.create(cr, uid, wizard_stock_view_vals, context=context)
################################



#                    raise osv.except_osv(_('XXNo Unit Cost Price!'), _('cannot find unit cost at supplier code ' +str(o.order_line)))
            for move_line2 in o.order_line:

                s_qty2 = uom_obj._compute_qty(cr, uid, move_line2.product_uom.id, move_line2.product_uom_qty, move_line2.product_id.uom_id.id)
                pl = 'p'+ str(move_line2.product_id.id) + 'l' + str(move_line2.location_id.id)
                if pl in prod_loc_vals:
#                    if move_line2.id == 2:
#                        raise osv.except_osv(_('Debug !'), _('xxx' + str(s_qty2) + 'xxx' + str(prod_loc_qty_onhand_free[pl]) + 'xxx' + str(prod_loc_qty_incoming_free[pl])))
                    if s_qty2 > prod_loc_qty_onhand_free[pl]:
                        s_qty2 = s_qty2 - prod_loc_qty_onhand_free[pl]
                        prod_loc_qty_onhand_free[pl] = 0.00
                        if s_qty2 > prod_loc_qty_incoming_free[pl]:
                            s_qty2 = s_qty2 - prod_loc_qty_incoming_free[pl]
                            prod_loc_qty_incoming_free[pl] = 0.00
                        else:
                            prod_loc_qty_incoming_free[pl] = prod_loc_qty_incoming_free[pl] - s_qty2
                            s_qty2 = 0.00
                    else:
                        prod_loc_qty_onhand_free[pl] = prod_loc_qty_onhand_free[pl] - s_qty2
                        s_qty2 = 0.00
                    qty_order = s_qty2
                else:
                    qty_order = s_qty2
                if qty_order > 0:
                    product_supplier = product_supplier_obj.browse(cr, uid, move_line2.product_supplier_id.id)
                    partner_child_id = product_supplier.partner_child_id.id
            
                    partner_id = product_supplier.partner_child_id.partner_id.id
                    supplier = partner.browse(cr, uid, partner_id)
                    
                    pricelist_id = supplier.property_product_pricelist_purchase.id
                    date_order = time.strftime('%m-%d-%Y')
                    product_supplier_price_ids = product_supplier_price_obj.search(cr, uid, [('product_supplier_id','=',product_supplier.id),
                        ('effective_date','<=',date_order)], order='effective_date DESC')
                    price = 0.00
                    if product_supplier_price_ids:

                        product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, 
                            product_supplier_price_ids[0], context=context)
#                                raise osv.except_osv(_('XXNo Unit Cost Price!'), _('cannot find unit cost at supplier code ' +str(product_supplier_price_id.effective_date)))
                        company_id = o.shop_id.company_id.id
                        company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)

                        ptype_src = company.currency_id.id
                        currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id

                        product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid,
                            [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',qty_order)], order='qty DESC')
                        if product_supplier_upper_limit_id:
                            
                            product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid,
                                product_supplier_upper_limit_id[0], context=context)
                            price = currency_obj.compute(cr, uid, 
                                product_supplier.currency_id.id, ptype_src, 
                                    product_supplier_upper_limit.unit_cost, round=False)
                        else:
                            price = currency_obj.compute(cr, uid, product_supplier.currency_id.id,
                                ptype_src, product_supplier_price_id.unit_cost, round=False)
                        price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                        price = product_product_obj.round_p(cr, uid, price, 'Purchase Price',)
                    else:
                        raise osv.except_osv(_('No Unit Cost Price!'), _('cannot find unit cost at supplier code ' +str(product_supplier.name)))
                    #raise osv.except_osv(_('XXNo Unit Cost Price!'), _('cannot find unit cost at supplier code ' +str(price)))
                    po_value_vals = self._prepare_po_value(cr, uid, wizard_id, o.id, partner_child_id,
                                                           partner_id, pricelist_id, move_line2, qty_order,
                                                           price, context=context)
                    po_value_id = po_value_obj.create(cr, uid, po_value_vals,context=context)

##########################################################





        return {
                'name':_("Convert To Purchase Order"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'so.to.po',
                'res_id': wizard_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
                }


    def wkf_action_cancel(self, cr, uid, ids, context=None):
        #Original Start
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids2:
                if pick.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Could not cancel sales order !'),
                        _('You must first cancel all picking attached to this sales order.'))
                if pick.state == 'cancel':
                    for mov in pick.move_lines:
                        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                        if proc_ids:
                            for proc in proc_ids:
                                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
            for r in self.read(cr, uid, ids, ['picking_ids2']):
                for pick in r['picking_ids2']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
            for inv in sale.invoice_ids:
                if inv.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Could not cancel this sales order !'),
                        _('You must first cancel all invoices attached to this sales order.'))
            for r in self.read(cr, uid, ids, ['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)
        #Original Stop
            for line in sale.order_line:
                if line.qty_onhand_count > 0:
                    raise osv.except_osv(
                        _('Could not cancel this sales order !'),
                        _('You must first cancel all quantity which allocated to this sales order.'))
                count_allocated = 0
                for all in line.allocated_ids:
                    count_allocated = count_allocated + 1
                if count_allocated > 0:
                    raise osv.except_osv(
                        _('Could not cancel this sales order !'),
                        _('You must first cancel all quantity which allocated to this sales order.'))
        #Original Start
            sale_order_line_obj.write(cr, uid, [l.id for l in  sale.order_line],
                    {'state': 'cancel'})
            message = _("The sales order '%s' has been cancelled.") % (sale.name,)
            self.log(cr, uid, sale.id, message)
        self.write(cr, uid, ids, {'state': 'cancel'})
        #Original Stop
        return True

sale_order()

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    _description = "Sales Order Line"

    def do_refresh(self, cr, uid, ids, context=None):
        return True

    def button_confirm_add(self, cr, uid, ids, context=None):
        self.button_confirm(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}

        sale_order_obj = self.pool.get('sale.order')
        res = super(sale_order_line, self).default_get(cr, uid, fields, context=context)
        model = context and 'active_model' in context and context.get(('active_model')) or False
        if model == 'sale.order':
            for lines in sale_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
                if not lines.partner_id:
                    raise osv.except_osv(_('Error !'), _('please select the customer before adding lines'))
                if 'partner_id_parent' in fields:
                    res.update({'partner_id_parent': lines.partner_id.id})
                if 'shop_id_parent' in fields:
                    res.update({'shop_id_parent': lines.shop_id.id})
                if 'company_id_parent' in fields:
                    res.update({'company_id_parent': lines.shop_id.company_id.id})
                if 'pricelist_id_parent' in fields:
                    res.update({'pricelist_id_parent': lines.pricelist_id.id})
                if 'date_order_parent' in fields:
                    res.update({'date_order_parent': lines.date_order})
                if 'fiscal_position_id_parent' in fields:
                    res.update({'fiscal_position_id_parent': lines.fiscal_position.id})
                if 'order_id' in fields:
                    res.update({'order_id': lines.id})
        return res



    def onhand_reallocated(self, cr, uid, ids, context=None):
        onhand_rellocated_obj = self.pool.get("onhand.reallocated")
        fifo_onhand_reallocated_obj = self.pool.get("fifo.onhand.reallocated")
        product_location_wizard_obj = self.pool.get("product.location.wizard")
        product_uom_obj = self.pool.get("product.uom")
        sale_allocated_obj = self.pool.get("sale.allocated")
        stock_move_obj = self.pool.get("stock.move")
        cost_price_fifo_obj = self.pool.get("cost.price.fifo")
        move_allocated_control_obj = self.pool.get("move.allocated.control")
        
        for o in self.browse(cr, uid, ids):
            if context is None: context = {}
            context = dict(context, active_ids=ids, active_model=self._name)

            result1 = product_location_wizard_obj.stock_location_get(cr, uid, [o.product_id.id], context=context)
            qty_free = 0.00
            for rs in result1:
                if rs['location_id'] == o.location_id.id:
                    qty_free = rs['qty_free']

            qtyp = product_uom_obj._compute_qty(cr, uid, o.product_uom.id, o.product_uom_qty, o.product_id.uom_id.id)
            sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('sale_line_id','=',o.id)]), context=context)
            qty_allocated = 0.00
            if sale_allocated_ids:
                for val in sale_allocated_ids:
                     qty_allocated = qty_allocated + (val.quantity - val.received_qty)
            qty_order_allocated = 0.00
            qty_order_allocated = qtyp - qty_allocated

            incoming_qty = 0.00
            if qtyp > 0:
                stock_move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',o.id),('state','=','done')])
                if stock_move_ids:
                    for stock_move_id in stock_move_ids:
                        stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                        incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, stock_move.product_id.uom_id.id)

            total_qty_reallocated = 0.00
            if o.qty_onhand_allocated + qty_free < qty_order_allocated:
                total_qty_reallocated = o.qty_onhand_allocated + qty_free - incoming_qty
            else:
                total_qty_reallocated = qty_order_allocated - incoming_qty
            
            qty_delivery = 0.00
            move_ids = stock_move_obj.search(cr, uid, [('sale_line_id','=',o.id),('state','=','assigned')])
            if move_ids:
                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)

            wizard_id = onhand_rellocated_obj.create(cr, uid, 
                                                     {'allocated_by_coulumn': True,
                                                      'qty_order_allocated' : qty_order_allocated,
                                                      'qty_free' : qty_free,
                                                      'qty_onhand_count': o.qty_onhand_allocated,
                                                      'qty_order_received': incoming_qty,
                                                      'total_qty_reallocated' : total_qty_reallocated,
                                                      'qty_delivery': qty_delivery,
                                                      'sale_line_id' : o.id,
                                                      'location_id' : o.location_id.id,
                                                      'spq' : o.product_id.spq,
                                                      'product_id' : o.product_id.id,
                                                      'allocated_by_field': False,
                                                      'qty_reallocated' : o.qty_onhand_allocated - incoming_qty,},
                                                     context=context)

            all_qty = {}
            
            res_fifo = cost_price_fifo_obj.stock_move_get(cr, uid,o.product_id.id, o.location_id.id, context=context)
            if res_fifo:
                for res_f1 in res_fifo:
                    if res_f1['int_move_id']:
                        move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',res_f1['move_id']), ('int_move_id','=',res_f1['int_move_id']), ('so_line_id','=',o.id)]), context=context)
                    else:
                        move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',res_f1['move_id']), ('so_line_id','=',o.id)]), context=context)
                    onhand_allocated_qty = 0.00
                    if move_allocated_control_ids:
                        for all_c in move_allocated_control_ids:
                            onhand_allocated_qty = onhand_allocated_qty + (all_c.quantity - all_c.rec_quantity)

                    qty_allocated = res_f1['qty_allocated'] - onhand_allocated_qty
                    fifo_onhand_reallocated_obj.create(cr, uid, {
                                                                 'int_move_id': res_f1['int_move_id'],
                                                                 'wizard_id2': wizard_id,
                                                                 'product_id': o.product_id.id,
                                                                 'move_id': res_f1['move_id'],
                                                                 'document_no': res_f1['document_no'],
                                                                 'document_date': res_f1['document_date'],
                                                                 'location_id': res_f1['location_id'],
                                                                 'product_qty': res_f1['product_qty'],
                                                                 'product_uom': res_f1['product_uom'],
                                                                 'qty_allocated': qty_allocated,
                                                                 'qty_onhand_free': res_f1['product_qty'] - qty_allocated,
                                                                 'onhand_allocated_qty': onhand_allocated_qty,
                                                                 },
                                                                 context=context)
        return {
                'name':_("OnHand Reallocated"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'onhand.reallocated',
                'res_id': wizard_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                'context': context,
                }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'allocated_ids':[],'qty_onhand_allocated': 0.00})
        return super(sale_order_line, self).copy_data(cr, uid, id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_allocated_obj = self.pool.get("sale.allocated")
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.qty_onhand_count > 0:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sale order line which is being allocated to purchase order \'%s\'!') %(rec.name,))
            sale_order_line_id = rec.id
            sale_allocated_ids = sale_allocated_obj.browse(cr, uid,
                sale_allocated_obj.search(cr, uid, [('sale_line_id', '=', sale_order_line_id)]),
                context=context)
            if sale_allocated_ids:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sale order line which is being allocated to purchase order \'%s\'!') %(rec.name,))
        return super(sale_order_line, self).unlink(cr, uid, ids, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def location_onchange(self, cr, uid, ids, product, location_id, context=None):
        location_ids = []
        res = {}
        product_product_obj = self.pool.get('product.product')
        product_product = product_product_obj.browse(cr, uid, product, context=context)
        for loc in product_product.location_ids:
            location_ids.append(loc.stock_location_id.id)
            if (loc.default_key == True):
                location_id_default = loc.stock_location_id.id
        if location_id not in location_ids:
            warning = {
                       'title': _('Configuration Error !'),
                       'message' : 'the selected location is not belong to this product, the system will automated selected the default location'
                       }
            res['warning'] = warning
            location_id = location_id_default or False
        res['value']= {'location_id': location_id,}
        res['domain'] = {'location_id': [('id','in',location_ids)]}
        return res

    def product_id_change3(self, cr, uid, ids, 
            location_id, company_id, product_customer_id,
            effective_date, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False,
            packaging=False, fiscal_position=False,
            flag=False, context=None):
        currency_obj = self.pool.get('res.currency')
        product_uom_obj = self.pool.get('product.uom')
        product_product_obj = self.pool.get('product.product')
        product_customer_obj = self.pool.get('product.customer')
        product_customer_price = self.pool.get('product.customer.price')
        product_pricelist = self.pool.get('product.pricelist')
        product_customer_upper_limit_obj = self.pool.get('product.customer.upper.limit')
        res = self.product_id_change2(cr, uid, ids, company_id, product_customer_id,
                                      effective_date, pricelist, product,
                                      qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                                      partner_id=partner_id, lang=lang, update_tax=update_tax,
                                      date_order=date_order, fiscal_position=fiscal_position, context=context)
        location_ids = []
        default_location_id = False
#        raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(res,))
        if not product_customer_id:
            return res
        if product:
            if 'product_uom' in res['value']:
                uom = res['value']['product_uom']
            default_uom = product_product_obj.browse(cr, uid, product, context=context).product_tmpl_id.uom_id.id
            spq = product_product_obj.browse(cr, uid, product, context=context).spq
            moq = product_customer_obj.browse(cr, uid, product_customer_id, context=context).moq
            res['value'].update({
                                 'spq': spq,
                                 'moq': moq,
                                 })
            if qty > 0:
                qty_overall = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
    #            raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(qty_overall,))


                if qty_overall < moq:
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'the input quantity is below from moq. \n (moq = ' + str(moq) + ')'
                                   }
                        res['warning'] = warning

                if qty_overall < spq:
                    qty_overall = 0
                if qty_overall%spq != 0:
                    qty_overall= 0
                if qty_overall == 0:
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
            else:
                qty_overall = 0
            if product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom) != qty_overall:
                product_customer_val = product_customer_obj.browse(cr, uid, product_customer_id, context=context)
                company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
                ptype_src = company.currency_id.id
                product_customer_price_ids = product_customer_price.search(cr, uid, [('product_customer_id','=',product_customer_id),('effective_date','<=',effective_date)], order='effective_date ASC')
                price = 0.00
                if product_customer_price_ids:
                    product_customer_price_id = product_customer_price.browse(cr, uid, product_customer_price_ids[0], context=context)
                    product_customer_upper_limit_ids = product_customer_upper_limit_obj.search(cr, uid, [('product_customer_price_id','=',product_customer_price_id.id),('qty','<=',qty_overall)], order='qty DESC')
                    currency_id = product_pricelist.browse(cr, uid, pricelist, context=context).currency_id.id
                    if product_customer_upper_limit_ids:
                        product_customer_upper_limit_id = product_customer_upper_limit_obj.browse(cr, uid, product_customer_upper_limit_ids[0], context=context)
                        price = currency_obj.compute(cr, uid, product_customer_val.pricelist_id.currency_id.id, ptype_src, product_customer_upper_limit_id.unit_cost, round=False)
                    else:
                        price = currency_obj.compute(cr, uid, product_customer_val.pricelist_id.currency_id.id, ptype_src, product_customer_price_id.unit_cost, round=False)
                    price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                    price = product_uom_obj._compute_price(cr, uid, default_uom, price, default_uom)
                    price = product_product_obj.round_p(cr, uid, price, 'Sale Price')
                res['value'].update({
                                     'price_unit': price,
                                     'product_uom_qty': qty_overall,
                                     'product_uom': default_uom,
                                     })

            product_product = product_product_obj.browse(cr, uid, product, context=context)

            for loc in product_product.location_ids:
                location_ids.append(loc.stock_location_id.id)
                if (loc.default_key == True):
                    default_location_id = loc.stock_location_id.id
            if location_id:
                if location_id not in location_ids:
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n The Selected Location is not belong to this product.'
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'The Selected Location is not belong to this product.'
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'The Selected Location is not belong to this product.'
                                   }
                        res['warning'] = warning
                    location_id = default_location_id or False
            else:
                location_id = default_location_id


            res['value'].update({'location_id': location_id})
            res['domain'].update({'location_id': [('id','in',location_ids)]})
        return res

    def product_uom_change3(self, cursor, user, ids, location_id, company_id,
                            product_customer_id, effective_date,
                            pricelist, product, qty=0,
                            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                            lang=False, update_tax=True, date_order=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])

        res = self.product_id_change3(cursor, user, ids, location_id, company_id, product_customer_id,
                                      effective_date, pricelist, product,
                                      qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                                      partner_id=partner_id, lang=lang, update_tax=update_tax,
                                      date_order=date_order, context=context)
#        if 'product_uom' in res['value']:
#            del res['value']['product_uom']
#        raise osv.except_osv(_('Debug !'), _(' \'%s\'!') %(res,))
        if not uom:
            res['value']['price_unit'] = 0.0
        return res

    def _qty_onhand_allocated(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.qty_onhand_allocated +  obj.qty_received_onorder
        return res

    def _qty_received_onorder(self, cr, uid, ids, name, arg, context=None):

        if not ids: return {}
        res = {}
        sale_allocated_obj = self.pool.get("sale.allocated")

        for obj in self.browse(cr, uid, ids, context=context):
            sale_order_line_id = obj.id
            qty_received = 0.00
            sale_allocated_ids = sale_allocated_obj.browse(cr, uid,
                sale_allocated_obj.search(cr, uid, [('sale_line_id', '=', sale_order_line_id)]),
                context=context)
            if sale_allocated_ids:
                for val in sale_allocated_ids:
                    qty_received = qty_received + val.received_qty

            res[obj.id] = qty_received
        return res

    _columns = {
        'partner_id_parent': fields.many2one('res.partner', 'Customer'),
        'shop_id_parent': fields.many2one('sale.shop', 'Shop'),
        'company_id_parent': fields.many2one('res.company', 'company'),
        'fiscal_position_id_parent': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'pricelist_id_parent': fields.many2one('product.pricelist', 'Pricelist'),
        'date_order_parent': fields.date('Date'),
        'effective_ids': fields.one2many('change.effective', 'sale_order_line_id', 'Change Effective History', readonly=True,),
        'location_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', required=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'allocated_ids': fields.one2many('sale.allocated', 'sale_line_id', 'Purchase Allocated', readonly=True, ondelete='set null'),
        'move_allocated_control_ids': fields.one2many('move.allocated.control', 'so_line_id', 'Move Allocated Control', readonly=True, ondelete='set null'),
        'qty_onhand_allocated' : fields.float("Quantity On Hand Allocated", digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'qty_received_onorder': fields.function(_qty_received_onorder, type='float', string='Quantity Received Based On Order'),
        'qty_onhand_count': fields.function(_qty_onhand_allocated, type='float', string='Total Quantity On Hand Allocated'),
    }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'allocated_ids':[],
                        'effective_ids':[],
                        'move_allocated_control_ids': [],
                        'qty_onhand_allocated': 0.00,
                        })
        return super(sale_order_line, self).copy_data(cr, uid, id, default, context)

    _defaults = {
        'product_uom_qty': 0,
        'product_uos_qty': 0,
    }
sale_order_line()

class product_pricelist(osv.osv):
    _inherit = "product.pricelist"
    _description = "Pricelist"

    def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        res = super(product_pricelist, self).price_get(cr, uid, ids, prod_id, qty,
                                      partner=partner,
                                      context=context)
        if res[ids[0]] == False:
            res.update({ids[0]: 0.00})

        return res
    
    def product_id_change3(self, cr, uid, ids, company_id, product_customer_id,
            effective_date, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False,
            packaging=False, fiscal_position=False,
            flag=False, context=None):
        product_product_obj = self.pool.get('product.product')
        res = self.product_id_change2(cr, uid, ids, company_id, product_customer_id,
                                      effective_date, pricelist, product,
                                      qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                                      partner_id=partner_id, lang=lang, update_tax=update_tax,
                                      date_order=date_order, context=context)
        location_ids = []
        if product:
            product_product = product_product_obj.browse(cr, uid, product, context=context)
            for loc in product_product.location_ids:
                location_ids.append(loc.stock_location_id.id)
                if (loc.default_key == True):
                    res['value'].update({'location_id': loc.stock_location_id.id})
            res['domain'].update({'location_id': [('id','in',location_ids)]})
        return res

product_pricelist()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
