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

class change_payment_no(osv.osv_memory):
    _name = 'change.payment.no'
    _description = 'Change Payment No'

    def do_validate(self, cr, uid, ids, context=None):
        account_voucher_obj = self.pool.get('account.voucher')
        account_move_obj = self.pool.get('account.move')
        for obj in self.browse(cr, uid, ids, context=context):
            move_id = account_voucher_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id and \
                        account_voucher_obj.browse(cr, uid, context.get(('active_ids'), [])[0], context).move_id.id or \
                        False
#            raise osv.except_osv(_('Error !'), _(str(context.get(('active_ids'), [])[0])))
            if move_id:
                account_move_obj.write(cr, uid, [move_id], {'name': obj.name}, context=context)
                account_voucher_obj.write(cr, uid, context.get(('active_ids'), []), {'number': obj.name}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'name': fields.char('number', size=64, required=True),
    }

change_payment_no()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
