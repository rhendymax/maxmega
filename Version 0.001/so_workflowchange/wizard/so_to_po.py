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

class so_to_po(osv.osv_memory):
    _name = 'so.to.po'
    _description = 'Convert To PO'

    def _prepare_po_value(self, cr, uid, wizard_id, sale_id, partner_child_id,
                          partner_id, pricelist_id, moves, qty,
                          price_unit, context=None):


        order_line_vals = {
            'wizard_id': wizard_id,
            'sale_id': sale_id,
            'partner_child_id': partner_child_id,
            'partner_id': partner_id,
            'pricelist_id' : pricelist_id,
            'pricelist_id2' : pricelist_id,
            'product_id': moves.product_id.id,
            'quantity': qty,
            'real_quantity': qty,
            'product_uom': moves.uom_id.id,
            'price_unit': price_unit,
            'move_id': moves.move_id.id,
            'quantity_order': qty,
            'original_request_date': time.strftime('%Y-%m-%d'),
            'location_dest_id' : moves.move_id.location_id.id,
        }

        return order_line_vals

    def do_refresh(self, cr, uid, ids, context=None):
#Declaration
###############################
        so_to_po_obj = self.pool.get('so.to.po')
        po_value_obj = self.pool.get('po.value')
        wizard_stock_view_obj = self.pool.get('wizard.stock.view')
        fifo_product_detail_obj = self.pool.get('fifo.product.detail')
        so_po_line_obj = self.pool.get('so.po.line')
        product_supplier_obj = self.pool.get('product.supplier')
        product_supplier_price_obj = self.pool.get('product.supplier.price')
        res_company_obj = self.pool.get('res.company')
        product_pricelist_obj = self.pool.get('product.pricelist')
        product_product_obj = self.pool.get('product.product')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')
        currency_obj = self.pool.get('res.currency')
        partner_obj = self.pool.get('res.partner')
##############################


##############################
        line_vals = []
        line_vals_qty_order = {}


        prod_vals = []
        prod_vals_qty_onhand_free = {}
        prod_vals_qty_incoming_free = {}

        prod_vals2 = []
        product_supplier_id = []
        move_id_vals = []
##############################
        po_value_ids = po_value_obj.search(cr, uid, [('wizard_id', '=', ids[0])])
        so_to_po = self.browse(cr, uid, ids[0], context=context)
        partial_product_detail_ids = so_to_po.product_detail_ids
        fifo_product = so_to_po.fifo_product_detail_ids

        for wizard_stock in so_to_po.wizard_stock_view_ids:
            inputplori = 'p' + str(wizard_stock.product_id.id) + 'l' + str(wizard_stock.move_id.location_id.id)
            qty_order = wizard_stock.qty_order

            if inputplori in prod_vals:
