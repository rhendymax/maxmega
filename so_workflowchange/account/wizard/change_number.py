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

class change_number_inv(osv.osv_memory):
    _name = 'change.number.inv'
    _description = 'Change Number'

    def do_validate(self, cr, uid, ids, context=None):
        account_invoice_obj = self.pool.get('account.invoice')
        account_move_obj = self.pool.get('account.move')
        for obj in self.browse(cr, uid, ids, context=context):

            
            move_id = account_invoice_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id and \
                        account_invoice_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id.id or \
                        False
#            raise osv.except_osv(_('Error !'), _(str(context.get(('active_ids'), [])[0])))
            if move_id:
                account_move_obj.write(cr, uid, [move_id], {'name': obj.name}, context=context)
                account_invoice_obj.write(cr, uid, context.get(('active_ids'), []), {'number': obj.name}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'name': fields.char('Number', size=64, required=True),
    }

    def ch_validate(self, cr, uid, ids, context=None):
        account_invoice_obj = self.pool.get('account.invoice')
        account_move_obj = self.pool.get('account.move')
        account_invoice_ids = account_invoice_obj.search(cr, uid, [('state', '=', 'open')])
        if account_invoice_ids:
            for ai_id in account_invoice_ids:
                move_id = False
                ai = account_invoice_obj.browse(cr, uid, ai_id, context=context)
                if ai.ref_no:
                    move_id = ai.move_id and \
                                ai.move_id.id or \
                                False
                    account_move_obj.write(cr, uid, [move_id], {'name': ai.ref_no}, context=context)
                    account_invoice_obj.write(cr, uid, ai.id, {'number': ai.ref_no, 'ref_no': False}, context=context)
#        for obj in self.browse(cr, uid, ids, context=context):
#
#            
#            move_id = account_invoice_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id and \
#                        account_invoice_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id.id or \
#                        False
##            raise osv.except_osv(_('Error !'), _(str(context.get(('active_ids'), [])[0])))
#            if move_id:
#                account_move_obj.write(cr, uid, [move_id], {'name': obj.name}, context=context)
#                account_invoice_obj.write(cr, uid, context.get(('active_ids'), []), {'number': obj.name}, context=context)
        return {'type': 'ir.actions.act_window_close'}

change_number_inv()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
