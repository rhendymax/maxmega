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

class change_effective(osv.osv_memory):
    _name = 'change.effective'
    _description = 'Change Effective Date'

    _columns = {
        'sale_order_line_id': fields.many2one('sale.order.line', 'Sale Order Line', ondelete='cascade'),
        'change_date': fields.date('Effective Date', required=True, select=True),
        'reason': fields.char('Reason', size=254, required=True, select=True),
        'create_uid': fields.many2one('res.users', 'Responsible'),
        'create_date': fields.datetime('Creation Date',),
    }

change_effective()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
