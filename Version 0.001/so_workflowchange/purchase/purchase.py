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

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    def default_get(self, cr, uid, fields, context=None):
#        raise osv.except_osv(_('Error !'), _('This button still in progress mode'))
        if context is None:
            context = {}
        purchase_order_obj = self.pool.get('purchase.order')
        res = super(purchase_order_line, self).default_get(cr, uid, fields, context=context)
        model = context and 'active_model' in context and context.get(('active_model')) or False
        if model == 'purchase.order':
            for lines in purchase_order_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
                if not lines.partner_id:
                    raise osv.except_osv(_('Error !'), _('please select the supplier before adding lines'))
                if 'partner_child_id_parent' in fields:
                    res.update({'partner_child_id_parent': lines.partner_child_id.id})
                if 'company_id' in fields:
                    res.update({'company_id': lines.company_id.id})
                if 'partner_id_parent' in fields:
                    res.update({'partner_id_parent': lines.partner_id.id})
                if 'pricelist_id_parent' in fields:
                    res.update({'pricelist_id_parent': lines.pricelist_id.id})
                if 'date_order_parent' in fields:
                    res.update({'date_order_parent': lines.date_order})
                if 'fiscal_position_id_parent' in fields:
                    res.update({'fiscal_position_id_parent': lines.fiscal_position.id})
                if 'order_id' in fields:
                    res.update({'order_id': lines.id})
        return res

    def _prepare_order_line_move(self, cr, uid, qty, line, date_planned, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name[:250],
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'assigned',
            #'state': 'waiting',
            'note': line.notes,
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0
        }

    def picking_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        sales = set()
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_move(cr, uid, line, False, context)
            if vals:
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%s,%s)', (line.id, inv_id))
                self.write(cr, uid, [line.id], {'invoiced': True})
                sales.add(line.order_id.id)
                create_ids.append(inv_id)
        # Trigger workflow events
        wf_service = netsvc.LocalService("workflow")
        for sale_id in sales:
            wf_service.trg_write(uid, 'sale.order', sale_id, cr)
        return create_ids

    def onchange_product_uom3(self, cr, uid, ids, location_dest_id, qty_allocated_onorder,
                              company_id, partner_child_id,
                              pricelist_id, product_id, qty, uom_id,
                              partner_id, original_request_date=False, 
                              date_order=False, fiscal_position_id=False,
                              date_planned=False, name=False, price_unit=False,
                              notes=False, context=None):
        """
        onchange handler of product_uom.
        """
        uom_id = False
        product_product_obj = self.pool.get('product.product')
        if product_id:
            uom_id = product_product_obj.browse(cr, uid, product_id, context=context).uom_po_id.id
        if not uom_id:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'notes': notes or'', 'product_uom' : uom_id or False}}

        return self.onchange_product_id3(cr, uid, ids, location_dest_id,  qty_allocated_onorder,
                                         company_id, partner_child_id,
                                         pricelist_id, product_id, qty, uom_id,
                                         partner_id, original_request_date, date_order,
                                         fiscal_position_id, date_planned,
                                         name, price_unit, notes, context=context)

    def test(self, cr, uid, ids, location_dest_id, qty_allocated_onorder,
                             company_id, partner_child_id,
                             pricelist_id, product_id, qty, uom_id,
                             partner_id, original_request_date=False, date_order=False,
                             fiscal_position_id=False, date_planned=False,
                             name=False, price_unit=False, notes=False,
                             context=None):
        raise osv.except_osv(_('Invalid action !'), _('Cxxx'))
        return {}

    def onchange_product_id3(self, cr, uid, ids, location_dest_id, qty_allocated_onorder,
                             company_id, partner_child_id,
                             pricelist_id, product_id, qty, uom_id,
                             partner_id, original_request_date=False, date_order=False,
                             fiscal_position_id=False, date_planned=False,
                             name=False, price_unit=False, notes=False,
                             context=None):
        
        product_vals = super(purchase_order_line, self).onchange_product_id2(cr, uid, ids,
                            company_id, partner_child_id,
                            pricelist_id, product_id, qty, uom_id,
                            partner_id, original_request_date, date_order,
                            fiscal_position_id, date_planned,
                            name, price_unit, notes, context=context)
        product_supplier_obj = self.pool.get('product.supplier')
        product_pricelist = self.pool.get('product.pricelist')
        currency_obj = self.pool.get('res.currency')
        product_product_obj = self.pool.get('product.product')
        product_uom_obj = self.pool.get('product.uom')

        product_product = product_product_obj.browse(cr, uid, product_id, context=context)
        if qty_allocated_onorder > 0:
            real_qty = product_uom_obj._compute_qty(cr, uid, uom_id, qty, product_product.uom_id.id)
            if real_qty < qty_allocated_onorder:
                product_vals['warning'] = {'title': _('Warning'), 'message': _('The Qty you entered cannot less than the allocated qty. (allocated qty = '+ str(qty_allocated_onorder) + ' '+ str(product_product.uom_id.name) + '.)')}
                product_vals['value'].update({'product_qty': qty_allocated_onorder})
                product_vals['value'].update({'product_uom':  product_product.uom_id.id})

        if product_id:
            location_ids = []
            default_location_id = False
            product_product2 = product_product_obj.browse(cr, uid, product_id, context=context)
            for loc in product_product2.location_ids:
                location_ids.append(loc.stock_location_id.id)
                if (loc.default_key == True):
                    default_location_id = loc.stock_location_id.id
            if location_dest_id:
                if location_dest_id not in location_ids:
                    if 'warning' in product_vals:
                        if 'message' in product_vals['warning']:
                            message = product_vals['warning']['message']
                            message = message + '\n & \n The Selected Location is not belong to this product.'
                            product_vals['warning'].update({
                                             'message': message,
                                             })
                        else:
                            message = 'The Selected Location is not belong to this product.'
                            product_vals['warning'].update({
                                            'title': _('Configuration Error !'),
                                            'message': message,
                                            })
                    else:
                        warning = {
                                   'title': _('Configuration Error !'),
                                   'message' : 'The Selected Location is not belong to this product.'
                                   }
                        product_vals['warning'] = warning
                    location_dest_id = default_location_id or False
            else:
                location_dest_id = default_location_id


            product_vals['value'].update({'location_dest_id': location_dest_id})
            product_vals['domain'].update({'location_dest_id': [('id','in',location_ids)]})

        return product_vals

    def do_refresh(self, cr, uid, ids, context=None):
        return True

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'allocated_ids':[],})
        return super(purchase_order_line, self).copy_data(cr, uid, id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.qty_allocated_onorder > 0:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a purchase order line which is being allocated \'%s\'!') %(rec.name,))
        return super(purchase_order_line, self).unlink(cr, uid, ids, context=context)

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True


    def action_adding_line(self, cr, uid, ids, context=None):
        self.action_confirm(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def _qty_allocated_onorder(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        sale_allocated_obj = self.pool.get("sale.allocated")
        qty_allocated = 0.00
        for obj in self.browse(cr, uid, ids, context=context):
            for val in obj.allocated_ids:
                qty_allocated = qty_allocated + val.quantity
            res[obj.id] = qty_allocated
        return res

    _columns = {
        'partner_child_id_parent': fields.many2one('res.partner.child', 'Partner Child'),
        'partner_id_parent': fields.many2one('res.partner', 'Customer'),
        'fiscal_position_id_parent': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'pricelist_id_parent': fields.many2one('product.pricelist', 'Pricelist'),
        'date_order_parent': fields.date('Date'),
        'effective_ids': fields.one2many('change.effective.po', 'po_line_id', 'Change Effective History', readonly=True,),
        'qty_allocated_onorder': fields.function(_qty_allocated_onorder, type='float', string='Total Quantity Allocated to Sales Order'),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', required=True, help="Location where the system will stock the finished products."),
        'allocated_ids': fields.one2many('sale.allocated', 'purchase_line_id', 'Purchase Allocated', readonly=True, ondelete='set null'),
    }

purchase_order_line()

class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    def _shipped_rate2(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        res2 = {}
        picking_ids = []
        stock_move_obj = self.pool.get('stock.move')

        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = [0.0,0.0]
            purchase_id = obj.id
            for line in obj.order_line:
                res[purchase_id][1] += line.product_qty or 0.0
                stock_move = stock_move_obj.browse(cr, uid, stock_move_obj.search(cr, uid, [('purchase_line_id','=',line.id),('state','=','done')]), context=context)
                if stock_move:
                    for sm in stock_move:
                        res[purchase_id][0] += sm.product_qty or 0.0
#            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(res[obj.id][0], res[obj.id][1]))
#            if res[obj.id][1] == 0:
#                raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(obj.name, res[obj.id][1]))

            if res[obj.id][0] == 0 or res[obj.id][1] == 0:
                res2[obj.id] = 0.0
            else:
                res2[obj.id] = 100.0 * res[obj.id][0] / res[obj.id][1]

        return res2

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
        'header_po': fields.text('Header'),
        'footer_po': fields.text('Footer'),
        'res_consigning_id': fields.many2one('res.consigning', 'Consigning'),
        'res_note_user_id': fields.many2one('res.note.user', 'Note User'),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True),
        'purchase_sequences_id': fields.many2one('purchase.sequences', 'Sequence', required=True),
        'name': fields.char('Order Reference', size=64, help="unique number of the purchase order,computed automatically when the purchase order is created"),
        'contact_person_id': fields.many2one('contact.person', 'Contact Person'),
        'picking_ids2': fields.many2many('stock.picking', 'purchase_order_picking_rel', 'order_id', 'picking_id', 'Related Picking', readonly=True, help="This is the list of incoming that have been generated for this purchase order. The same purchase order may have been invoiced in several times (by line for example)."),
        'shipped_rate': fields.function(_shipped_rate2, string='Received', type='float'),
        'ship_method_id': fields.many2one('shipping.method','Ship Method', readonly=True),
        'fob_id': fields.many2one('fob.point.key', 'FOB Point Key', select=True, readonly=True,),
        'requisitor_id': fields.many2one('res.users', 'Requisitor', states={'draft': [('readonly', False)]}, select=True, readonly=True),
        'buyer_id': fields.many2one('res.users', 'Buyer', states={'draft': [('readonly', False)]}, select=True, readonly=True),
        'sale_term_id': fields.many2one('sale.payment.term', 'Payment Term', select=True, readonly=True,),
    }

    def onchange_pricelist_id(self, cr, uid, ids, partner_id):
        if partner_id:
            pricelist_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context=None).property_product_pricelist_purchase.id
            return {'value':{'pricelist_id': pricelist_id}}
        return {'value':{'pricelist_id': False}}

    def onchange_partner_id(self, cr, uid, ids, partner_id, partner_id2, partner_child_id, contact_person_id, order_line):
        if order_line:
            partner_id = partner_id2
        result = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id, partner_id2, partner_child_id, order_line)

        if not partner_id:
            return result

        res_partner_obj = self.pool.get('res.partner')
        partner = res_partner_obj.browse(cr, uid, partner_id, context=None)
        contact_person_ids = []
        for pc in partner.contact_person_ids:
            contact_person_ids.append(pc.id)

        if 'domain' in result:
            result['domain'].update({'contact_person_id': [('id', 'in', contact_person_ids)]})
        else:
            result['domain'] = {'contact_person_id': [('id', 'in', contact_person_ids)]}

        if contact_person_id:
            if contact_person_id not in contact_person_ids:
                result['value'].update({'contact_person_id': False})
                if 'warning' in result:
                    if 'message' in result['warning']:
                        mess = result['warning']['message']
                        result['warning'].update({'message': _( mess + '\n & \n' +'The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')})
                    else:
                        result['warning'].update({'message': _('The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')})
                else:
                    result['warning'] = {'title': _('Warning'), 'message': _('The selected Contact Person is not belong to Supplier ' + str(partner.name) + ' !')}
        else:
            if contact_person_ids:
                result['value'].update({'contact_person_id': contact_person_ids[0]})
            else:
                result['value'].update({'contact_person_id': False})

        result['value'].update({'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
                                'fob_id': (partner.fob_id and partner.fob_id.id) or False,
                                'sale_term_id': (partner.sale_term_id and partner.sale_term_id.id) or False,
                                })
        return result

    def create(self, cr, user, vals, context=None):
        if 'purchase_sequences_id' in vals:
            obj_purchase_sequence = self.pool.get('purchase.sequences')
            obj_sequence = self.pool.get('ir.sequence')
            purchase_sequence = obj_purchase_sequence.browse(cr, user, vals['purchase_sequences_id'], context=None)
            seq_id = (purchase_sequence.sequence_id and purchase_sequence.sequence_id.id) or False
            if not seq_id:
                raise osv.except_osv(_('Invalid action !'), _('no default sequence found in "' + str(purchase_sequence.name) + '" purchase sequences.'))

            new_name = obj_sequence.next_by_id(cr, user, seq_id, None)
            vals.update({'name' : new_name,
                     })

        if 'partner_id2' in vals:
            partner_id = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, user, partner_id, context=None)
            vals.update({'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
                         'fob_id' : (partner.fob_id and partner.fob_id.id) or False,
                         'sale_term_id': (partner.sale_term_id and partner.sale_term_id.id) or False,
                         'fiscal_position' : partner.property_account_position.id,
                         })
        if 'order_line' in vals:
            partner_id = ('partner_id2' in vals and vals['partner_id2']) or False
            product_supplier_name = ''
            qty_name = ''
            price_name = ''
            for lines in vals['order_line']:
                product_id = lines[2]['product_id'] or False
                if product_id:
                    product_product = self.pool.get('product.product').browse(cr, user, product_id, context=None)
                    supplier_ids = []
                    for supplierm_ids in product_product.supplierm_ids:
                        supplier_ids.append(supplierm_ids.partner_id2.id)
                    if lines[2]['product_qty'] == 0:
                        qty_name += (str(product_product.name) + ' \n')
                    if lines[2]['price_unit'] == 0:
                        price_name += (str(product_product.name) + ' \n')
                    if partner_id not in supplier_ids:
                        product_supplier_name += (str(product_product.name) + ' \n')
            if product_supplier_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Following Part Number is not matches with the Supplier: \n' + product_supplier_name))
            if qty_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Qty of The Following Part Number is Zero: \n' + qty_name))
            if price_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Price Unit of The Following Part Number is Zero: \n' + price_name))

        new_id = super(purchase_order, self).create(cr, user, vals, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        po_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        partner_id2 = ('partner_id2' in vals and vals['partner_id2']) or (self.pool.get('purchase.order').browse(cr, uid, po_id, context=None).partner_id.id) or False
        if 'partner_id2' in vals:
            partner_id22 = vals['partner_id2']
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id22, context=None)
            vals.update({
                         'ship_method_id' : (partner.ship_method_id and partner.ship_method_id.id) or False,
                         'fob_id' : (partner.fob_id and partner.fob_id.id) or False,
                         'sale_term_id': (partner.sale_term_id and partner.sale_term_id.id) or False,
                         })

        if 'order_line' in vals:
            product_supplier_name = ''
            qty_name = ''
            price_name = ''
            for lines in vals['order_line']:
                if lines[0] == 0:
                    product_id = ('product_id' in lines[2] and lines[2]['product_id']) or False
                    if product_id:
                        product_product = self.pool.get('product.product').browse(cr, uid, product_id, context=None)
                        supplier_ids = []
                        for supplierm_ids in product_product.supplierm_ids:
                            supplier_ids.append(supplierm_ids.partner_id2.id)
                        if lines[2]['product_qty'] == 0:
                            qty_name += (str(product_product.name) + ' \n')
                        if lines[2]['price_unit'] == 0:
                            price_name += (str(product_product.name) + ' \n')
                        if partner_id2 not in supplier_ids:
                            product_supplier_name += (str(product_product.name) + ' \n')

                if lines[0] == 1:
                    product_id_vs2 =  ('product_id' in lines[2] and lines[2]['product_id']) or self.pool.get('purchase.order.line').browse(cr, uid, lines[1], context=None).product_id.id  or False
