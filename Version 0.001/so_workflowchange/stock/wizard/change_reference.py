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

class change_reference(osv.osv_memory):
    _name = 'change.reference'
    _description = 'Change Reference No'

    def do_validate(self, cr, uid, ids, context=None):
        stock_picking_obj = self.pool.get('stock.picking')
        for obj in self.browse(cr, uid, ids, context=context):
            stock_picking_obj.write(cr, uid, context.get(('active_ids'), []), {'name': obj.name}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'name': fields.char('Reference', size=64, required=True),
    }

change_reference()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
