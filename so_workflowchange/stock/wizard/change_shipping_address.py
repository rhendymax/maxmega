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

class change_shipping_address(osv.osv_memory):
    _name = 'change.shipping.address'
    _description = 'Change Shipping Address'

    def default_get(self, cr, uid, fields, context=None):

        stock_picking_obj = self.pool.get('stock.picking')
        if context is None:
            context = {}
        res = super(change_shipping_address, self).default_get(cr, uid, fields, context=context)

        for picking in stock_picking_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
            if 'partner_id' in fields:
                res.update({'partner_id': picking.partner_id.id})
        return res

    def change_shipping(self, cr, uid, ids, context=None):
        stock_picking_obj = self.pool.get('stock.picking')

        for obj in self.browse(cr, uid, ids, context=context):
            for picking in stock_picking_obj.browse(cr, uid, context.get(('active_ids'), []), context=context):
                stock_picking_obj.write(cr, uid, picking.id,
                    {'partner_shipping_id': obj.shipping_address.id}, context=context)

        return {'type': 'ir.actions.act_window_close'}


    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', help="Id of Partner", required=1),
        'shipping_address': fields.many2one('res.partner.address', 'Address', help="Address of shipping", required=1),
    }

change_shipping_address()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
