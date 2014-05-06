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
import time
import math

class purchase_make_incoming(osv.osv_memory):
    _name = "purchase.make.incoming"
    _description = "Purchase Make incoming(s)"
    _columns = {
        'incoming_date': fields.date('Goods Receipt Date'),
        'do_date': fields.date('GRN Date'),
        'invoice_date': fields.date('Supplier Invoice Date'),
        'invoice_no': fields.char('Supplier Invoice No', size=64),
        'ref_no': fields.char('Reference No', size=64),
        'desc': fields.text('Description'),
        'country_org_id': fields.many2one('res.country', 'Country of Origin'),
        'country_des_id': fields.many2one('res.country', 'Country of Destination'),
        'incoming_lines_ids' : fields.one2many('incoming.lines', 'wizard_id', 'Incoming Lines'),
    }

    def view_init(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False)
        if record_id:
            order = self.pool.get('purchase.order').browse(cr, uid, record_id, context=context)
            if order and order.state == 'draft':
                raise osv.except_osv(_('Warning !'),'You can not create incoming(s) when purchase order is not confirmed.')
        return False

    def default_get(self, cr, uid, fields, context=None):
        purchase_order_obj = self.pool.get('purchase.order')
        stock_move_obj = self.pool.get('stock.move')
        product_uom_obj = self.pool.get('product.uom')
        result1 = []
        if context is None:
            context = {}
        res = super(purchase_make_incoming, self).default_get(cr, uid, fields, context=context)

        for order in purchase_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            for lines in order.order_line:
                qty_delivery = 0.00
                move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',lines.id),('state','!=','cancel')])
                if move_ids:
                    for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                        qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
                qty_sales = product_uom_obj._compute_qty(cr, uid, lines.product_uom.id, lines.product_qty, lines.product_id.uom_id.id)

                qty_order = qty_sales - qty_delivery
                qty_unit_sale = qty_sales / lines.product_qty
                qty_order = math.floor(qty_order / qty_unit_sale)

                incoming_lines_vals = {
                    'spq' : lines.spq,
                    'order_id' : order.id,
                    'uom_id' : lines.product_uom.id,
                    'product_uom2' : lines.product_id.uom_id.id,
                    'product_uom' : lines.product_uom.id,
                    'qty_delivery' : qty_delivery,
                    'product_uom_qty' : lines.product_qty,
                    'product_id' : lines.product_id.id,
                    'order_line_id' : lines.id,
                    'qty_order' : qty_order,
                    'location_dest_id' : lines.location_dest_id.id,
                    }
                result1.append(incoming_lines_vals)
        if 'incoming_lines_ids' in fields:
            res.update({'incoming_lines_ids': result1})

        return res

