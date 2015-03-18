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

from osv import fields, osv
from tools.translate import _
import time
from datetime import datetime
from mx import DateTime as dt
from mx.DateTime import RelativeDateTime as rdt
from datetime import timedelta
import pooler
import base64

class purchase_order_document(osv.osv_memory):
    _name = "purchase.order.document"
    _description = "Purchase Order Document"
    
#     def _get_period(self, cr, uid, context=None):
#         period_obj  = self.pool.get('account.period')
#         date_now    = time.strftime('%Y-%m-%dchase Order Document ')
#         period_ids  = period_obj.search(cr, uid, [('date_stop','>=',date_now)], order="date_stop ASC")
#         period_id   = False
#         if period_ids:
#             period_id = period_ids[0]
#         return period_id

    _columns = {
#         'period_id'     : fields.many2one('account.period', 'Period', domain=[('state', '=','draft')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }
#     _defaults = {
#          'period_id'     : _get_period,
#     }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas           = {'ids': context.get('active_ids')}
        datas['model']  = 'purchase.order'
        datas['form']   = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.purchase.order',
            'datas': datas,
        }

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        po_ids = ('ids' in data and data['ids']) or False
        model = ('model' in data and data['model']) or False
        if po_ids:
            result['po_ids'] = po_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, context=context)[0]
#         print data['ids']
#         for field in ['period_id']:
#             if isinstance(data['form'][field], tuple):
#                 data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_attn(self, o):
        contact = ''
        if o.contact_person_id:
            contact = (o.contact_person_id.name) or ''
        else:
            if o.partner_order_id:
                contact = (o.partner_order_id.name) or ''
        return contact

    def _get_description(self, cr, uid, l, partner_child_id):
        product_supplier_price = self.pool.get('product.supplier.price')
        product_supplier_obj = self.pool.get('product.supplier')
        description = ''
        product_supplier_id = product_supplier_obj.search(cr, uid, [('product_id','=', l.product_id.id),('partner_child_id','=', partner_child_id)])[0] or False
        product_supplier_price_ids = product_supplier_price.search(cr, uid, [('product_supplier_id','=', product_supplier_id),('effective_date','<=', l.original_request_date)], order='effective_date DESC')
        
        notes = ""
        if l.notes:
#             notes = '\n' + str(l.notes)
            notes = str(l.notes)
        
        if product_supplier_price_ids:
            remark = product_supplier_price.browse(cr, uid, product_supplier_price_ids[0],context=None).name
            if not remark:
                remark = ""
            else:
                remark = str(remark)
                if remark == "-":
                    remark = ""
        else:
            remark = ""
        if remark == "" :
            description = str(l.product_id.name)
        else:
#             description = str(l.product_id.name)+ '\n;' + str(remark)
            description = str(l.product_id.name) + ' ' + str(remark)
        return description + ' ' + notes

    def _display_address1(self, cr, uid, address, context=None):
        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner.address to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the address format
        address_format = address.country_id and address.country_id.address_format or \
                                         '%(street)s %(street2)s %(city)s,%(state_code)s %(zip)s' 
        # get the information that will be injected into the display format
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
        }
        address_field = ['title', 'street', 'street2', 'zip', 'city']
        for field in address_field :
            args[field] = getattr(address, field) or ''

        return address_format % args

    def _get_shipping(self, o):
        name = ''
#         print o
#         print o.partner_shipping_id
#         print o.partner_shipping_id.partner_id_dummy
#         print "TEST1"
        if o.partner_shipping_id and o.partner_shipping_id.partner_id_dummy:
#             print "TES"
            name = ((o.partner_shipping_id.partner_id_dummy.title and o.partner_shipping_id.partner_id_dummy.title.name) or '') + ((o.partner_shipping_id.partner_id_dummy.name) or '')
        return name

    def _get_tplines(self, cr, uid, ids, data, context):