#                raise osv.except_osv(_('Debug!'), _('test2' + str(wizard_stock.onhand_allocated_qty)))
                qty_onhand = 0.00
                qty_incoming_un = 0.00
                for pd in partial_product_detail_ids:
                    if pd.location_id.id == wizard_stock.move_id.location_id.id and pd.product_id.id == wizard_stock.product_id.id:
                        qty_onhand = pd.qty_free - prod_vals_qty_onhand_free[inputplori]
                        qty_incoming_un = pd.qty_incoming_non_booked
                allocated_onhand_qty = 0.00
                if so_to_po.allocated_onhand_all == True:
                    allocated_onhand_qty = qty_onhand
                else:
                    allocated_onhand_qty = wizard_stock.onhand_allocated_qty

                if allocated_onhand_qty > qty_onhand:
                    allocated_onhand_qty = qty_onhand

                if allocated_onhand_qty > qty_order:
                    allocated_onhand_qty = qty_order
                allocated_qty = 0.00
                if so_to_po.allocated_all == True:
                    allocated_qty = qty_incoming_un
                else:
                    allocated_qty = wizard_stock.allocated_qty
                
                qty_incoming_un2 = qty_incoming_un - prod_vals_qty_incoming_free[inputplori]

                if allocated_qty > qty_incoming_un2:
                    allocated_qty = qty_incoming_un2


                if allocated_qty > (qty_order - allocated_onhand_qty):
                    allocated_qty = qty_order - allocated_onhand_qty

                qty_order = qty_order - (allocated_onhand_qty + allocated_qty)
                wizard_stock_view_obj.write(cr, uid, wizard_stock.id, {
                                                                   'onhand_allocated_qty': allocated_onhand_qty,
                                                                   'allocated_qty': allocated_qty
                                                                   })

                hasil_onhand = prod_vals_qty_onhand_free[inputplori] + allocated_onhand_qty

                prod_vals_qty_onhand_free[inputplori] = prod_vals_qty_onhand_free[inputplori] + allocated_onhand_qty
                prod_vals_qty_incoming_free[inputplori] = prod_vals_qty_incoming_free[inputplori] + allocated_qty
            else:
                prod_vals.append(inputplori)
                qty_onhand = 0.00
                qty_incoming_un = 0.00
                for pd in partial_product_detail_ids:
                    if pd.location_id.id == wizard_stock.move_id.location_id.id and pd.product_id.id == wizard_stock.product_id.id:
                        qty_onhand = pd.qty_free
                        qty_incoming_un = pd.qty_incoming_non_booked
                allocated_onhand_qty = 0.00
                if so_to_po.allocated_onhand_all == True:
                    allocated_onhand_qty = qty_onhand
                else:
                    allocated_onhand_qty = wizard_stock.onhand_allocated_qty

                if allocated_onhand_qty > qty_onhand:
                    allocated_onhand_qty = qty_onhand

                if allocated_onhand_qty > qty_order:
                    allocated_onhand_qty = qty_order

                allocated_qty = 0.00
                if so_to_po.allocated_all == True:
                    allocated_qty = qty_incoming_un
                else:
                    allocated_qty = wizard_stock.allocated_qty

                if allocated_qty > qty_incoming_un:
                    allocated_qty = qty_incoming_un
    
                if allocated_qty > (qty_order - allocated_onhand_qty):
                    allocated_qty = qty_order - allocated_onhand_qty

                qty_order = qty_order - (allocated_onhand_qty + allocated_qty)

                wizard_stock_view_obj.write(cr, uid, wizard_stock.id, {
                                                                   'onhand_allocated_qty': allocated_onhand_qty,
                                                                   'allocated_qty': allocated_qty
                                                                   })
                prod_vals_qty_onhand_free[inputplori] = allocated_onhand_qty
                prod_vals_qty_incoming_free[inputplori] = allocated_qty

            line_vals.append(wizard_stock.move_id.id)
            line_vals_qty_order[wizard_stock.move_id.id] = qty_order



        for po_value in po_value_obj.browse(cr, uid, po_value_ids, context=context):
            po_value_obj.unlink(cr, uid, po_value.id, context=context)
        for wi_st in so_to_po.wizard_stock_view_ids:
            inputplori2 = 'p' + str(wi_st.product_id.id) + 'l' + str(wi_st.move_id.location_id.id)
            if inputplori2 not in prod_vals2:
                prod_vals2.append(inputplori2)
                if inputplori2 in prod_vals:
                    fifo_qty = prod_vals_qty_onhand_free[inputplori2]
                else:
                    fifo_qty = 0.00
                for fifo_prod in fifo_product:
                    if fifo_prod.location_id.id == wi_st.move_id.location_id.id and fifo_prod.product_id.id == wi_st.product_id.id:
                        fifo_input = 0.00
                        if fifo_qty > fifo_prod.qty_onhand_free:
                            fifo_qty = fifo_qty - fifo_prod.qty_onhand_free
                            fifo_input = fifo_prod.qty_onhand_free
                        else:
                            fifo_input = fifo_qty
                            fifo_qty = 0.00
                        fifo_product_detail_obj.write(cr, uid, fifo_prod.id, {
                                                                              'onhand_allocated_qty': fifo_input,
                                                                              })



        for wi_st2 in so_to_po.wizard_stock_view_ids:
            if wi_st2.move_id.id in line_vals:
                qty_order2 = line_vals_qty_order[wi_st2.move_id.id]
            else:
                qty_order2 = 0.00
            if qty_order2 > 0:

                product_supplier = product_supplier_obj.browse(cr, uid, wi_st2.product_supplier_id.id)
                partner_child_id = product_supplier.partner_child_id.id
                partner_id = product_supplier.partner_child_id.partner_id.id
                supplier = partner_obj.browse(cr, uid, partner_id)
                pricelist_id = supplier.property_product_pricelist_purchase.id


                product_supplier_price_ids = product_supplier_price_obj.search(cr, uid, [('product_supplier_id','=',product_supplier.id),('effective_date','<=',time.strftime('%Y-%m-%d'))], order='effective_date DESC')
                product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, product_supplier_price_ids[0], context=context)
                company = res_company_obj.browse(cr, uid, res_company_obj._company_default_get(cr, uid, 'purchase.order', context=context), context=context)
                ptype_src = company.currency_id.id
                currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id
                product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',qty_order)], order='qty DESC')
                if product_supplier_upper_limit_id:
                    product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                    price = currency_obj.compute(cr, uid, product_supplier.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
                else:
                    price = currency_obj.compute(cr, uid, product_supplier.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
                price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                price = product_product_obj.round_p(cr, uid, price, 'Purchase Price',)
                po_value_vals = self._prepare_po_value(cr, uid, ids[0], so_to_po.sale_id.id, partner_child_id,
                                                       partner_id, pricelist_id, wi_st2, qty_order2,
                                                       price, context=context)
                po_value_obj.create(cr, uid, po_value_vals,context=context)
        return True

    def do_partial(self, cr, uid, ids, context=None):

        assert len(ids) == 1, 'Partial picking processing may only be done one at a time'

#Declaration
#############################################

        purchase_sequences_obj = self.pool.get('purchase.sequences')
        obj_sequence = self.pool.get('ir.sequence')

        purchase_order_obj = self.pool.get('purchase.order')
        purchase_order_line_obj = self.pool.get('purchase.order.line')

        sale_order_obj = self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')
        sale_allocated_obj =  self.pool.get('sale.allocated')

        stock_move_obj = self.pool.get('stock.move')

        currency_obj = self.pool.get('res.currency')
        partner_obj = self.pool.get('res.partner')
        res_company_obj = self.pool.get('res.company')

        product_product_obj = self.pool.get('product.product')
        product_supplier_price_obj = self.pool.get('product.supplier.price')
        product_uom_obj = self.pool.get('product.uom')
        product_pricelist_obj = self.pool.get('product.pricelist')
        product_supplier_upper_limit_obj = self.pool.get('product.supplier.upper.limit')

        product_supplier_obj = self.pool.get('product.supplier')
        move_allocated_control_obj = self.pool.get('move.allocated.control')

        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')
#############################################

        partial = self.browse(cr, uid, ids[0], context=context)

        wizard_ids = partial.wizard_stock_view_ids
        partial_po_ids = partial.po_value_ids
        fifo_product = partial.fifo_product_detail_ids
        partial_product_detail_ids = partial.product_detail_ids

        po_vals = []
        po_lines = {}

#################################################3
        line_vals = []
        line_vals_qty_order = {}
        line_vals_onhand = {}
        line_vals_incoming = {}

        prod_vals = []
        prod_vals_qty_onhand_free = {}
        prod_vals_qty_incoming_free = {}

        fifo_vals = []
        fifo_vals_qty_input = {}

        po_vals = []
        po_vals_qty_input = {}

        partner_child_id_vals = []
###############################################

##############################################
        for wizard in wizard_ids:
            partner_child_id_vals.append(wizard.product_supplier_id.partner_child_id.id)
            sale_order_line_obj.button_confirm(cr, uid, wizard.move_id.id, context)
            inputplori = 'p' + str(wizard.product_id.id) + 'l' + str(wizard.move_id.location_id.id)
            qty_order = wizard.qty_order
            if inputplori in prod_vals:

                qty_onhand = 0.00
                qty_incoming_un = 0.00
                for pd in partial_product_detail_ids:
                    if pd.location_id.id == wizard.move_id.location_id.id and pd.product_id.id == wizard.product_id.id:
                        qty_onhand = pd.qty_free - prod_vals_qty_onhand_free[inputplori]
                        qty_incoming_un = pd.qty_incoming_non_booked
                allocated_onhand_qty = 0.00
                if partial.allocated_onhand_all == True:
                    allocated_onhand_qty = qty_onhand
                else:
                    allocated_onhand_qty = wizard.onhand_allocated_qty

                if allocated_onhand_qty > qty_onhand:
                    allocated_onhand_qty = qty_onhand

                if allocated_onhand_qty > qty_order:
                    allocated_onhand_qty = qty_order
                allocated_qty = 0.00
                if partial.allocated_all == True:
                    allocated_qty = qty_incoming_un
                else:
                    allocated_qty = wizard.allocated_qty

                qty_incoming_un2 = qty_incoming_un - prod_vals_qty_incoming_free[inputplori]

                if allocated_qty > qty_incoming_un2:
                    allocated_qty = qty_incoming_un2

                if allocated_qty > (qty_order - allocated_onhand_qty):
                    allocated_qty = qty_order - allocated_onhand_qty

                qty_order = qty_order - (allocated_onhand_qty + allocated_qty)

                prod_vals_qty_onhand_free[inputplori] = prod_vals_qty_onhand_free[inputplori] + allocated_onhand_qty
                prod_vals_qty_incoming_free[inputplori] = prod_vals_qty_incoming_free[inputplori] + allocated_qty

            else:
                prod_vals.append(inputplori)
                qty_onhand = 0.00
                qty_incoming_un = 0.00
                for pd in partial_product_detail_ids:
                    if pd.location_id.id == wizard.move_id.location_id.id and pd.product_id.id == wizard.product_id.id:
                        qty_onhand = pd.qty_free
                        qty_incoming_un = pd.qty_incoming_non_booked
                allocated_onhand_qty = 0.00
                if partial.allocated_onhand_all == True:
                    allocated_onhand_qty = qty_onhand
                else:
                    allocated_onhand_qty = wizard.onhand_allocated_qty

                if allocated_onhand_qty > qty_onhand:
                    allocated_onhand_qty = qty_onhand

                if allocated_onhand_qty > qty_order:
                    allocated_onhand_qty = qty_order

                allocated_qty = 0.00
                if partial.allocated_all == True:
                    allocated_qty = qty_incoming_un
                else:
                    allocated_qty = wizard.allocated_qty

                if allocated_qty > qty_incoming_un:
                    allocated_qty = qty_incoming_un
    
                if allocated_qty > (qty_order - allocated_onhand_qty):
                    allocated_qty = qty_order - allocated_onhand_qty

                qty_order = qty_order - (allocated_onhand_qty + allocated_qty)
                
                prod_vals_qty_onhand_free[inputplori] = allocated_onhand_qty
                prod_vals_qty_incoming_free[inputplori] = allocated_qty

            line_vals.append(wizard.move_id.id)
            line_vals_qty_order[wizard.move_id.id] = qty_order

            sale_onhand_allocated = sale_order_line_obj.browse(cr, uid, wizard.move_id.id, context=context).qty_onhand_allocated
            sale_order_line_obj.write(cr, uid, wizard.move_id.id, {'qty_onhand_allocated': sale_onhand_allocated + allocated_onhand_qty}, context=context)

            line_vals_onhand[wizard.move_id.id] = allocated_onhand_qty
            line_vals_incoming[wizard.move_id.id] = allocated_qty

#allocated move
###############################################
        number = 0
        for wizard2 in wizard_ids:

            if wizard2.move_id.id in line_vals:
                fifo_qty = line_vals_onhand[wizard2.move_id.id]
                allocated_qty = line_vals_incoming[wizard2.move_id.id]
            else:
                fifo_qty = 0.00
                allocated_qty = 0.00
#            raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(fifo_qty, allocated_qty))
            
            for fifo_prod in fifo_product:
                if fifo_prod.location_id.id == wizard2.move_id.location_id.id and fifo_prod.product_id.id == wizard2.product_id.id:
                    fifo_input = 0.00
                    ff_onh = fifo_prod.qty_onhand_free
                    if fifo_prod.id in fifo_vals:
                        qty_f = fifo_vals_qty_input[fifo_prod.id]
                        ff_onh = fifo_prod.qty_onhand_free - qty_f

                    if fifo_qty > ff_onh:
                        fifo_qty = fifo_qty - ff_onh
                        fifo_input = ff_onh
                    else:
                        fifo_input = fifo_qty
                        fifo_qty = 0.00
#                    raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(fifo_input, '00000'))
            
                    if fifo_input > 0:
                        if fifo_prod.id in fifo_vals:
                            fifo_vals_qty_input[fifo_prod.id] = fifo_vals_qty_input[fifo_prod.id] + fifo_input
                        else:
                            fifo_vals.append(fifo_prod.id)
                            fifo_vals_qty_input[fifo_prod.id] = fifo_input

                        move_allocated_control_obj.create(cr, uid, {
                                                                    'move_id': fifo_prod.move_id.id,
                                                                    'int_move_id': fifo_prod.int_move_id.id,
                                                                    'so_line_id': wizard2.move_id.id,
                                                                    'quantity': fifo_input,
                                                                    }, context=context)
##########################################

#allocated incoming
##########################################
            if allocated_qty > 0:
                purchase_order_line_ids = purchase_order_line_obj.browse(cr, uid, purchase_order_line_obj.search(cr, uid, [('product_id','=',wizard2.product_id.id),('location_dest_id','=',wizard2.move_id.location_id.id),('state','<>','done'),('state','<>','draft'),('state','<>','cancel')], order='id ASC'), context=context)
                if purchase_order_line_ids:
                    all_qty = allocated_qty
                    for pol in purchase_order_line_ids:
                        if all_qty > 0:
                            qtyp = product_uom_obj._compute_qty(cr, uid, pol.product_uom.id, pol.product_qty, wizard2.uom_id.id)
                            sale_allocated_ids = sale_allocated_obj.browse(cr, uid, sale_allocated_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('receive','=',False)]), context=context)
                            qty_allocated = 0.00
                            qty_received = 0.00
                            incoming_qty = 0.00
                            if sale_allocated_ids:
                                for val in sale_allocated_ids:
                                    qty_allocated = qty_allocated + val.quantity
                                    qty_received = qty_received + val.received_qty
                            if qtyp > 0:
                                stock_move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',pol.id),('state','=','done')])
                                if stock_move_ids:
                                    for stock_move_id in stock_move_ids:
                                        stock_move = stock_move_obj.browse(cr, uid, stock_move_id, context=context)
                                        incoming_qty = incoming_qty + product_uom_obj._compute_qty(cr, uid, stock_move.product_uom.id, stock_move.product_qty, wizard2.uom_id.id)
