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
from tools.translate import _

class res_partner(osv.osv):
    _inherit = "res.partner"
    _description = "Partner"

    def _compute_lines_payment(self, cr, uid, ids, name, args, context=None):
        result = {}
        for partners in self.browse(cr, uid, ids, context=context):
            lines = []
            invoice_obj = self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(cr,uid,[('partner_id','=',ids[0])])
            invoices = invoice_obj.browse(cr, uid, invoice_ids, context=context)
            for inv in invoices:
                temp_lines = []
                temp_lines = map(lambda x: x.id, inv.invoice_line)
                lines += [x for x in temp_lines]
#            raise osv.except_osv(_('Debug Add!'), _(str(lines)))
            result[partners.id] = lines
        return result

    _columns = {
        'invoice_id': fields.function(_compute_lines_payment, relation='account.invoice.line', type="many2many", string='Invoices'),
    }

res_partner()

class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    _description = "Invoice Line"

    _columns = {
        'date_invoice': fields.related('invoice_id','date_invoice',type='date',string='Invoice Date'),
        'type_choose': fields.related('invoice_id','type',type='selection', selection=[('out_invoice','Customer Invoice'),('in_invoice','Supplier Invoice'),('out_refund','Customer Refund'),('in_refund','Supplier Refund')], string='Type'),
        'state': fields.related('invoice_id','state',type='selection', selection=[('draft','Draft'),('proforma','Pro-forma'),('proforma2','Pro-forma'),('open','Open'),('paid','Paid'),('cancel','Cancelled')], string='Status'),
        'comment': fields.related('invoice_id','comment',type='text',string='Additional Information'),
        'document': fields.related('invoice_id','document',type='char',string='Document Number'),
    }

account_invoice_line()

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _description = "Invoice"

    _columns = {
        'document': fields.char('Document Number', size=64, help="Reference of the document that supplier give.", readonly=True, states={'draft':[('readonly',False)]}),
    }

account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