#    def generated_do(self, cr, uid, ids, context=None):
#        wf_service = netsvc.LocalService("workflow")
#        assert len(ids) == 1
#        purchase_order_obj = self.pool.get('purchase.order')
#        stock_picking_obj = self.pool.get('stock.picking')
#        stock_move_obj = self.pool.get('stock.move')
#        account_fiscal_position = self.pool.get('account.fiscal.position')
#        account_tax = self.pool.get('account.tax')
#        res_partner_obj = self.pool.get('res.partner')
#        mod_obj = self.pool.get('ir.model.data')
#        act_obj = self.pool.get('ir.actions.act_window')
#        res_temp1 = []
#        res_temp2 = []
#        res_temp3 = []
#        res_temp4 = []
#        res_temp5 = []
#        res_temp6 = []
#        res_temp7 = []
#        res_temp8 = []
#        res_temp9 = []
#        res_temp10 = []
#        res_temp11 = []
#        newinv = []
#
#        po_id_temp = []
#
#        supplier_group = {}
#        supplier_branch_group = {}
#        ordering_contact_group = {}
#        shipping_address_group = {}
#        invoice_address_group = {}
#        pricelist_group = {}
#        ship_method_group = {}
#        fob_point_key_group = {}
#        payment_term_group = {}
#        fiscal_position_group = {}
#
#        generated = self.browse(cr, uid, ids[0], context=context)
#        move_ids = generated.incoming_lines_ids
#        if move_ids:
#            #store data
#            for moves in move_ids:
#                if moves.qty_order < 1:
#                    continue
#                po_vals = purchase_order_obj.browse(cr, uid, moves.order_id.id, context=context)
#                res_temp1.append({
#                                 'supplier_id': (po_vals.partner_id and po_vals.partner_id.id) or 0,
#                                 'supplier_branch_id': (po_vals.partner_child_id and po_vals.partner_child_id.id) or 0,
#                                 'shipping_address_id' : (po_vals.partner_shipping_id and po_vals.partner_shipping_id.id) or 0,
#                                 'pricelist_id' : (po_vals.pricelist_id and po_vals.pricelist_id.id) or 0,
#                                 'fiscal_position_id' : (po_vals.fiscal_position and po_vals.fiscal_position.id) or 0,
#                                 'po_line_id' : moves.order_line_id.id,
#                                 }
#                                )
#                #sort by supplier
#                fiscal_position_group[moves.order_line_id.id] = po_vals.fiscal_position.id
#                #supplier_group[moves.order_line_id.id] = po_vals.partner_id.id
#            if res_temp1:
#                for key, value in sorted(fiscal_position_group.iteritems(), key=lambda (k,v): (v,k)):
##                for key, value in sorted(supplier_group.iteritems(), key=lambda (k,v): (v,k)):
#                    for temp in res_temp1:
#                        if temp['po_line_id'] == key:
#                            pricelist_group[temp['po_line_id']] = temp['pricelist_id']
##                            shipping_address_group[temp['po_line_id']] = temp['shipping_address_id']
#                            res_temp4.append({
#                                            'supplier_id': temp['supplier_id'],
#                                            'supplier_branch_id': temp['supplier_branch_id'],
#                                            'shipping_address_id' : temp['shipping_address_id'],
#                                            'pricelist_id' : temp['pricelist_id'],
#                                            'fiscal_position_id' : temp['fiscal_position_id'],
#                                            'po_line_id' : temp['po_line_id'],
#                                            })
#
#            if res_temp4:
#                for key, value in sorted(pricelist_group.iteritems(), key=lambda (k,v): (v,k)):
##                for key, value in sorted(shipping_address_group.iteritems(), key=lambda (k,v): (v,k)):
#                    for temp in res_temp4:
#                        if temp['po_line_id'] == key:
#                            shipping_address_group[temp['po_line_id']] = temp['shipping_address_id']
#
##                            pricelist_group[temp['po_line_id']] = temp['pricelist_id']
##                            invoice_address_group[temp['po_line_id']] = temp['invoice_address_id']
#                            res_temp6.append({
#                                            'supplier_id': temp['supplier_id'],
#                                            'supplier_branch_id': temp['supplier_branch_id'],
#                                            'shipping_address_id' : temp['shipping_address_id'],
#                                            'pricelist_id' : temp['pricelist_id'],
#                                            'fiscal_position_id' : temp['fiscal_position_id'],
#                                            'po_line_id' : temp['po_line_id'],
#                                            })
#
#            if res_temp6:
#                for key, value in sorted(shipping_address_group.iteritems(), key=lambda (k,v): (v,k)):
#                    for temp in res_temp6:
#                        if temp['po_line_id'] == key:
#                             supplier_branch_group[temp['po_line_id']] = temp['supplier_branch_id']
# #                            fiscal_position_group[temp['po_line_id']] = temp['fiscal_position_id']
#                             res_temp9.append({
#                                            'supplier_id': temp['supplier_id'],
#                                            'supplier_branch_id': temp['supplier_branch_id'],
#                                            'shipping_address_id' : temp['shipping_address_id'],
#                                            'pricelist_id' : temp['pricelist_id'],
#                                            'fiscal_position_id' : temp['fiscal_position_id'],
#                                            'po_line_id' : temp['po_line_id'],
#                                            })
#
#            if res_temp9:
#                for key, value in sorted(supplier_branch_group.iteritems(), key=lambda (k,v): (v,k)):
#                    for temp in res_temp6:
#                        if temp['po_line_id'] == key:
#                             supplier_group[temp['po_line_id']] = temp['supplier_id']
# #                            fiscal_position_group[temp['po_line_id']] = temp['fiscal_position_id']
#                             res_temp10.append({
#                                            'supplier_id': temp['supplier_id'],
#                                            'supplier_branch_id': temp['supplier_branch_id'],
#                                            'shipping_address_id' : temp['shipping_address_id'],
#                                            'pricelist_id' : temp['pricelist_id'],
#                                            'fiscal_position_id' : temp['fiscal_position_id'],
#                                            'po_line_id' : temp['po_line_id'],
#                                            })
#            if res_temp10:
#                for key, value in sorted(supplier_group.iteritems(), key=lambda (k,v): (v,k)):
#                    for temp in res_temp10:
#                        if temp['po_line_id'] == key:
#                            res_temp11.append({
#                                            'supplier_id': temp['supplier_id'],
#                                            'supplier_branch_id': temp['supplier_branch_id'],
#                                            'shipping_address_id' : temp['shipping_address_id'],
#                                            'pricelist_id' : temp['pricelist_id'],
#                                            'fiscal_position_id' : temp['fiscal_position_id'],
#                                            'po_line_id' : temp['po_line_id'],
#                                            })
#                            
##            raise osv.except_osv(
##                                 _('Debug !'),
##                                 _(str(res_temp11) + ' - ' + str(' ')))
#            if res_temp11:
##                raise osv.except_osv(
##                                     _('Debug !'),
##                                     _(str(res_temp11) + ' - ' + str(' ')))
#
#                old_record = False
#                for temp in res_temp11:
#                    if old_record == False:
#                        old_record = True
#                        supplier_id = temp['supplier_id']
#                        supplier_branch_id = temp['supplier_branch_id']
#                        shipping_address_id = temp['shipping_address_id']
#                        pricelist_id = temp['pricelist_id']
#                        fiscal_position_id = temp['fiscal_position_id']
#                        po_line_id = temp['po_line_id']
#                        supplier_val = supplier_id and res_partner_obj.browse(cr, uid, supplier_id, context=context) or False
#                        addr = supplier_id and res_partner_obj.address_get(cr, uid, [supplier_id], ['delivery', 'invoice', 'contact'])
#                        for mv in move_ids:
#                            if mv.order_line_id.id == po_line_id:
#                                po_name = mv.order_id.name
#                                po_id = mv.order_id.id
#                                po_id_temp.append(po_id)
#                                if mv.order_id.invoice_method == 'picking':
#                                    invoice_state = '2binvoiced'
#                                else:
#                                    invoice_state = 'none'
#                                company_id = mv.order_id.company_id.id
#                                taxes = account_tax.browse(cr, uid, map(lambda x: x.id, mv.order_line_id.taxes_id))
#                                pol_name = mv.order_line_id.name
#                                product_id = mv.order_line_id.product_id.id
#                                product_qty = mv.qty_order
#                                product_uom = mv.order_line_id.product_uom.id
#                                date = mv.order_line_id.estimated_time_departure
#                                date_expected = mv.order_line_id.estimated_time_arrive
#                                location_id = mv.order_id.partner_id.property_stock_supplier.id
#                                location_dest_id = mv.location_dest_id.id
#                                move_dest_id = mv.order_line_id.move_dest_id.id
#                                price_unit = mv.order_line_id.price_unit
#                                price_currency_id = mv.order_id.pricelist_id.currency_id.id
#                        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
#                        picking_vals = {
#                                        'name': sequence,
#                                        'date': generated.incoming_date or time.strftime('%Y-%m-%d'),
#                                        'do_date': generated.do_date or time.strftime('%Y-%m-%d'),
#                                        'type': 'in',
#                                        'state': 'draft',
#                                        'invoice_state': invoice_state,
#                                        'company_id': company_id,
#                                        'pricelist_id': pricelist_id,
#                                        'partner_order_id' : addr and addr['contact'] or False,
#                                        'partner_shipping_id' : shipping_address_id,
#                                        'partner_invoice_id' : addr and addr['invoice'] or False,
#                                        'partner_id': supplier_id,
#                                        'partner_child_id': supplier_branch_id,
#                                        'ship_method_id' : supplier_val and supplier_val.ship_method_id and supplier_val.ship_method_id.id or False,
#                                        'fob_id' : supplier_val and supplier_val.fob_id and supplier_val.fob_id.id or False,
#                                        'sale_term_id' : supplier_val and supplier_val.sale_term_id and supplier_val.sale_term_id.id or False,
#                                        'fiscal_position' : fiscal_position_id,
#                                        'invoice_date' : generated.invoice_date,
#                                        'invoice_no' : generated.invoice_no,
#                                        'ref_no' : generated.ref_no,
#                                        'country_org_id' : generated.country_org_id.id,
#                                        'country_des_id' : generated.country_des_id.id,
#                                        'note' : generated.desc,
#                                        }
#                        picking_create = stock_picking_obj.create(cr, uid, picking_vals)
#                        newinv.append(picking_create)
#                        cr.execute('insert into purchase_order_picking_rel (order_id,picking_id) values (%s,%s)', (po_id, picking_create))
#                        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
#                        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
#
#                        move_vals = {
#                                     'name': po_name + ': ' + (pol_name or ''),
#                                     'picking_id': picking_create,
#                                     'product_id': product_id,
#                                     'product_qty': product_qty,
#                                     'product_uom': product_uom,
#                                     'product_uos': product_uom,
#                                     'date': date or time.strftime('%Y-%m-%d'),
#                                     'date_expected': date_expected or time.strftime('%Y-%m-%d'),
#                                     'location_id': location_id,
#                                     'location_dest_id': location_dest_id,
#                                     'address_id': shipping_address_id,
#                                     'move_dest_id': move_dest_id,
#                                     'state': 'assigned',
#                                     'purchase_line_id': po_line_id,
#                                     'company_id': company_id,
#                                     'price_unit': price_unit,
#                                     'price_currency_id': price_currency_id,
#                                     'taxes_id': [(6,0,taxes_ids)],
#                                     }
#
#
#                        stock_move_obj.create(cr, uid, move_vals, context=None)
#                    else:
#                        for mv in move_ids:
#                            if mv.order_line_id.id == temp['po_line_id']:
#                                po_name_x = mv.order_id.name
#                                po_id_x = mv.order_id.id
#                                if mv.order_id.invoice_method == 'picking':
#                                    invoice_state_x = '2binvoiced'
#                                else:
#                                    invoice_state_x = 'none'
#                                company_id_x = mv.order_id.company_id.id
#                                taxes_x = account_tax.browse(cr, uid, map(lambda x: x.id, mv.order_line_id.taxes_id))
#                                pol_name_x = mv.order_line_id.name
#                                product_id_x = mv.order_line_id.product_id.id
#                                product_qty_x = mv.qty_order
#                                product_uom_x = mv.order_line_id.product_uom.id
#                                date_x = mv.order_line_id.estimated_time_departure
#                                date_expected_x = mv.order_line_id.estimated_time_arrive
#                                location_id_x = mv.order_id.partner_id.property_stock_supplier.id
#                                location_dest_id_x = mv.location_dest_id.id
#                                move_dest_id_x = mv.order_line_id.move_dest_id.id
#                                price_unit_x = mv.order_line_id.price_unit
#                                price_currency_id_x = mv.order_id.pricelist_id.currency_id.id
#
#                        if po_id_x in po_id_temp:
#                            taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes_x)
#
#                            move_vals = {
#                                         'name': po_name_x + ': ' + (pol_name_x or ''),
#                                         'picking_id': picking_create,
#                                         'product_id': product_id_x,
#                                         'product_qty': product_qty_x,
#                                         'product_uom': product_uom_x,
#                                         'product_uos': product_uom_x,
#                                         'date': date_x or time.strftime('%Y-%m-%d'),
#                                         'date_expected': date_expected_x or time.strftime('%Y-%m-%d'),
#                                         'location_id': location_id_x,
#                                         'location_dest_id': location_dest_id_x,
#                                         'address_id': temp['shipping_address_id'],
#                                         'move_dest_id': move_dest_id_x,
#                                         'state': 'assigned',
#                                         'purchase_line_id': temp['po_line_id'],
#                                         'company_id': company_id_x,
#                                         'price_unit': price_unit_x,
#                                         'price_currency_id': price_currency_id_x,
#                                         'taxes_id': [(6,0,taxes_ids)],
#                                         }
#                            stock_move_obj.create(cr, uid, move_vals)
#                        else:
#                            po_id_temp.append(po_id_x)
#                            supplier_id_x = temp['supplier_id']
#                            supplier_branch_id_x = temp['supplier_branch_id']
#                            shipping_address_id_x = temp['shipping_address_id']
#                            pricelist_id_x = temp['pricelist_id']
#                            fiscal_position_id_x = temp['fiscal_position_id']
#                            po_line_id_x = temp['po_line_id']
#                            if supplier_id_x == supplier_id and \
#                                supplier_branch_id_x == supplier_branch_id and \
#                                shipping_address_id_x == shipping_address_id and \
#                                pricelist_id_x == pricelist_id and \
#                                fiscal_position_id_x == fiscal_position_id:
#                                cr.execute('insert into purchase_order_picking_rel (order_id,picking_id) values (%s,%s)', (po_id_x, picking_create))
#                                taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes_x)
#
#                                move_vals = {
#                                             'name': po_name_x + ': ' + (pol_name_x or ''),
#                                             'picking_id': picking_create,
#                                             'product_id': product_id_x,
#                                             'product_qty': product_qty_x,
#                                             'product_uom': product_uom_x,
#                                             'product_uos': product_uom_x,
#                                             'date': date_x or time.strftime('%Y-%m-%d'),
#                                             'date_expected': date_expected_x or time.strftime('%Y-%m-%d'),
#                                             'location_id': location_id_x,
#                                             'location_dest_id': location_dest_id_x,
#                                             'address_id': shipping_address_id_x,
#                                             'move_dest_id': move_dest_id_x,
#                                             'state': 'assigned',
#                                             'purchase_line_id': temp['po_line_id'],
#                                             'company_id': company_id_x,
#                                             'price_unit': price_unit_x,
#                                             'price_currency_id': price_currency_id_x,
#                                             'taxes_id': [(6,0,taxes_ids)],
#                                             }
#                                stock_move_obj.create(cr, uid, move_vals)
#                            else:
#                                supplier_id = temp['supplier_id']
#                                supplier_branch_id = temp['supplier_branch_id']
#                                shipping_address_id = temp['shipping_address_id']
#                                pricelist_id = temp['pricelist_id']
#                                fiscal_position_id = temp['fiscal_position_id']
#                                po_line_id = temp['po_line_id']
#                                supplier_val = supplier_id and res_partner_obj.browse(cr, uid, supplier_id, context=context) or False
#                                addr = supplier_id and res_partner_obj.address_get(cr, uid, [supplier_id], ['delivery', 'invoice', 'contact'])
#
#                                for mv in move_ids:
#                                    if mv.order_line_id.id == po_line_id:
#                                        po_name = mv.order_id.name
#                                        po_id = mv.order_id.id
#                                        if mv.order_id.invoice_method == 'picking':
#                                            invoice_state = '2binvoiced'
#                                        else:
#                                            invoice_state = 'none'
#                                        company_id = mv.order_id.company_id.id
#                                        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, mv.order_line_id.taxes_id))
#                                        pol_name = mv.order_line_id.name
#                                        product_id = mv.order_line_id.product_id.id
#                                        product_qty = mv.qty_order
#                                        product_uom = mv.order_line_id.product_uom.id
#                                        date = mv.order_line_id.estimated_time_departure
#                                        date_expected = mv.order_line_id.estimated_time_arrive
#                                        location_id = mv.order_id.partner_id.property_stock_supplier.id
#                                        location_dest_id = mv.location_dest_id.id
#                                        move_dest_id = mv.order_line_id.move_dest_id.id
#                                        price_unit = mv.order_line_id.price_unit
#                                        price_currency_id = mv.order_id.pricelist_id.currency_id.id
#                                sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
#                                picking_vals = {
#                                                'name': sequence,
#                                                'date': generated.incoming_date or time.strftime('%Y-%m-%d'),
#                                                'do_date': generated.do_date or time.strftime('%Y-%m-%d'),
#                                                'type': 'in',
#                                                'state': 'draft',
#                                                'invoice_state': invoice_state,
#                                                'company_id': company_id,
#                                                'pricelist_id': pricelist_id,
#                                                'partner_order_id' : addr and addr['contact'] or False,
#                                                'partner_shipping_id' : shipping_address_id,
#                                                'partner_invoice_id' : addr and addr['invoice'] or False,
#                                                'partner_id': supplier_id,
#                                                'partner_child_id': supplier_branch_id,
#                                                'ship_method_id' : supplier_val and supplier_val.ship_method_id and supplier_val.ship_method_id.id or False,
#                                                'fob_id' : supplier_val and supplier_val.fob_id and supplier_val.fob_id.id or False,
#                                                'sale_term_id' : supplier_val and supplier_val.sale_term_id and supplier_val.sale_term_id.id or False,
#                                                'fiscal_position' : fiscal_position_id,
#                                                'invoice_date' : generated.invoice_date,
#                                                'invoice_no' : generated.invoice_no,
#                                                'ref_no' : generated.ref_no,
#                                                'country_org_id' : generated.country_org_id.id,
#                                                'country_des_id' : generated.country_des_id.id,
#                                                'note' : generated.desc,
#                                                }
#                                picking_create = stock_picking_obj.create(cr, uid, picking_vals)
#                                newinv.append(picking_create)
#                                cr.execute('insert into purchase_order_picking_rel (order_id,picking_id) values (%s,%s)', (po_id, picking_create))
#                                fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
#                                taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
#                                move_vals = {
#                                             'name': po_name + ': ' + (pol_name or ''),
#                                             'picking_id': picking_create,
#                                             'product_id': product_id,
#                                             'product_qty': product_qty,
#                                             'product_uom': product_uom,
#                                             'product_uos': product_uom,
#                                             'date': date or time.strftime('%Y-%m-%d'),
#                                             'date_expected': date_expected or time.strftime('%Y-%m-%d'),
#                                             'location_id': location_id,
#                                             'location_dest_id': location_dest_id,
#                                             'address_id': shipping_address_id,
#                                             'move_dest_id': move_dest_id,
#                                             'state': 'assigned',
#                                             'purchase_line_id': po_line_id,
#                                             'company_id': company_id,
#                                             'price_unit': price_unit,
#                                             'price_currency_id': price_currency_id,
#                                             'taxes_id': [(6,0,taxes_ids)],
#                                             }
#                                stock_move_obj.create(cr, uid, move_vals)
#            for sp in newinv:
#                wf_service.trg_validate(uid, 'stock.picking', sp,
#                    'button_confirm', cr)
#                wf_service.trg_write(uid, 'stock.picking', sp, cr)
#        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree4')
#        id = result and result[1] or False
#        result = act_obj.read(cr, uid, [id], context=context)[0]
#        result['domain'] = "[('id','in', ["+','.join(map(str,newinv))+"])]"
#        result['context'] = "{'search_default_available':0}"
#        return result

    def _prepare_picking(self, cr, uid, generated, po_vals, context=None):
        res_partner_obj = self.pool.get('res.partner')
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
        if po_vals.invoice_method == 'picking':
            invoice_state = '2binvoiced'
        else:
            invoice_state = 'none'

        addr = po_vals.partner_id and res_partner_obj.address_get(cr, uid, [po_vals.partner_id.id], ['delivery', 'invoice', 'contact'])
        partner_val = po_vals.partner_id or False

        picking_vals = {
                        'name': sequence,
                        'invoice_state': invoice_state,
                        'type': 'in',
                        'state': 'draft',
                        'date': generated.incoming_date or time.strftime('%Y-%m-%d'),
                        'do_date': generated.do_date or time.strftime('%Y-%m-%d'),
                        'company_id': (po_vals.company_id and po_vals.company_id.id) or False,
                        'pricelist_id': (po_vals.pricelist_id and po_vals.pricelist_id.id) or False,
                        'partner_order_id' : addr and addr['contact'] or False,
                        'partner_invoice_id' : addr and addr['invoice'] or False,
                        'partner_shipping_id' : (po_vals.partner_shipping_id and po_vals.partner_shipping_id.id) or False,
                        'partner_id': (po_vals.partner_id and po_vals.partner_id.id) or False,
                        'partner_child_id': (po_vals.partner_child_id and po_vals.partner_child_id.id) or False,
                        'ship_method_id' : (partner_val and partner_val.ship_method_id and partner_val.ship_method_id.id) or False,
                        'fob_id' : (partner_val and partner_val.fob_id and partner_val.fob_id.id) or False,
                        'sale_term_id' : (partner_val and partner_val.sale_term_id and partner_val.sale_term_id.id) or False,
                        'fiscal_position' : (po_vals.fiscal_position and po_vals.fiscal_position.id) or False,
                        'invoice_date' : generated.invoice_date,
                        'invoice_no' : generated.invoice_no,
                        'ref_no' : generated.ref_no,
                        'country_org_id' : generated.country_org_id.id,
                        'country_des_id' : generated.country_des_id.id,
                        'note' : generated.desc,
                        }
        return picking_vals

    def _prepare_stock_move(self, cr, uid, moves, picking_id, context=None):
        res_partner_obj = self.pool.get('res.partner')
        account_tax_obj = self.pool.get('account.tax')
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        taxes = account_tax_obj.browse(cr, uid, map(lambda x: x.id, moves.order_line_id.taxes_id))
        fpos = moves.order_id.fiscal_position or False
        taxes_ids = fiscal_position_obj.map_tax(cr, uid, fpos, taxes)

        move_vals = {
             'name': moves.order_id.name + ': ' + (moves.order_line_id.name or ''),
             'picking_id': picking_id,
             'product_id': moves.order_line_id.product_id.id,
             'product_qty': moves.qty_order,
             'product_uom': moves.order_line_id.product_uom.id,
             'product_uos': moves.order_line_id.product_uom.id,
             'date': moves.order_line_id.estimated_time_departure or time.strftime('%Y-%m-%d'),
             'date_expected': moves.order_line_id.estimated_time_arrive or time.strftime('%Y-%m-%d'),
             'location_id': moves.order_id.partner_id.property_stock_supplier.id,
             'location_dest_id': moves.location_dest_id.id,
             'purchase_line_id': moves.order_line_id.id,
             'company_id': (moves.order_id.company_id and moves.order_id.company_id.id) or False,
             'price_unit': moves.order_line_id.price_unit,
             'price_currency_id': moves.order_id.pricelist_id.currency_id.id,
             'state': 'assigned',
             'taxes_id': [(6,0,taxes_ids)],
             'address_id': (moves.order_id.partner_shipping_id and moves.order_id.partner_shipping_id.id) or False,
             'move_dest_id': moves.order_line_id.move_dest_id.id,
             }
        return move_vals

    def generated_do(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        assert len(ids) == 1
        picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        newinv = []
        picking_group = {}

        generated = self.browse(cr, uid, ids[0], context=context)
        move_ids = generated.incoming_lines_ids
        if move_ids:
            for moves in move_ids:
                if moves.qty_order < 1:
                    continue
                po_vals = moves.order_id
                if (str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False)) in picking_group:
                    picking_id = picking_group[(str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False))]
                else:
                    picking_vals = self._prepare_picking(cr, uid, generated, po_vals, context=context)
                    picking_id = picking_obj.create(cr, uid, picking_vals, context=context)
                    newinv.append(picking_id)
                    cr.execute('insert into purchase_order_picking_rel (order_id,picking_id) values (%s,%s)', (moves.order_id.id, picking_id))

                    picking_group[(str(po_vals.partner_id.id) + '--' + str(po_vals.partner_child_id.id)+ '--' + str(po_vals.partner_shipping_id.id) + '--' + str(po_vals.pricelist_id.id) + '--' + str((po_vals.fiscal_position and po_vals.fiscal_position.id) or False))] = picking_id
                if moves.order_line_id.state == 'cancel':
                    continue

                vals = self._prepare_stock_move(cr, uid, moves, picking_id, context=context)
                if vals:
                    stock_move_id = stock_move_obj.create(cr, uid, vals, context=context)

            for sp in newinv:
                wf_service.trg_validate(uid, 'stock.picking', sp,
                    'button_confirm', cr)
                wf_service.trg_write(uid, 'stock.picking', sp, cr)
        result = mod_obj.get_object_reference(cr, uid, 'stock', 'action_picking_tree4')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', ["+','.join(map(str,newinv))+"])]"
        result['context'] = "{'search_default_available':0}"
        return result