#                            raise osv.except_osv(_('Debug!'), _(str(qtyp) + '----' + str(qty_allocated) + '----' + str(incoming_qty)))

                            qtyp = qtyp - (incoming_qty - qty_received) - qty_allocated


                            if pol.id in po_vals:

                                qtyp = qtyp - po_vals_qty_input[pol.id]
                            if qtyp > all_qty:
                                qtyp = all_qty
                            if qtyp > 0:
                                if pol.id in po_vals:
                                    po_vals_qty_input[pol.id] = po_vals_qty_input[pol.id] + fifo_input
                                else:
                                    po_vals.append(pol.id)
                                    po_vals_qty_input[pol.id] = qtyp

                                allocated_vals2 = {
                                    'sale_line_id' : wizard2.move_id.id,
                                    'purchase_line_id': pol.id,
                                    'quantity': qtyp,
                                    'product_uom' : wizard2.uom_id.id,
                                    'product_id' : wizard2.product_id.id,}
                                sale_allocated_obj.create(cr, uid, allocated_vals2, context=context)
                                all_qty = all_qty - qtyp
                        else:
                            break


#        raise osv.except_osv(_('Debug!'), _(str(test_dict) + '----'))
#        test_dict
##########################################

##########################################
        if partner_child_id_vals:
            for pc in sorted(set(partner_child_id_vals)):
                for wizard3 in wizard_ids:
                    if wizard3.product_supplier_id.partner_child_id.id != pc:
                        continue
                    if wizard3.move_id.id in line_vals:
                        qty_order = line_vals_qty_order[wizard3.move_id.id]
                    else:
                        qty_order = 0.00
                    if not qty_order > 0:
                        continue
                    if wizard3.product_supplier_id.partner_child_id.id not in po_vals:
                        po_vals.append(wizard3.product_supplier_id.partner_child_id.id)
                        pricelist_id = wizard3.product_supplier_id.partner_child_id.partner_id.property_product_pricelist_purchase.id
                        fiscal_positionzz = wizard3.product_supplier_id.partner_child_id.partner_id.property_account_position and wizard3.product_supplier_id.partner_child_id.partner_id.property_account_position.id or False

                        purchase_sequences_ids = purchase_sequences_obj.search(cr, uid, [('default_key','=',True)])
                        if not purchase_sequences_ids:
                            raise osv.except_osv(_('Invalid action !'), _('no default purchase sequences found.'))
                        purchase_sequences = purchase_sequences_obj.browse(cr, uid, purchase_sequences_ids[0], context=context)
                        sequence_id = (purchase_sequences.sequence_id and purchase_sequences.sequence_id.id) or False
                        if not sequence_id:
                            raise osv.except_osv(_('Invalid action !'), _('no default sequence found in "' + str(purchase_sequences.name) + '" purchase sequences.'))
                        addr = self.pool.get('res.partner').address_get(cr, uid, [wizard3.product_supplier_id.partner_child_id.partner_id.id], ['delivery', 'invoice', 'contact'])
                        partner_invoice_id = addr['invoice']
                        partner_order_id = addr['contact']
                        partner_shipping_id = addr['delivery']
                        ship_method_id = (wizard3.product_supplier_id.partner_child_id.partner_id.ship_method_id and wizard3.product_supplier_id.partner_child_id.partner_id.ship_method_id.id) or False
                        fob_id = (wizard3.product_supplier_id.partner_child_id.partner_id.fob_id and wizard3.product_supplier_id.partner_child_id.partner_id.fob_id.id) or False
                        sale_term_id =  (wizard3.product_supplier_id.partner_child_id.partner_id.sale_term_id and wizard3.product_supplier_id.partner_child_id.partner_id.sale_term_id.id) or False
            
                        contact_person_ids = []
                        for pc in wizard3.product_supplier_id.partner_child_id.partner_id.contact_person_ids:
                            contact_person_ids.append(pc.id)
                        contact_person_id = (contact_person_ids and contact_person_ids[0]) or False

                        order_val2 = {
                            'purchase_sequences_id': purchase_sequences.id,
                            'origin': wizard3.move_id.order_id.name,
                            'date_order': time.strftime('%Y-%m-%d'),
                            'partner_child_id' : wizard3.product_supplier_id.partner_child_id.id,
                            'partner_child_id2' : wizard3.product_supplier_id.partner_child_id.id,
                            'partner_id' : wizard3.product_supplier_id.partner_child_id.partner_id.id,
                            'partner_id2' : wizard3.product_supplier_id.partner_child_id.partner_id.id,
                            'partner_address_id': self.pool.get('res.partner').address_get(cr, uid, [wizard3.product_supplier_id.partner_child_id.partner_id.id], ['default'])['default'],
                            'warehouse_id': self.pool.get('stock.warehouse').search(cr, uid, [])[0],
                            'location_id': self.pool.get('stock.warehouse').browse(cr, uid, self.pool.get('stock.warehouse').search(cr, uid, [])[0]).lot_input_id.id,
                            'pricelist_id' : pricelist_id,
                            'fiscal_position' : fiscal_positionzz,
                            'state': 'draft',
                            'shipped': 0,
                            'invoice_method': 'picking',
                            'invoiced': 0,
                            'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order', context=context),
                            'partner_order_id' : partner_order_id,
                            'partner_invoice_id' : partner_invoice_id,
                            'partner_shipping_id' : partner_shipping_id,
                            'ship_method_id' : ship_method_id,
                            'fob_id' : fob_id,
                            'buyer_id' : uid,
                            'sale_term_id' : sale_term_id,
                            'contact_person_id' : contact_person_id,
                            }
                        purchase_order_id = purchase_order_obj.create(cr, uid, order_val2, context=context)
                        purchase_order_obj.action_trigger_booked(cr, uid, purchase_order_id, '', context)
                        po_lines[wizard3.product_supplier_id.partner_child_id.id] = purchase_order_id
                    else:
                        purchase_order_id = po_lines[wizard3.product_supplier_id.partner_child_id.id]

                    pricelist_id = wizard3.product_supplier_id.partner_child_id.partner_id.property_product_pricelist_purchase.id
                    supplier = partner_obj.browse(cr, uid, wizard3.product_supplier_id.partner_child_id.partner_id.id)
                    effective_date = time.strftime('%m-%d-%Y')
                    product_supplier_price_ids = product_supplier_price_obj.search(cr, uid, [('product_supplier_id','=',wizard3.product_supplier_id.id),('effective_date','<=', effective_date)], order='effective_date DESC')
                    product_supplier_price_id = product_supplier_price_obj.browse(cr, uid, product_supplier_price_ids[0], context=context)
                    company = res_company_obj.browse(cr, uid, res_company_obj._company_default_get(cr, uid, 'purchase.order', context=context), context=context)
                    ptype_src = company.currency_id.id
                    currency_id = product_pricelist_obj.browse(cr, uid, pricelist_id, context=context).currency_id.id

                    product_supplier_upper_limit_id = product_supplier_upper_limit_obj.search(cr, uid, [('product_supplier_price_id','=',product_supplier_price_id.id),('qty','<=',qty_order)], order='qty DESC')
                    if product_supplier_upper_limit_id:
                        product_supplier_upper_limit = product_supplier_upper_limit_obj.browse(cr, uid, product_supplier_upper_limit_id[0], context=context)
                        price = currency_obj.compute(cr, uid, wizard3.product_supplier_id.currency_id.id, ptype_src, product_supplier_upper_limit.unit_cost, round=False)
                    else:
                        price = currency_obj.compute(cr, uid, wizard3.product_supplier_id.currency_id.id, ptype_src, product_supplier_price_id.unit_cost, round=False)
                    price = currency_obj.compute(cr, uid, ptype_src, currency_id, price, round=False)
                    price = product_product_obj.round_p(cr, uid, price, 'Purchase Price',)
                    qty_in_line_uom = product_uom_obj._compute_qty(cr, uid, wizard3.uom_id.id, qty_order, wizard3.uom_id.id)
                    taxes = account_tax.browse(cr, uid, map(lambda x: x.id, wizard3.product_id.supplier_taxes_id))
                    fiscal_position_id = supplier.property_account_position and supplier.property_account_position.id or False
                    fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
                    taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