#                    raise osv.except_osv(_('Debug !'), _('x' + str(self.pool.get('purchase.order.line').browse(cr, uid, lines[1], context=None).product_id.id)))
                    if product_id_vs2:
                        product_product_vs2 = self.pool.get('product.product').browse(cr, uid, product_id_vs2, context=None)
                        supplier_ids_vs2 = []
                        for supplierm_ids_vs2 in product_product_vs2.supplierm_ids:
                            supplier_ids_vs2.append(supplierm_ids_vs2.partner_id2.id)
                        if 'product_qty' in lines[2]:
                            product_qty = lines[2]['product_qty']
                        else:
                            product_qty = -1
                        if product_qty == 0:
                            qty_name += (str(product_product_vs2.name) + ' \n')

                        if 'price_unit' in lines[2]:
                            price_unit = lines[2]['price_unit']
                        else:
                            price_unit = -1
                        if price_unit == 0:
                            price_name += (str(product_product_vs2.name) + ' \n')

                        if partner_id2 not in supplier_ids_vs2:
                            product_supplier_name += (str(product_product_vs2.name) + ' \n')

            if product_supplier_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Following Customer Part No is not matches with the Customer: \n' + product_customer_name))
            if qty_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Qty of The Following Customer Part No is Zero: \n' + qty_name))
            if price_name != '':
                raise osv.except_osv(_('Invalid action !'), _('The Price Unit of The Following Customer Part No is Zero: \n' + price_name))


        return super(purchase_order, self).write(cr, uid, ids, vals, context=context)

    _defaults = {
        'invoice_method': 'picking',
        'buyer_id': lambda self, cr, uid, context: uid,
        'name': '',
    }
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        raise osv.except_osv(_('Error!'), _('cannot duplicate Puchase Order'))
        return super(purchase_order, self).copy(cr, uid, id, default, context)

