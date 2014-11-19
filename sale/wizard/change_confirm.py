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

class change_confirm(osv.osv_memory):
    _name = 'change.confirm'
    _description = 'Change Confirmation Date'

    def do_reschedule(self, cr, uid, ids, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context=context):
            sale_order_line_obj.write(cr, uid, obj.sale_order_line_id.id, {'confirmation_date': obj.confirmation_date}, context=context)
        return {'type': 'ir.actions.act_window_close'}

#    def create(self, cr, user, vals, context=None):
#        sale_order_line_obj = self.pool.get('sale.order.line')
#        if 'reason_type' in vals:
#            if vals['reason_type'] == 'etd':
#                for lines in sale_order_line_obj.browse(cr, user, context.get(('active_ids'), []), context=context):
#                    sol_id = lines.id or False
#                change_cod2 = self.pool.get('change.cod')
#                change_cod_ids = self.search(cr, user, [('sale_order_line_id','=',sol_id)])
#                if change_cod_ids:
#                    for change_cod_id in self.browse(cr, user, change_cod_ids, context=context):
#                        if change_cod_id.reason_type == 'etd':
#                            raise osv.except_osv(_('Invalid Action!'), _('The System has detected that already input etd before.'))
#
#                vals.update({'reason': '-'})
#        new_id = super(change_cod, self).create(cr, user, vals, context)
#        return new_id
#
#    def type_onchange(self, cursor, user, ids, reason_type, context=None):
#        if reason_type:
#            if reason_type == 'etd':
#                return {'value': {'reason': '-'}}
#        return {}

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        res = super(change_confirm, self).default_get(cr, uid, fields, context=context)
        for lines in sale_order_line_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'sale_order_line_id' in fields:
                res.update({'sale_order_line_id': lines.id or False})
        return res

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', ondelete='cascade'),
        'confirmation_date': fields.date('Confirmation Reschedule Date', required=True, select=True),
    }

change_confirm()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