#                    raise osv.except_osv(_('Invalid action !'), _(str(taxes_ids)))
                    order_line_vals2 = {
                        'done_savedrecords' : True,
                        'sale_line_id' : wizard3.move_id.id,
                        'name': wizard3.product_id.name,
                        'product_qty': qty_in_line_uom,
                        'date_planned': time.strftime('%Y-%m-%d'),
                        'product_uom' : wizard3.uom_id.id,
                        'product_id' : wizard3.product_id.id,
                        'price_unit': price,#
                        'order_id': purchase_order_id,
                        'taxes_id': [(6,0,taxes_ids)],
                        'state': 'draft',
                        'location_dest_id': wizard3.move_id.location_id.id,
                        'invoiced' : 0,
                        'estimated_time_arrive' : time.strftime('%Y-%m-%d'),
                        'original_request_date2' : time.strftime('%Y-%m-%d'),
                        'original_request_date' : time.strftime('%Y-%m-%d'),
                        'spq' : wizard3.product_id.spq,
                        'moq' : wizard3.product_supplier_id.moq,
                        }

                    purchase_order_line_id = purchase_order_line_obj.create(cr, uid, order_line_vals2, context=context)

                    allocated_vals = {
                        'sale_line_id' : wizard3.move_id.id,
                        'purchase_line_id': purchase_order_line_id,
                        'quantity': qty_in_line_uom,
                        'product_uom' : wizard3.uom_id.id,
                        'product_id' : wizard3.product_id.id,}

                    sale_allocated_obj.create(cr, uid, allocated_vals, context=context)

