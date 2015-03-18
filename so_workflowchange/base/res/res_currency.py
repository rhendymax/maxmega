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

class res_currency(osv.osv):
    _inherit = "res.currency"
    _description = "Currency"

    def create_sequence(self, cr, uid, sname, company_id, seq_func, context=None):
        if seq_func == "so":
            name = "SO/" + sname.upper()
        if seq_func == "do":
            name = "DO/" + sname.upper()
        suffix = sname.upper()
        seq = {
            'name': name,
            'implementation':'no_gap',
            'prefix': "%(y)s",
            'suffix': suffix,
            'padding': 5,
            'number_increment': 1
        }
        if company_id:
            seq['company_id'] = company_id

        return self.pool.get('ir.sequence').create(cr, uid, seq)

    def btn_create_sinvoice(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sinv_sequence_id:
                
#                raise osv.except_osv(_('Debug !'), _('xxx'))
                self.write(cr, uid, ids, {'sinv_sequence_id': self.create_sequence(cr, uid, o.name, o.company_id.id, "sinvoice", context)})
        return True

    def btn_create_cinvoice(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.cinv_sequence_id:
                
#                raise osv.except_osv(_('Debug !'), _('xxx'))
                self.write(cr, uid, ids, {'cinv_sequence_id': self.create_sequence(cr, uid, o.name, o.company_id.id, "cinvoice", context)})
        return True

    def btn_create_srefund(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sref_sequence_id:
                self.write(cr, uid, ids, {'sref_sequence_id': self.create_sequence(cr, uid, o.name, o.company_id.id, "srefund", context)})
        return True

    def btn_create_crefund(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.cref_sequence_id:
                self.write(cr, uid, ids, {'cref_sequence_id': self.create_sequence(cr, uid, o.name, o.company_id.id, "crefund", context)})
        return True

    def btn_create_sale(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.max_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input SO Currency Code before process.'))
            if not o.so_sequence_id:
                self.write(cr, uid, ids, {'so_sequence_id': self.create_sequence(cr, uid, o.max_name, o.company_id.id, "so", context)})
        return True

    def btn_create_do(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.do_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input DO Currency Code before process.'))
            if not o.do_sequence_id:
                self.write(cr, uid, ids, {'do_sequence_id': self.create_sequence(cr, uid, o.do_name, o.company_id.id, "do", context)})
        return True

    _columns = {
        'max_name': fields.char('Max Currency Code', size=64, select=True),
        'do_name': fields.char('DO Currency Code', size=64, select=True),
        'so_sequence_id': fields.many2one('ir.sequence', 'Sale Order Sequence', help="This field contains the information related to the numbering of the Sale Order entries.", required=True),
        'do_sequence_id': fields.many2one('ir.sequence', 'DO Sequence', help="This field contains the information related to the numbering of the DO entries.", required=True),
        'sinv_sequence_id': fields.many2one('ir.sequence', 'Supplier Invoice Sequence', help="This field contains the information related to the numbering of the supplier invoices entries.", required=True),
        'cinv_sequence_id': fields.many2one('ir.sequence', 'Customer Invoice Sequence', help="This field contains the information related to the numbering of the customer invoices entries.", required=True),
        'sref_sequence_id': fields.many2one('ir.sequence', 'Supplier Refund Sequence', help="This field contains the information related to the numbering of the supplier refund entries.", required=True),
        'cref_sequence_id': fields.many2one('ir.sequence', 'Customer Refund Sequence', help="This field contains the information related to the numbering of the customer refund entries.", required=True),
        'rate_ids2': fields.one2many('res.currency.rate2', 'currency_id', 'Rates for SGD'),
    }

res_currency()

class res_currency_rate2(osv.osv):
    _name = "res.currency.rate2"
    _description = "Currency Rate for SGD"

    _columns = {
        'name': fields.date('Date', required=True, select=True),
        'rate': fields.float('Rate', digits=(12,6), help='The rate of the currency to the currency of rate 1'),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
    }
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'),
    }
    _order = "name desc"

res_currency_rate2()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
