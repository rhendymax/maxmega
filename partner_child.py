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

import tools
from osv import fields,osv

class res_partner(osv.osv):
    _inherit = "res.partner"
    _description = "Partner"
    _columns = {
        'pchild_ids': fields.one2many('res.partner.child', 'partner_id', 'Partner Child'),
    }

res_partner()

class res_partner_child(osv.osv):
    _name = "res.partner.child"
    _description = "Partner Child"

    def _default_customer(self, cr, uid, context=None):
        customer = context.get('customer')
        return customer

    def _default_supplier(self, cr, uid, context=None):
        supplier = context.get('supplier')
        return supplier

    _columns = {
        'customer' : fields.related('partner_id', 'customer', type='boolean', string='Customer'),
        'supplier' : fields.related('partner_id', 'supplier', type='boolean', string='Supplier'),
        'name': fields.char('Branch Name', size=64),
        'partner_id': fields.many2one('res.partner', 'headquarters', required=True,
            ondelete='cascade', select=True),
    }

res_partner_child()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
