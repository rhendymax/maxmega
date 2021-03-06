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
import re

class res_partner(osv.osv):
    _inherit = "res.partner"
    _description = "Partner"

    _columns = {
        'ref': fields.char('Code', size=64, select=1, required=True),
        'sundry': fields.boolean('Sundry', help="Check this box to set this partner as Sundry."),
        'contact_person_ids': fields.one2many('contact.person', 'partner_id', 'Contact Person'),
        'sale_term_id': fields.many2one('sale.payment.term','Sale Payment Term'),
        'ship_method_id': fields.many2one('shipping.method','Ship Method'),
        'sales_zone_id': fields.many2one('res.partner.sales.zone','Sales Zone'),
        'fob_id': fields.many2one('fob.point.key','FOB Point Key'),
        'property_product_pricelist': fields.property(
            'product.pricelist',
            type='many2one', 
            relation='product.pricelist', 
            domain=[('type','=','sale')],
            string="Sale Pricelist",
            required=True,
            view_load=True,
            help="This pricelist will be used, instead of the default one, for sales to the current partner"),
        'property_product_pricelist_purchase': fields.property(
          'product.pricelist',
          type='many2one', 
          relation='product.pricelist', 
          domain=[('type','=','purchase')],
          string="Purchase Pricelist", 
          required=True,
          view_load=True,
          help="This pricelist will be used, instead of the default one, for purchases from the current partner"),
        'grace': fields.integer('Grace Days', help="number of Grace Days(for customer only)"),
        'exist_partner': fields.boolean('Allowed Existing Partner', help="Allowed Existing Partner when address is different!"),
    }

    def address_get(self, cr, uid, ids, adr_pref=None):
        if adr_pref is None:
            adr_pref = ['default']
        address_obj = self.pool.get('res.partner.address')
        address_ids = address_obj.search(cr, uid, [('partner_id', 'in', ids)])
        default_type_use_ids = []
        default_type_ids = []
        delivery_type_use_ids = []
        delivery_type_ids = []
        invoice_type_use_ids = []
        invoice_type_ids = []
        contact_type_use_ids = []
        contact_type_ids = []

        for addr in address_obj.browse(cr, uid, address_ids, context=None):
            if addr.type == 'default' and addr.default_key == True:
                default_type_use_ids.append(addr.id)
            if addr.type == 'default' and addr.default_key != True:
                default_type_ids.append(addr.id)
            if addr.type == 'delivery' and addr.default_key == True:
                delivery_type_use_ids.append(addr.id)
            if addr.type == 'delivery' and addr.default_key != True:
                delivery_type_ids.append(addr.id)
            if addr.type == 'invoice' and addr.default_key == True:
                invoice_type_use_ids.append(addr.id)
            if addr.type == 'invoice' and addr.default_key != True:
                invoice_type_ids.append(addr.id)
            if addr.type == 'contact' and addr.default_key == True:
                contact_type_use_ids.append(addr.id)
            if addr.type == 'contact' and addr.default_key != True:
                contact_type_ids.append(addr.id)
        default = default_type_use_ids and default_type_use_ids[0] or \
                default_type_ids and default_type_ids[0] or False
        delivery = delivery_type_use_ids and delivery_type_use_ids[0] or \
                delivery_type_ids and delivery_type_ids[0] or default
        invoice = invoice_type_use_ids and invoice_type_use_ids[0] or \
                invoice_type_ids and invoice_type_ids[0] or default
        contact = contact_type_use_ids and contact_type_use_ids[0] or \
                contact_type_ids and contact_type_ids[0] or default
        result = {}
        result['default'] = default
        result['contact'] = contact
        result['delivery'] = delivery
        result['invoice'] = invoice
        return result

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            ref = d.get('ref',False)
            if ref:
                name = '[%s] %s' % (ref,name)

            return (d['id'], name)

        result = []
        for partner in self.browse(cr, user, ids, context=context):
            mydict = {
                      'id': partner.id,
                      'name': partner.name,
                      'ref': partner.ref,
                      }
            result.append(_name_get(mydict))
        return result

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('ref','=',name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('ref',operator,name)], limit=limit, context=context))
                if len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit-len(ids)), context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('ref','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    def _check_name(self, cursor, user, ids, context=None):
        for partner in self.browse(cursor, user, ids, context=context):
            if self.search(cursor, user, [('name', '=', partner.name),('ref', '=', partner.ref),('customer', '=', partner.customer),('supplier', '=', partner.supplier),('id', '!=', partner.id)]):
                if partner.exist_partner == False:
                    return False
        return True

    _constraints = [
        (_check_name, 'Error: Partner Name and Ref must be unique per Partner! or Tick the Allowed Existing Partner to Save!', ['name']),
    ]

    def create(self, cr, user, vals, context=None):
        #RT
        name = ('name' in vals and vals['name']) or False
        ref = ('ref' in vals and vals['ref']) or False
        if name:
            vals.update({'name': name.strip()})
        if ref:
            vals.update({'ref': ref.strip()})
        
        customer = ('customer' in  vals and vals['customer']) or False
        supplier = ('supplier' in  vals and vals['supplier']) or False
        sundry = ('sundry' in  vals and vals['sundry']) or False
        if (not customer) and (not supplier) and (not sundry): 
            raise osv.except_osv(_('Error!'), _('You Need Tick At least Customer Or Supplier!'))
        if customer:
            if supplier or sundry:
                raise osv.except_osv(_('Error!'), _('You Can Only Tick Customer Or Supplier Only!'))
        if supplier:
            if customer:
                raise osv.except_osv(_('Error!'), _('You Can Only Tick Customer Or Supplier Only!'))
        if sundry:
            if not supplier:
                raise osv.except_osv(_('Sundry!'), _('You Need Tick Supplier When Choosing Sundry !'))
        #END RT
        
        if 'customer' in vals:
            if vals['customer']:
                sales_zone_id = ('sales_zone_id' in vals and vals['sales_zone_id']) or False
                if not sales_zone_id:
                    raise osv.except_osv(_('No Sales Zone!'), _('You have to select a Sales Zone in the customer form !'))
        new_id = super(res_partner, self).create(cr, user, vals, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        po_id = (type(ids).__name__ == 'list' and ids[0]) or ids or False
        customer = ('customer' in vals and vals['customer']) or False
        if not 'customer' in vals:
            customer = (self.pool.get('res.partner').browse(cr, uid, po_id, context=None).customer)

        sales_zone_id = ('sales_zone_id' in vals and vals['sales_zone_id']) or (self.pool.get('res.partner').browse(cr, uid, po_id, context=None).sales_zone_id and self.pool.get('res.partner').browse(cr, uid, po_id, context=None).sales_zone_id.id) or False
        #RT
        name = ('name' in vals and vals['name']) or False
        ref = ('ref' in vals and vals['ref']) or False
        if name:
            vals.update({'name': name.strip()})
        if ref:
            vals.update({'ref': ref.strip()})

        supplier = ('supplier' in vals and vals['supplier']) or False
        if not 'supplier' in vals:
            supplier = (self.pool.get('res.partner').browse(cr, uid, po_id, context=None).supplier)

        sundry = ('sundry' in vals and vals['sundry']) or False
        if not 'sundry' in vals:
            sundry = (self.pool.get('res.partner').browse(cr, uid, po_id, context=None).sundry)

        if (not customer) and (not supplier) and (not sundry): 
            raise osv.except_osv(_('Error!'), _('You Need Tick At least Customer Or Supplier!'))
        if customer:
            if supplier or sundry:
                raise osv.except_osv(_('Error!'), _('You Can Only Tick Customer Or Supplier Only!'))
        if supplier:
            if customer:
                raise osv.except_osv(_('Error!'), _('You Can Only Tick Customer Or Supplier Only!'))
        if sundry:
            if not supplier:
                raise osv.except_osv(_('Sundry!'), _('You Need Tick Supplier When Choosing Sundry !'))
        #end RT

        if customer:
            if not sales_zone_id:
                raise osv.except_osv(_('No Sales Zone!'), _('You have to select a Sales Zone in the customer form !'))

        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

res_partner()

class res_partner_address(osv.osv):
    _inherit = "res.partner.address"
    _description = "Partner Addresses"

    _columns = {
        'partner_id_dummy': fields.many2one('res.partner', 'Print Supplier Name', ondelete='set null'),
        'loc_address' : fields.boolean('Location Address'),
        'default_key' : fields.boolean('Default Use'),
        'type': fields.selection( [ ('default','Default'),('invoice','Invoice'), ('delivery','Delivery'), ('contact','Mail'), ('other','Other') ],'Address Type', help="Used to select automatically the right address according to the context in sales and purchases documents."),
    }

res_partner_address()


class sale_payment_term(osv.osv):
    _name = "sale.payment.term"
    _description = "Sale Payment Term"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
        'act': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the payment term without removing it."),
        'days': fields.integer('Number of Days',),
        'grace': fields.integer('Number of Grace Days'),
    }

sale_payment_term()

class shipping_method(osv.osv):
    _name = "shipping.method"
    _description = "Shipping Method"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
    }

shipping_method()

class fob_point_key(osv.osv):
    _name = "fob.point.key"
    _description = "FOB Point Key"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.char('Description', size=64, required=True),
    }

fob_point_key()

class contact_person(osv.osv):
    _name = "contact.person"
    _description = "Contact Person"

    _columns = {
        'partner_id':fields.many2one('res.partner', 'Supplier', required=True),
        'name': fields.char('Name', size=64, required=True),
    }

contact_person()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