#        raise osv.except_osv(_('Still Not Working !'), _('Not Working'))
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        obj_partner = self.pool.get('res.partner.address')
        
        all_content_line = ''
        
        company = self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id))
        header = 'sep=;' + " \n"
        header += str((company.name).title() or '') + ';' + str((company.street).title() or '') + ' ' + str((company.country_id and company.country_id.name).title() or '') + ' ' + str(company.zip or '') + ';' \
                + 'Telephone : ' + str(company.phone or '') + ' ' +'Facsimile : ' + str(company.fax or '') + ';'
        po_ids = form['po_ids'] or False
        po_obj = self.pool.get('purchase.order')
        x_no = 1

        if po_ids: 
            for po in po_obj.browse(cr, uid, po_ids):
                nom = 0
                po_date = po.date_order
                tgl = str(po_date)
                tgl2 = datetime.strftime(datetime.strptime(tgl,'%Y-%m-%d'),'%d-%m-%Y')
                if x_no > 1:
                    header += ';;;' + 'QUOTATION ORDER' + ';' \
                            + 'TO : ' + ';' + 'To_Tel' + ';' + 'To_Fax' + ';' + 'To_ATTN' + ';' \
                            + 'SHIP TO : ' + ';' + 'ShipTo_Tel' + ';' + 'ShipTo_Fax' + ';' + 'ShipTo_ATTN' + ';' \
                            + 'PO NO' + ';' + 'PO DATE' + ';' + 'SUBTOTAL' + ';' + str((po.fiscal_position and po.fiscal_position.name) or 'GST 7%') + ';' + 'TOTAL AMOUNT' + ';' + 'E.&.O.E' + ';' + 'ISSUED BY' + ';' \
                            + 'SHIPMENT METHOD' + ';' + 'SHIPMENT TERM' + ';' + 'REFERENCE NO :' + ';' + 'REQUISITOR :' + ';' + 'BUYER' + ';' \
                            + 'NO' + ';' + 'ITEM DESCRIPTION' + ';' + 'REQUIRED DATE' + ';' + 'QTY' + ';' \
                            + 'UNIT PRICE ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + ';' + 'TOTAL AMOUNT ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + " \n"
                else:
                    header += 'QUOTATION ORDER' + ';' \
                            + 'TO : ' + ';' + 'To_Tel' + ';' + 'To_Fax' + ';' + 'To_ATTN' + ';' \
                            + 'SHIP TO : ' + ';' + 'ShipTo_Tel' + ';' + 'ShipTo_Fax' + ';' + 'ShipTo_ATTN' + ';' \
                            + 'PO NO' + ';' + 'PO DATE' + ';' + 'SUBTOTAL' + ';' + str((po.fiscal_position and po.fiscal_position.name) or 'GST 7%') + ';' + 'TOTAL AMOUNT' + ';' + 'E.&.O.E' + ';' + 'ISSUED BY' + ';' \
                            + 'SHIPMENT METHOD' + ';' + 'SHIPMENT TERM' + ';' + 'REFERENCE NO :' + ';' + 'REQUISITOR :' + ';' + 'BUYER' + ';' \
                            + 'NO' + ';' + 'ITEM DESCRIPTION' + ';' + 'REQUIRED DATE' + ';' + 'QTY' + ';' \
                            + 'UNIT PRICE ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + ';' + 'TOTAL AMOUNT ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + " \n"
                # START FROM TO :
                header += ';;;;' \
                        + str((po.partner_id and po.partner_id.name).title() or '') + ';' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].phone) or '') + ';' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].fax) or '') + ';' + self._get_attn(po) + ';' \
                        + str(self._get_shipping(po)) + ';' + str(((po.partner_shipping_id and po.partner_shipping_id.phone)) or '') + ';' + str(((po.partner_shipping_id and po.partner_shipping_id.fax)) or '') + ';' + str((po.partner_shipping_id and po.partner_shipping_id.name) or '') + ';' \
                        + str((po.product_id and po.product_id.name) or '') + ';' + str(tgl2 or '') + ';' + str(po.amount_untaxed or 0) + ';' + str(po.amount_tax or 0) + ';' + str(po.amount_total or 0) + ';;;' \
                        + str((po.partner_id and po.partner_id.ship_method_id and po.partner_id.ship_method_id.name) or '') + ';' + str((po.partner_id and po.partner_id.fob_id and po.partner_id.fob_id.name) or '') + ';' + str(po.partner_ref or '') + ';' + str((po.requisitor_id and po.requisitor_id.name) or '') + ';' + str((po.buyer_id and po.buyer_id.name).title() or '') + ';'
                l_no = 1
                if po.order_line:
                    for l in po.order_line:
                        if l_no > 1:
                            header += ';;;;;;;;;;;;;;;;;;;;;;;;'
                        nom +=1
                        l_no += 1
                        header += str(nom) + ';' + str(self._get_description(cr, uid, l, po.partner_child_id and po.partner_child_id.id)) + ';' + str(datetime.strftime(datetime.strptime(str(l.original_request_date2),'%Y-%m-%d'),'%d-%m-%Y') or '') + ';' + str(l.product_qty or 0) + ' ' + str((l.product_uom and l.product_uom.name) or '') + ';' \
                                + str(l.price_unit or 0) + ';' + str((l.price_unit * l.product_qty) or 0) + ';' \
                                + " \n"

