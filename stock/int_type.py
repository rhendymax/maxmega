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

class int_type(osv.osv):
    _name = "int.type"
    _description = "Physical Inventories Type"

    def create_sequence(self, cr, uid, sname, company_id, context=None):
        suffix = sname.upper()

        seq = {
            'name': "PI/" + suffix,
            'implementation':'no_gap',
            'prefix': "%(y)s",
            'suffix': suffix,
            'padding': 5,
            'number_increment': 1
        }
        if company_id:
            seq['company_id'] = company_id

        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def btn_create_type_s(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.seq_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Sequence Code before process.'))
            if not o.sequence_id:
                self.write(cr, uid, ids, {'sequence_id': self.create_sequence(cr, uid, o.seq_name, o.company_id.id, context)})
        return True

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'desc': fields.char('Description', size=64, select=True),
        'seq_name': fields.char('Sequence Code', size=64, select=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', help="This field contains the information related to the numbering of the purchase order entries."),
        'company_id':fields.many2one('res.company', 'Company'),
        'type': fields.selection([('addiction', 'Addiction'),
                                   ('reduction', 'Reduction')], 'Type',
                                   required=True),
        'property_stock_input': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Input Account', view_load=True),
        'property_stock_output': fields.property('account.account',
            type='many2one', relation='account.account',
            string='Output Account', view_load=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }
int_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
