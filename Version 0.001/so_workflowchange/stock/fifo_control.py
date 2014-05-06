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

class fifo_control(osv.osv):
    _name = 'fifo.control'
    _description = 'FIFO Control'

    def _out_date(self, cr, uid, ids, prop, arg, context=None):
        res = {}
#        fifo_control_obj = self.pool.get('fifo.control')
#        uom_obj = self.pool.get('product.uom')
        for fifo in self.browse(cr, uid, ids, context=context):
            if fifo.out_move_id.picking_id:
                res[fifo.id] = fifo.out_move_id.picking_id.do_date
            else:
                if fifo.out_move_id.stock_inventory_ids:
                    for si in sm.stock_inventory_ids:
                        res[fifo.id] = si.date_done
        return res

    _columns = {
        'int_in_move_id': fields.many2one('stock.move', 'Int In Move Id'),
        'in_move_id': fields.many2one('stock.move', 'In Move Id'),
        'out_move_id': fields.many2one('stock.move', 'Out Move Id'),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM')),
        'out_date' : fields.function(_out_date, string='Out Date', type='datetime'),
    }

fifo_control()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