###########################
#     START COMMENT
###########################
# LEMPARAN --> + 'SHIP TO : ' + ';' + 'PO NO : '+ str((po.product_id and po.product_id.name) or '') + ';' \
#                                 + str((po.header_po and po.header_po.replace("\n", " ")) or '') + ';' + str(po.footer_po and po.footer_po.replace("\n", " ") or '') + ';' + 'SUBTOTAL' + ';' + str((po.fiscal_position and po.fiscal_position.name) or 'GST 7%') + ';' \
#                                 + 'TOTAL AMOUNT' + ';' + 'E.&.O.E ' + ';' + 'ISSUED BY' 
                                
                                
#                 header += str((po.partner_id and po.partner_id.name).title() or '') + ';' + str(self._get_shipping(po)) + ';' \
#                                 + 'PO DATE : '+ str(tgl2 or '') + ';;;' + str(po.amount_untaxed or '') + ';' + str(po.amount_tax or '') + ';' \
#                                 + str(po.amount_total or '') + ';;' + str(company.name or '') + '\n'
#                 header += str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].street).title() or '') + ';' \
#                         + str((po.partner_shipping_id and self._display_address1(cr, uid, po.partner_shipping_id, context)) or '') + ';' \
#                         + 'GST REG NO : '+ str((po.company_id and po.company_id.gst_reg_no) or '') + " \n"
#                 header += str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].country_id.name).title() or '') + ';' \
#                         + 'Tel. : ' + str(((po.partner_shipping_id and po.partner_shipping_id.phone)) or '') + ';' \
#                         + 'SHIPMENT METHOD : '+ str((po.partner_id and po.partner_id.ship_method_id and po.partner_id.ship_method_id.name) or '') + " \n"
#                 header += 'Tel. : ' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].phone) or '') + ';' \
#                         + 'Fax : ' + str(((po.partner_shipping_id and po.partner_shipping_id.fax)) or '') + ';' \
#                         + 'SHIPMENT TERM : '+ str((po.partner_id and po.partner_id.fob_id and po.partner_id.fob_id.name) or '') + " \n"
#                 header += 'Fax : ' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].fax) or '') + ';' \
#                         + 'ATTN : ' + str((po.partner_shipping_id and po.partner_shipping_id.name) or '') + ';' \
#                         + 'REFERENCE NO : '+ str(po.partner_ref or '') + ';' + " \n"
#                 header += 'ATTN : ' + self._get_attn(po) + ';;' + 'REQUISITOR : '+ str((po.requisitor_id and po.requisitor_id.name) or '') + " \n"
#                 header += ';;' + 'BUYER : '+ str((po.buyer_id and po.buyer_id.name).title() or '') + " \n"
#                 header += 'NO'+ ';' + 'ITEM DESCRIPTION' + ';' + 'REQUIRED DATE' + ';' + 'QTY' + ';' + 'UNIT PRICE ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + ';' \
#                                 + 'TOTAL AMOUNT ' + str((po.pricelist_id and po.pricelist_id.currency_id and po.pricelist_id.currency_id.name) or '') + " \n"
#                 if po.order_line:
#                     for l in po.order_line:
#                         nom +=1
#                         header += str(nom) + ';' + str(self._get_description(cr, uid, l, po.partner_child_id and po.partner_child_id.id)) + ';' \
#                                 + str(datetime.strftime(datetime.strptime(str(l.original_request_date2),'%Y-%m-%d'),'%d-%m-%Y') or '') + ';' \
#                                 + str(l.product_qty or 0) + ' ' + str((l.product_uom and l.product_uom.name) or '') + ';' + str(l.price_unit or 0) + ';' \
#                                 + str((l.price_unit * l.product_qty) or 0) + '\n'
# END COMMENT
#                         ';;' + str(po.amount_untaxed or '') + ';' \
#                         + str(po.amount_tax or '') + ';' + str(po.amount_total or '') + ';' + str(company.name or '') + " \n"
###########################
#     START COMMENT
###########################
                header += " \n"
                x_no += 1