#    def copy(self, cr, uid, id, default=None, context=None):
#        if not default:
#            default = {}
#        purchase_order_obj = self.pool.get('purchase.order')
#        obj_purchase_sequence = self.pool.get('purchase.sequences')
#        obj_sequence = self.pool.get('ir.sequence')
#        purchase_order_id = purchase_order_obj.browse(cr, uid, id, context=None)
#
#        purchase_sequence = obj_purchase_sequence.browse(cr, uid, purchase_order_id.purchase_sequences_id.id, context=None)
#        seq_id = (purchase_sequence.sequence_id and purchase_sequence.sequence_id.id) or False
#        if not seq_id:
#            raise osv.except_osv(_('Invalid action !'), _('no default sequence found in "' + str(purchase_sequence.name) + '" purchase sequences.'))
#
#        new_name = obj_sequence.next_by_id(cr, uid, seq_id, None)

        default.update({
            'origin':'',
            'picking_ids2':[],
            'name': new_name,
            })

        return super(purchase_order, self).copy(cr, uid, id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            productname = ''
            for line in rec.order_line:
                if line.qty_allocated_onorder > 0:
                    productname = line.name + ", "
            if productname != '':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete a purchase order line which is being allocated \'%s\'!') %(productname,))
        return super(purchase_order, self).unlink(cr, uid, ids, context=context)

    def purchase_confirm2(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error !'),_('You cannot confirm a purchase order without any lines.'))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)
            message = _("Purchase order '%s' is confirmed.") % (po.name,)
            self.log(cr, uid, po.id, message)
#        current_name = self.name_get(cr, uid, ids)[0][1]
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'approved', 'date_approve': fields.date.context_today(self,cr,uid,context=context), 'validator' : uid})

