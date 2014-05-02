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

import netsvc
import time

from osv import osv,fields
from tools.translate import _
import decimal_precision as dp

class return_picking_memory(osv.osv_memory):
    _name = "return.picking.memory"
    _rec_name = 'product_id'
    _columns = {
        'product_id' : fields.many2one('product.product', string="Product", required=True, readonly=True),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'location_dest_id': fields.many2one('stock.location', 'Location',readonly=True, select=True),
        'qty_free': fields.float('Quantity On Hand Free', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'qty_return' : fields.float("Quantity Return", digits_compute=dp.get_precision('Product UoM')),
        'wizard_id' : fields.many2one('return.picking', string="Wizard"),
        'move_id' : fields.many2one('stock.move', "Move"),
    }

    def qty_return_onchange(self, cr, uid, ids, qty, qty_free, qty_return, location, context=None):
        location_ids = []
        res = {}
        if location:
            if qty_return:
                qty_can_return = qty
                if qty_can_return > qty_free:
                    qty_can_return = qty_free
                if qty_return > qty_can_return:
                    warning = {
                               'title': _('Configuration Error !'),
                               'message' : 'The Qty Return Entered cannot be more than ' + str(qty_can_return)
                               }
                    res['warning'] = warning
                    res['value']= {'qty_return': qty_can_return,}
        return res

return_picking_memory()


class return_picking(osv.osv_memory):
    _name = 'return.picking'
    _description = 'Return Picking'

    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        if context is None:
            context = {}
        res = super(return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        pick_obj = self.pool.get('stock.picking')
        product_location_wizard_obj = self.pool.get('product.location.wizard')
        pick = pick_obj.browse(cr, uid, record_id, context=context)

        if pick:
            return_history = self.get_return_history(cr, uid, record_id, context)
            for line in pick.move_lines:
                qty = line.product_qty - return_history[line.id]
                if qty > 0:
                    qty_free = 0.00
                    qty_return = qty
                    location_dest_id = False
                    if pick.type=='in':
                        location_dest_id = line.location_dest_id.id
                        res_1 = product_location_wizard_obj.stock_location_get(cr, uid, line.product_id.id, context=context)
                        if res_1:
                            for rs in res_1:
                                if rs['location_id'] == line.location_dest_id.id:
                                    qty_free = rs['qty_free']
                        if qty_return > qty_free:
                            qty_return = qty_free
                    result1.append({'product_id': line.product_id.id,
                                    'location_dest_id' : location_dest_id,
                                    'qty_free' : qty_free,
                                    'quantity': qty,
                                    'qty_return':qty_return,
                                    'move_id':line.id})
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
        return res

    def get_return_history(self, cr, uid, pick_id, context=None):
        """ 
         Get  return_history.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param pick_id: Picking id
         @param context: A standard dictionary
         @return: A dictionary which of values.
        """
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, pick_id, context=context)
        return_history = {}
        for m  in pick.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history

    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """

    
        if context is None:
            context = {} 
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('return.picking.memory')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        new_picking = None
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        date_n = time.strftime('%Y-%m-%d')
        returned_lines = 0
        
#        Create new picking for returned products
        if pick.type=='out':
            new_type = 'in'
            new_picking = pick_obj.copy(cr, uid, pick.id, {'name':'%s->%s' % (self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.return.out'), pick.name),
                    'move_lines':[], 'state':'draft', 'type':new_type, 'created_vals':True,
                    'date':date_cur, 'invoice_state':'none', 'do_date' :date_n, 'allow_copy':True, 'account_invoice_ids': False, 'invoice_no': pick and pick.invoice_no and '%s-RT' % (pick.invoice_no) or False})

            val_id = data['product_return_moves']
            for v in val_id:
                data_get = data_obj.browse(cr, uid, v, context=context)
                mov_id = data_get.move_id.id
                new_qty = data_get.qty_return
                move = move_obj.browse(cr, uid, mov_id, context=context)
                new_location = move.location_dest_id.id
                returned_qty = move.product_qty
                for rec in move.move_history_ids2:
                    returned_qty -= rec.product_qty

                if new_qty:
                    returned_lines += 1
                    new_move=move_obj.copy(cr, uid, move.id, {
                        'sale_line_id': False,
                        'purchase_line_id': False,
                        'product_qty': new_qty,
                        'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id,
                            new_qty, move.product_uos.id),
                        'picking_id':new_picking, 'state':'draft',
                        'location_id':new_location, 'location_dest_id':move.location_id.id,
                        'date':date_cur,})
                    move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]})
            if not returned_lines:
                raise osv.except_osv(_('Warning !'), _("Please specify at least one non-zero quantity!"))
    
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
            pick_obj.force_assign(cr, uid, [new_picking], context)
            pick_obj.action_done2(cr, uid, [new_picking], context)
        
        elif pick.type=='in':
#            raise osv.except_osv(_('xx !'), _("XXX"))
            new_type = 'out'
            new_picking = pick_obj.copy(cr, uid, pick.id, {'name':'%s->%s' % (self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.return.in'), pick.name),
                    'invoice_state':'none', 'move_lines':[], 'state':'draft', 'type':new_type, 'created_vals':True,
                    'date':date_cur, 'account_invoice_ids': False, 'do_date' :date_n, 'allow_copy':True, 'invoice_no': pick and pick.invoice_no and '%s-RT' % (pick.invoice_no) or False})
#            raise osv.except_osv(_('xx !'), _(str(re)))
            val_id = data['product_return_moves']
            for v in val_id:
                data_get = data_obj.browse(cr, uid, v, context=context)
                mov_id = data_get.move_id.id
                new_qty = data_get.qty_return
                move = move_obj.browse(cr, uid, mov_id, context=context)
                new_location = move.location_dest_id.id
                returned_qty = move.product_qty
                for rec in move.move_history_ids2:
                    returned_qty -= rec.product_qty
    

                if new_qty:
                    returned_lines += 1
                    new_move=move_obj.copy(cr, uid, move.id, {
                        'sale_line_id': False,
                        'purchase_line_id': False,
                        'product_qty': new_qty,
                        'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id,
                            new_qty, move.product_uos.id),
                        'picking_id':new_picking, 'state':'draft',
                        'location_id':new_location, 'location_dest_id':move.location_id.id,
                        'date':date_cur,})
                    move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]})
            if not returned_lines:
                raise osv.except_osv(_('Warning !'), _("Please specify at least one non-zero quantity!"))
    
            wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
            pick_obj.force_assign(cr, uid, [new_picking], context)
            pick_obj.action_done2(cr, uid, [new_picking], context)
            
        else:
            raise osv.except_osv(_('Error !'),_(str('this return picking not in GRN or DO')))

        # Update view id in context, lp:702939
        view_list = {
                'out': 'view_picking_out_tree',
                'in': 'view_picking_in_tree',
                'internal': 'vpicktree',
            }
        data_obj = self.pool.get('ir.model.data')
        res = data_obj.get_object_reference(cr, uid, 'stock', view_list.get(new_type, 'vpicktree'))
        context.update({'view_id': res and res[1] or False})
        return {
            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            'name': 'Picking List',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'stock.picking',
            'type':'ir.actions.act_window',
            'context':context,
        }

    _columns = {
        'product_return_moves' : fields.one2many('return.picking.memory', 'wizard_id', 'Moves'),
     }

return_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