#############################################

        sale_order_obj.write(cr, uid, context['active_id'], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
        return {'type': 'ir.actions.act_window_close'}


    def do_non_partial(self, cr, uid, ids, context=None):

        assert len(ids) == 1, 'Partial picking processing may only be done one at a time'
        sale_order_obj = self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')
        partial = self.browse(cr, uid, ids[0], context=context)
        wizard_ids = partial.wizard_stock_view_ids
        for wizard in wizard_ids:
            sale_order_line_obj.button_confirm(cr, uid, wizard.move_id.id, context)
        sale_order_obj.write(cr, uid, context['active_id'], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})

        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'allocated_onhand_all': fields.boolean('From On Hand(Allocated All)', help="ticked if want to allocated all the On Hand Free Quantity to this sales order."),
        'allocated_all': fields.boolean('From Incoming(Allocated All)', help="ticked if want to allocated all the Incoming non Allocated Quantity to this sales order."),
        'date': fields.datetime('Date', required=True),
        'po_value_ids' : fields.one2many('po.value', 'wizard_id', 'Purchase Order Detail', readonly=True),
        'wizard_stock_view_ids' : fields.one2many('wizard.stock.view', 'wizard_id', 'Stock Detail View', readonly=True),
        'fifo_product_detail_ids' : fields.one2many('fifo.product.detail', 'wizard_id', 'Fifo Product Detail View', readonly=True),
        'product_detail_ids' : fields.one2many('product.detail', 'wizard_id', 'Product Detail View', readonly=True),
        'sale_id': fields.many2one('sale.order', 'Sale Order', required=True, ondelete='cascade'),
    }

