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

class internal_move_control(osv.osv):
    _name = 'internal.move.control'
    _description = 'Internal Move Control'

    _columns = {
        'internal_move_id': fields.many2one('stock.move', 'Internal Move Id'),
        'other_move_id': fields.many2one('stock.move', 'Move Id'),
        'quantity' : fields.float("Quantity", digits_compute=dp.get_precision('Product UoM')),
    }

internal_move_control()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
