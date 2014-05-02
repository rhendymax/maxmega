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
import time
from osv import fields,osv
from tools.translate import _
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
import decimal_precision as dp
import netsvc

class purchase_sequences(osv.osv):
    _name = "purchase.sequences"
    _description = "Purchase Order Sequences"

    def create_sequence(self, cr, uid, sname, company_id, context=None):
        prefix = sname.upper()

        seq = {
            'name': prefix,
            'implementation':'no_gap',
            'prefix': prefix,
            'suffix': "/%(y)s",
            'padding': 4,
            'number_increment': 1
        }
        if company_id:
            seq['company_id'] = company_id

        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def btn_create_purchase_s(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sequence_id:
#                raise osv.except_osv(_('Debug !'), _('xxx'))
                self.write(cr, uid, ids, {'sequence_id': self.create_sequence(cr, uid, o.name, o.company_id.id, context)})
        return True

    def create(self, cr, uid, data, context=None):
        purchase_sequences_obj = self.pool.get('purchase.sequences')
        if 'default_key' in data:
            if data['default_key'] == True:
                purchase_sequences_ids = purchase_sequences_obj.search(cr, uid, [('default_key','=',True)])
                if purchase_sequences_ids:
                    raise osv.except_osv(_('Invalid Action'), _('The System has detected that already have default sequence before.'))
        return super(purchase_sequences, self).create(cr, uid, data, context)

    def write(self, cr, uid, ids, vals, context=None):
        purchase_sequences_obj = self.pool.get('purchase.sequences')
        if 'default_key' in vals:
            if vals['default_key'] == True:
                purchase_sequences_ids = purchase_sequences_obj.search(cr, uid, [('default_key','=',True)])
                if purchase_sequences_ids:
                    raise osv.except_osv(_('Invalid Action'), _('The System has detected that already have default sequence before.'))

        return super(purchase_sequences, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', help="This field contains the information related to the numbering of the purchase order entries."),
        'company_id':fields.many2one('res.company', 'Company'),
        'default_key' : fields.boolean('Default Sequence'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }
purchase_sequences()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