so_to_po()

class wizard_stock_view(osv.osv_memory):
    _name = 'wizard.stock.view'
    _description = 'Stock Detail View'

    def onchange_allocated_qty(self, cr, uid, ids, allocated_qty, spq):
        if allocated_qty > 0:
            if allocated_qty%spq != 0:
                allocated_qty= spq * ((allocated_qty-(allocated_qty%spq))/spq)
        else:
            allocated_qty = 0
        return {'value': {'allocated_qty': allocated_qty}}

    def onchange_onhand_allocated_qty(self, cr, uid, ids, onhand_allocated_qty, spq):
        if onhand_allocated_qty > 0:
            if onhand_allocated_qty%spq != 0:
                onhand_allocated_qty= spq * ((onhand_allocated_qty-(onhand_allocated_qty%spq))/spq)
        else:
            onhand_allocated_qty = 0
        return {'value': {'onhand_allocated_qty': onhand_allocated_qty}}
    
    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Invalid action !'), _('Cannot deleted Stock Detail Record'))
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)

    _columns = {
        'spq': fields.float('SPQ', help="Standard Packaging Qty"),
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True),
        'product_supplier_id':fields.many2one('product.supplier', 'Supplier Branch Name.', invisible=True, ondelete='cascade'),
        'qty_order': fields.float('Qty Order', digits_compute= dp.get_precision('Product UoM'), readonly=True),
        'wizard_id' : fields.many2one('so.to.po', string="Wizard", ondelete='cascade'),
        'onhand_allocated_qty': fields.float('Qty.(On Hand)', digits_compute= dp.get_precision('Product UoM')),
        'allocated_qty': fields.float('Qty.(Incoming)', digits_compute= dp.get_precision('Product UoM')),
        'move_id' : fields.many2one('sale.order.line', "Order Line", ondelete='cascade'),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string='Default UoM', readonly=True),
    }

