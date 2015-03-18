# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields

class company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'def_pur_journal_id': fields.many2one('account.journal', 'Default Purchase Journal'),
        'def_sal_journal_id': fields.many2one('account.journal', 'Default Sales Journal'),
        'location_id' : fields.many2one('stock.location', 'Default Location'),
        'tax_id': fields.many2one('account.tax', 'Default Sales Tax', domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])]),
        'supplier_tax_id': fields.many2one('account.tax', 'Default Purchase Tax', domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])]),
        'sinv_name': fields.char('Supplier Invoice Code', size=64),
        'sref_name': fields.char('Supplier Refund Code', size=64),
        'cref_name': fields.char('Customer Refund Code', size=64),
        'sinv_sundry_name': fields.char('Supplier Invoice(Sundry) Code', size=64),
        'sref_sundry_name': fields.char('Supplier Refund(Sundry) Code', size=64),
        'sinv_chrg_name': fields.char('Supplier Invoice(Charges) Code', size=64),
        'cinv_chrg_name': fields.char('Customer Invoice(Charges) Code', size=64),
        'sinv_seq_id': fields.many2one('ir.sequence', 'Supplier Invoice Sequence', help="This field contains the information related to the numbering of the supplier invoices entries."),
        'sref_seq_id': fields.many2one('ir.sequence', 'Supplier Refund Sequence', help="This field contains the information related to the numbering of the supplier refund entries."),
        'cref_seq_id': fields.many2one('ir.sequence', 'Customer Refund Sequence', help="This field contains the information related to the numbering of the supplier refund entries."),
        'sinv_sundry_seq_id': fields.many2one('ir.sequence', 'Supplier Invoice(Sundry) Sequence', help="This field contains the information related to the numbering of the supplier invoices(sundry) entries."),
        'sref_sundry_seq_id': fields.many2one('ir.sequence', 'Supplier Refund(Sundry) Sequence', help="This field contains the information related to the numbering of the supplier refund(sundry) entries."),
        'sinv_chrg_seq_id': fields.many2one('ir.sequence', 'Supplier Invoice(Charges) Sequence', help="This field contains the information related to the numbering of the supplier invoices(charges) entries."),
        'cinv_chrg_seq_id': fields.many2one('ir.sequence', 'Customer Invoice(Charges) Sequence', help="This field contains the information related to the numbering of the customer invoices(charges) entries."),
        'currency_tax_id': fields.many2one('res.currency', 'Currency for Tax Purpose', required=True),
        'gst_reg_no': fields.char('GST Reg No', size=64, select=1, required=True),
        
    }
    def btn_crt_si(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sinv_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Supplier Invoice Code before process.'))
            if not o.sinv_seq_id:
                self.write(cr, uid, ids, {'sinv_seq_id': self.create_sequence(cr, uid, o.sinv_name, o.id, "si", context)})
        return True

    def btn_crt_si_s(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sinv_sundry_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Supplier(Sundry) Code before process.'))
            if not o.sinv_sundry_seq_id:
                self.write(cr, uid, ids, {'sinv_sundry_seq_id': self.create_sequence(cr, uid, o.sinv_sundry_name, o.id, "si_s", context)})
        return True

    def btn_crt_sr(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sref_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Supplier Refunds Code before process.'))
            if not o.sref_seq_id:
                self.write(cr, uid, ids, {'sref_seq_id': self.create_sequence(cr, uid, o.sref_name, o.id, "sr", context)})
        return True

    def btn_crt_cr(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.cref_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Customer Refunds Code before process.'))
            if not o.cref_seq_id:
                self.write(cr, uid, ids, {'cref_seq_id': self.create_sequence(cr, uid, o.cref_name, o.id, "cr", context)})
        return True

    def btn_crt_sr_s(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sref_sundry_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Supplier Refunds(Sundry) Code before process.'))
            if not o.sref_sundry_seq_id:
                self.write(cr, uid, ids, {'sref_sundry_seq_id': self.create_sequence(cr, uid, o.sref_sundry_name, o.id, "sr_s", context)})
        return True

    def btn_crt_si_c(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.sinv_chrg_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Supplier(Charges) Code before process.'))
            if not o.sinv_chrg_seq_id:
                self.write(cr, uid, ids, {'sinv_chrg_seq_id': self.create_sequence(cr, uid, o.sinv_chrg_name, o.id, "si_c", context)})
        return True

    def btn_crt_ci_c(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.cinv_chrg_name:
                raise osv.except_osv(_('Invalid Action !'), _('Please input Customer(Charges) Code before process.'))
            if not o.cinv_chrg_seq_id:
                self.write(cr, uid, ids, {'cinv_chrg_seq_id': self.create_sequence(cr, uid, o.cinv_chrg_name, o.id, "ci_c", context)})
        return True

    def create_sequence(self, cr, uid, sname, company_id, seq_func, context=None):
        if seq_func == "si":
            name = "SI/" + sname.upper()
        if seq_func == "si_s":
            name = "SI(S)/" + sname.upper()
        if seq_func == "sr":
            name = "SR/" + sname.upper()
        if seq_func == "sr_s":
            name = "SR(S)/" + sname.upper()
        if seq_func == "cr":
            name = "CR/" + sname.upper()
        if seq_func == "si_c":
            name = "SI(C)/" + sname.upper()
        if seq_func == "ci_c":
            name = "CI(C)/" + sname.upper()
        prefix = sname.upper()
        seq = {
            'name': name,
            'implementation':'no_gap',
            'prefix':prefix,
            'suffix':"/%(y)s",
            'padding': 4,
            'number_increment': 1
        }
        if company_id:
            seq['company_id'] = company_id

        return self.pool.get('ir.sequence').create(cr, uid, seq)
company()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