#        raise osv.except_osv(_('Invalid action !'), _(''))
        return True

    def action_cancel_draft2(self, cr, uid, ids, *args):
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state':'draft','shipped':0})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
            wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        for (id,name) in self.name_get(cr, uid, ids):
            message = _("Purchase order '%s' has been set in draft state.") % name
            self.log(cr, uid, id, message)
        for purchase in self.browse(cr, uid, ids):
            for line in purchase.order_line:
                purchase_order_line_obj.action_draft(cr, uid, line.id)
        return True

    def wkf_action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")

        purchase_order_line_obj = self.pool.get('purchase.order.line')
        sale_order_obj = self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')

        for purchase in self.browse(cr, uid, ids, context=context):
            for pick in purchase.picking_ids2:
                if pick.state not in ('draft','cancel'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order!'),
                        _('You must first cancel all receptions related to this purchase order.'))
            for pick in purchase.picking_ids2:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order!'),
                        _('You must first cancel all invoices related to this purchase order.'))
                if inv:
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)

            for line in purchase.order_line:
                if line and line.qty_allocated_onorder > 0:
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order!'),
                        _('You must first cancel all allocated qty related to this purchase order.'))
                if line:
                    purchase_order_line_obj.action_cancel(cr, uid, line.id, context)
        self.write(cr,uid,ids,{'state':'cancel', 'origin':'',})

        for (id, name) in self.name_get(cr, uid, ids):
            wf_service.trg_validate(uid, 'purchase.order', id, 'purchase_cancel', cr)
            message = _("Purchase order '%s' is cancelled.") % name
            self.log(cr, uid, id, message)
        return True

    def action_trigger_booked(self, cr, uid, ids, name, context=None):
        message = _("The purchase order '%s' has been create with draft status.") % (name,)
        self.log(cr, uid, ids, message)
        return True

    def requirement_onchange(self, cursor, user, ids, res_consigning_id, context=None):
        res_consigning_obj = self.pool.get('res.consigning')
        header_po = ''
        if res_consigning_id:
            header_po = res_consigning_obj.browse(cursor, user, res_consigning_id, context=context).note
        return {'value': {'header_po': header_po}}

    def Shipping_onchange(self, cursor, user, ids, res_note_user_id, context=None):
        res_note_user_obj = self.pool.get('res.note.user')
        footer_po = ''
        if res_note_user_id:
            footer_po = res_note_user_obj.browse(cursor, user, res_note_user_id, context=context).note
        return {'value': {'footer_po': footer_po}}

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
