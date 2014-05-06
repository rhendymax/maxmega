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

class change_eta(osv.osv_memory):
    _name = 'change.eta'
    _description = 'Change Estimated Time Arrive'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        res = super(change_eta, self).default_get(cr, uid, fields, context=context)
        for lines in purchase_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'po_line_id' in fields:
                res.update({'po_line_id': lines.id or False})
        return res

    def do_reschedule(self, cr, uid, ids, context=None):
        purchase_order_line_obj = self.pool.get('purchase.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            purchase_order_line_obj.write(cr, uid, context.get(('active_ids'), []), {'estimated_time_arrive': obj.change_date}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'po_line_id': fields.many2one('purchase.order.line', 'Purchase Order Line', ondelete='cascade'),
        'change_date': fields.date('Effective Date', required=True, select=True),
        'reason': fields.char('Reason', size=254, required=True, select=True),
        'create_uid': fields.many2one('res.users', 'Responsible'),
        'create_date': fields.datetime('Creation Date',),
    }

change_eta()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