wizard_stock_view()

class fifo_product_detail(osv.osv_memory):
    _name = 'fifo.product.detail'
    _description = 'Fifo Product Detail'

    _columns = {
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True),
        'wizard_id' : fields.many2one('so.to.po', string="Wizard", ondelete='cascade'),
        'int_move_id': fields.many2one('stock.move', 'int move id',),
        'int_doc_no': fields.char('Int Number', size=64, readonly=True),
        'move_id': fields.many2one('stock.move', 'move id',),
        'document_no': fields.char('Number', size=64, readonly=True),
        'document_date': fields.datetime('Date Done', readonly=True),
        'location_id': fields.many2one('stock.location', 'Location', readonly=True),
        'product_qty': fields.float('Qty On_Hand', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure'),
        'qty_allocated': fields.float('Qty Allocated', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'qty_onhand_free': fields.float('Qty On_Hand Free', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'onhand_allocated_qty': fields.float('Qty.(On Hand)', digits_compute= dp.get_precision('Product UoM')),
    }

fifo_product_detail()

class product_detail(osv.osv_memory):
    _name = 'product.detail'
    _description = 'Product Detail'

    _columns = {
        'product_id': fields.many2one('product.product', 'Supplier Part No', ondelete='cascade', readonly=True),
        'wizard_id' : fields.many2one('so.to.po', string="Wizard", ondelete='cascade'),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string='Default UoM', readonly=True),
        'location_id': fields.many2one('stock.location', 'Location', ondelete='cascade', readonly=True),
        'qty_available' : fields.float('Quantity on Hand', readonly=True),
        'qty_incoming_booked': fields.float('Quantity Incoming Allocated', readonly=True),
        'qty_incoming_non_booked': fields.float('Quantity Incoming Un-Allocated', readonly=True),
        'qty_booked': fields.float('Total SO Quantity', readonly=True),
        'qty_free': fields.float('Quantity On Hand Free', readonly=True),
        'qty_allocated': fields.float('Quantity On Hand Allocated', readonly=True),
        'qty_free_balance': fields.float('Quantity Free Balance', readonly=True),
    }

product_detail()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