#                 header += " \n"
#                 header += ';;;' + 'This is a computer generated Purchase Order. ' + ' \n'
#                 header += ';;;' + 'No signature is required' + ' \n'
# END COMMENT
#                 header += " \n" 
#                 header += " \n"
#                 header += 'TO :' + ';;;;;' + 'PO DATE' + ';' + ':' + ';' + str(tgl2 or '') + " \n"
#                 header += str((po.partner_id and po.partner_id.name).title() or '') + ';;;;;' + 'GST REG NO' + ';' + ':' + ';' \
#                        + str((po.company_id and po.company_id.gst_reg_no) or '') + " \n"
#                 header += str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].street).title() or '') \
#                        + ';;;;;' + 'SHIPMENT METHOD' + ';' + ':' + ';' + str((po.partner_id and po.partner_id.ship_method_id and po.partner_id.ship_method_id.name) or '') + " \n"
#                 header += str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].country_id.name).title() or '') + ' ' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].zip) or '') + " \n"
#                 header += 'Tel. : ' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].phone) or '') + ';;;;;' + 'SHIPMENT TERM' + ';' + ':' + ';' + str((po.partner_id and po.partner_id.fob_id and po.partner_id.fob_id.name) or '') + " \n"
#                 header += 'Fax : ' + str((po.partner_id and po.partner_id.address[0] and po.partner_id.address[0].fax) or '') + ';;;;;' + 'REFERENCE NO' + ';' + ':' + ';' + str(po.partner_ref or '') + " \n"
#                 header += 'ATTN : ' + self._get_attn(po) + " \n"
#                 header += ';;;;;' + 'REQUISITOR' + ';' + ':' + ';' + str((po.requisitor_id and po.requisitor_id.name) or '')  + " \n"
#                 header += 'SHIP TO : ' + ';;;;;' + 'BUYER' + ';' + ':' + ';' + str((po.buyer_id and po.buyer_id.name).title() or '')
#                 header += str(self._get_shipping(po)) + ';;;;;' + 'PAYMENT TERM' + ';' + ':' + ';' + str((po.sale_term_id and po.sale_term_id.description).upper() or '') + " \n"
#                 header += str((po.partner_shipping_id and obj_partner._display_address(cr, uid, po.partner_shipping_id, context)) or '') + " \n"
#                 header += 'Tel. : ' + str(((po.partner_shipping_id and po.partner_shipping_id.phone)) or '') + " \n"
#                 header += 'Fax : ' + str(((po.partner_shipping_id and po.partner_shipping_id.fax)) or '') + " \n"
#                 header += 'ATTN : ' + str((po.partner_shipping_id and po.partner_shipping_id.name) or '') + " \n"
#                 header += " \n"
#                 header += 'NO'+ ';' + 'ITEM DESCRIPTION' + ';;;' + 'REQUIRED DATE' + ';;' + 'QTY' + ';' + 'UNIT PRICE' + ';;' + 'TOTAL AMOUNT' +" \n"
#                 header += ';;;;;;;' + 'USD' + ';;' + 'USD' +" \n"
#                 header += " \n"
#                 header += str(po.header_po or '') + ' \n'
#                 if po.order_line:
#                     for l in po.order_line:
#                         nom +=1
#                         header += str(nom) + ';' + str(self._get_description(cr, uid, l, po.partner_child_id and po.partner_child_id.id)) + ';;;' + str(datetime.strftime(datetime.strptime(str(l.original_request_date2),'%Y-%m-%d'),'%d-%m-%Y') or '') + ';;' + str(l.product_qty or 0) + ' ' + str((l.product_uom and l.product_uom.name) or '') + ';' + str(l.price_unit or 0) + ';;' + str((l.price_unit * l.product_qty) or 0) +" \n"
#                 header += str(po.footer_po or '') + ' \n'
#                 header += " \n"
#                 header += " \n"
#                 header += " \n"
#                 header += ';;;;;' + 'SUBTOTAL' + ';;' + ':' + ';;' + str(po.amount_untaxed or '') + " \n"
#                 header += ';;;;;' + str((po.fiscal_position and po.fiscal_position.name) or 'GST 7%') + ';;' + ':' + ';;' + str(po.amount_tax or '') + " \n"
#                 header += ';;;;;' + 'TOTAL AMOUNT' + ';;' + ':' + ';;' + str(po.amount_total or '') + " \n"
#                 header += " \n"
#                 header += ';;;;;;;;;' + 'E.&.O.E' + ' \n'
#                 header += ';;;;;' + 'ISSUED BY'
#                 header += " \n"
#                 header += " \n"
#                 header += ';;;;;' + str(company.name or '') + ' \n \n'
#                 header += ';;;;;' + 'This is a computer generated Purchase Order. ' + ' \n'
#                 header += ';;;;;' + 'No signature is required' + ' \n'
                
#        user_obj = self.pool.get('res.partner')
        
#         po_obj = self.pool.get('purchaspo_idse.order')
        
#         invoice_obj     = self.pool.get('account.invoice')
#         sale_payment_term_obj     = self.pool.get('sale.payment.term')
#         period_obj = self.pool.get('account.period')
#         
#         period_id = form['period_id'] or False
#         period = self.pool.get('account.period').browse(cr, uid, period_id)
#         company = self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id))
#         partner_ids = form['partner_ids'] or False

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += str(company.name or '') + ' \n \n'
        all_content_line += 'This is a computer generated Purchase Order. ' + ' \n'
        all_content_line += 'No signature is required' + ' \n'
#         all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Purchase Order Document.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','action_purchase_order_csv_report')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Purchase Order Document',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order.document',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }


purchase_order_document()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