purchase_make_incoming()

class incoming_lines(osv.osv_memory):
    _name = 'incoming.lines'
    _description = 'Incoming Lines'

    _columns = {
        'spq': fields.float('SPQ', help="Standard Packaging Qty", readonly=True),
        'wizard_id': fields.many2one('purchase.make.incoming', 'Generated Incoming(s)', ondelete='cascade',),
        'order_id' : fields.many2one('purchase.order', 'Order', ondelete='cascade',),
        'order_line_id' : fields.many2one('purchase.order.line', 'Order Line', ondelete='cascade', required=True,),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True,),
        'product_uom_qty': fields.float('Qty (Purchase Order)', readonly=True,),
        'product_uom': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_delivery': fields.float('has generate Qty', readonly=True),
        'product_uom2': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'qty_order': fields.float('Qty (Incoming Shipment)',),
        'uom_id': fields.many2one('product.uom', 'UoM', readonly=True, ondelete='cascade',),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', readonly=True, help="Location where the system will stock the finished products."),
    }

    def onchange_order_id(self, cr, uid, ids ,purchase_order_id, purchase_order_line_id, product_id, location_dest_id, context={}):

        purchase_order_line_obj = self.pool.get("purchase.order.line")
        purchase_order_obj = self.pool.get("purchase.order")
        product_uom_obj = self.pool.get("product.uom")
        stock_move_obj = self.pool.get("stock.move")
        sale_allocated_obj = self.pool.get("sale.allocated")
        product_product_obj = self.pool.get("product.product")
        res = {}
        res['value'] = {}
        pol_ids = []
        if not purchase_order_id:
            return {}

        purchase_order_line_ids = purchase_order_line_obj.search(cr, uid, [('product_id','=',product_id),('location_dest_id','=',location_dest_id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')])
        if purchase_order_line_ids:
            for val in purchase_order_line_ids:
                pol = purchase_order_line_obj.browse(cr, uid, val, context=context)

                qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, pol.product_id.uom_id.id)
                sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
                qty_allocated = 0.00
                qty_received = 0.00
                incoming_qty = 0.00
                if sale_allocated_ids:
                    for val2 in sale_allocated_ids:
                        qty_allocated = qty_allocated + val2.quantity
                        qty_received = qty_received + val2.received_qty
        #        if pol.id == 46:
        #            raise osv.except_osv(_('Debug !'), _(str(qty_allocated) + '----' + '' + '----' + ''))

                if qtyp > 0:
                    stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
                    if stock_move_ids:
                        for stock_move_id in stock_move_ids:
                            stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                            incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, pol.product_id.uom_id.id)
                    if qtyp - (incoming_qty - qty_received) - qty_allocated > 0:
                        pol_ids.append(val)

        pol_ids = sorted(set(pol_ids))
        po_ids = []
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

        for o in pol_ids:
            pol2 = purchase_order_line_obj.browse(cr, uid, o, context=context)
            po_ids.append(pol2.order_id.id)
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

        po_ids = sorted(set(po_ids))

        res['domain'] = {'purchase_order_id': [('id','in',po_ids)]}

        if purchase_order_id not in po_ids:
            res['value'].update({'purchase_order_id': False, 'purchase_order_line_id': False})
            res['warning'] = {'title': _('Warning'), 'message': _('The selected Purchase Order is not belong to Product ' + str(product_product_obj.browse(cr, uid, product_id, context=context).name) + ' !')}
            return res

        if purchase_order_line_id:
            pol3 = purchase_order_line_obj.browse(cr, uid, purchase_order_line_id, context=context)
            if pol3.order_id.id != purchase_order_id:
                res['value'].update({'purchase_order_line_id': False})
#                res['warning'] = {'title': _('Warning'), 'message': _('The selected Purchase Order Line is not belong to Purchase Order ' + str(purchase_order_obj.browse(cr, uid, purchase_order_id, context=context).name) + ' !')}
            return res
#        raise osv.except_osv(_('Debug !'), _(str(pol_ids) + '----' + '' + '----' + ''))

#        res['domain'] = {'product_id': [('id','in',product_ids)]}
        return res

    def onchange_qty_order(self, cr, uid, ids, product_id, product_uom_qty, product_uom_id, qty_delivery, product_uom2,
            qty_order, uom_id, spq, order_id, context=None):
        res= {}
        product_uom_obj = self.pool.get('product.uom')
        product_product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        spq_approve = False
        if order_id:
            spq_approve = self.pool.get('purchase.order').browse(cr, uid, order_id, context=context).spq_approve
        product_uom = product_uom_obj.browse(cr, uid, product_uom2, context=context)
        res['value'] = {'qty_order': qty_order or 0.0, 'uom_id' : uom_id or False}
        res['domain'] = {'uom_id': [('category_id','=',product_product.uom_id.category_id.id)]}
        if not uom_id:
            return res
        qty_sale = product_uom_obj._compute_qty(cr, uid, product_uom_id, product_uom_qty, product_product.uom_id.id)
        qty_delivery = product_uom_obj._compute_qty(cr, uid, product_uom2, qty_delivery, product_product.uom_id.id)
        qty_order = product_uom_obj._compute_qty(cr, uid, uom_id, qty_order, product_product.uom_id.id)
        if qty_order > 0:
            if spq_approve == False and qty_order%spq != 0:
                qty_order = 0
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
                if qty_order > qty_sale - qty_delivery:
                    if 'warning' in res:
                        if 'message' in res['warning']:
                            message = res['warning']['message']
                            message = message + '\n & \n The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                            res['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'The Qty entered cannot more than ' + str(qty_sale - qty_delivery) + ' ' + product_uom.name
                                   }
                        res['warning'] = warning
                    qty_order = 0.00
        else:
            qty_order = 0.00
        res['value'].update({'qty_order': qty_order})
        return res

incoming_lines()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
