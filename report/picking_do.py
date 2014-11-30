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

import time
from report import report_sxw
from osv import osv
import pooler
import locale
from mx import DateTime as dt
from report.interface import report_rml
from tools import to_xml
import calendar
import math
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, '')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#class picking(report_sxw.rml_parse):
#    def __init__(self, cr, uid, name, context):
#        super(pickingw, self).__init__(cr, uid, name, context=context)
#        self.localcontext.update({
#            'time': time,
#            'get_qtytotal':self._get_qtytotal
#        })
#    def _get_qtytotal(self,move_lines):
#        total = 0.0
#        uom = move_lines[0].product_uom.name
#        for move in move_lines:
#            total+=move.product_qty
#        return {'quantity':total,'uom':uom}

#report_sxw.report_sxw('report.stock.picking.list2','stock.picking','addons/max_report_addons/report/picking.rml',parser=picking)
## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
class maxmega_picking_do(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(maxmega_picking_do, self).__init__(cr, uid, name, context=context)
#         user_obj       = self.pool.get('res.users')
#         name = user_obj.browse(cr, uid, uid, context=None).name
#         print str(name)
        self.localcontext.update({
              'get_description' : self._get_description,
        })

    def _get_description(self, l):
        description = ''
        len_note_pn = len(l.note or "")
        len_note_pn_remark = 0
        if len_note_pn > 1:
            pn_note_lines = str(l.note or "").split('\n')
            while (len_note_pn_remark < 1):
                part_note = str(pn_note_lines[len_note_pn_remark])
                len_note_pn_remark += 1
        if len_note_pn > 0:
            description = str(l.product_id.default_code)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
        else:
            description = str(l.product_id.default_code)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
        return description

# class maxmega_picking_do(report_rml):
#     def create(self, cr, uid, ids, datas, context):
#         pool           = pooler.get_pool(cr.dbname)
#         do_obj         = pool.get('stock.picking')
#         user_obj       = pool.get('res.users')
#         do_ids         = ids
#         rml_res        = ''
# 
#         def _number_format(amount):
#             res = {'amount': amount}
#             return locale.format("%(amount).2f", res,1)
#         
#         def _qty_format(qty1):
#             q1 = {'qty1' : qty1}
#             return locale.format("%(qty1).f", q1,1)
#         
#         def header(o):
#             header = """
#             <blockTable colWidths="257.0,38.00,260.0" style="Tableau1">
#                 <tr>
#                     <td>
#                         <blockTable colWidths="257.0" rowHeights="100.0,100.0" style="Tableau2">
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_Bold_8">BILL TO :</para>
#                                     <para style="terp_default_8">""" + str((o.partner_id and o.partner_id.title and o.partner_id.title.name) or '') + """ """ + str((o.partner_id and o.partner_id.name) or '') +  """</para>"""
#             disaddress = False
#             if o.partner_invoice_id:
#                 address = o.partner_invoice_id
#                 address_format = address.country_id and address.country_id.address_format or \
#                      '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
#                 args = {
#                     'state_code': address.state_id and address.state_id.code or '',
#                     'state_name': address.state_id and address.state_id.name or '',
#                     'country_code': address.country_id and address.country_id.code or '',
#                     'country_name': address.country_id and address.country_id.name or '',
#                 }
#                 address_field = ['title', 'street', 'street2', 'zip', 'city']
#                 for field in address_field :
#                     args[field] = getattr(address, field) or ''
#                 disaddress = address_format % args
#             if disaddress:
#                 header += """            <para style="terp_default_8">""" + str(disaddress) + """</para>
#                                         """
#             if (o.partner_invoice_id and o.partner_invoice_id.phone):
#                 header += """
#                     <para style="terp_default_8">Tél. : """ + str (o.partner_invoice_id.phone) + """</para> """
#             if (o.partner_invoice_id and o.partner_invoice_id.fax):
#                 header += """
#                     <para style="terp_default_8">Fax : """ + str (o.partner_invoice_id.fax) + """</para> """
#             attention = False
#             if (o.partner_invoice_id and o.partner_invoice_id.name):
#                 attention = str(o.address_id.name)
#             if (o.partner_invoice_id and o.partner_invoice_id.email):
#                 if attention:
#                     attention += ' ' + str(o.partner_invoice_id.email)
#                 else:
#                     attention = str(o.partner_invoice_id.email)
#             if attention:
#                 header += """
#                     <para style="terp_default_8">Attn : """ + attention + """</para> """
# 
#             header += """
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_Bold_8">SHIP TO :</para>
#                                     <para style="terp_default_8">""" + str((o.partner_id and o.partner_id.title and o.partner_id.title.name) or '') + """ """ + str((o.partner_id and o.partner_id.name) or '') +  """</para>"""
#             disaddress = False
#             if o.partner_shipping_id:
#                 address = o.partner_shipping_id
#                 address_format = address.country_id and address.country_id.address_format or \
#                      '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
#                 args = {
#                     'state_code': address.state_id and address.state_id.code or '',
#                     'state_name': address.state_id and address.state_id.name or '',
#                     'country_code': address.country_id and address.country_id.code or '',
#                     'country_name': address.country_id and address.country_id.name or '',
#                 }
#                 address_field = ['title', 'street', 'street2', 'zip', 'city']
#                 for field in address_field :
#                     args[field] = getattr(address, field) or ''
#                 disaddress = address_format % args
#             if disaddress:
#                 header += """            <para style="terp_default_8">""" + str(disaddress) + """</para>
#                                         """
#             if (o.partner_shipping_id and o.partner_shipping_id.phone):
#                 header += """
#                     <para style="terp_default_8">Tél. : """ + str (o.partner_shipping_id.phone) + """</para> """
#             if (o.partner_shipping_id and o.partner_shipping_id.fax):
#                 header += """
#                     <para style="terp_default_8">Fax : """ + str (o.partner_shipping_id.fax) + """</para> """
#             attention = False
#             if (o.partner_shipping_id and o.partner_shipping_id.name):
#                 attention = str(o.partner_shipping_id.name)
#             if (o.partner_shipping_id and o.address_id.email):
#                 if attention:
#                     attention += ' ' + str(o.partner_shipping_id.email)
#                 else:
#                     attention = str(o.partner_shipping_id.email)
#             if attention:
#                 header += """
#                     <para style="terp_default_8">Attn : """ + attention + """</para> """
# 
#             header += """
#                                 </td>
#                             </tr>
#                         </blockTable>
#                     </td>
#                     <td>
#                     </td>
#                     <td>
#                         <blockTable colWidths="120.0,140.0" rowHeights="12,200" style="Tableau2">
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_9_Italic_Bold">DELIVERY ORDER</para>
#                                 </td>
#                                 <td>
#                                 </td>
#                             </tr>
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_Bold_8">GST REG.NO</para>
#                                     <para style="terp_default_Bold_8">NO</para>
#                                     <para style="terp_default_Bold_8">SHIP DATE</para>
#                                     <para style="terp_default_Bold_8">PAYMENT TERM</para>
#                                     <para style="terp_default_Bold_8">SALES PERSON</para>
#                                 </td>
#                                 <td>
#                                     <para style="terp_default_8">:""" """ """+(o.company_id and o.company_id.company_registry or '')+"""</para>
#                                     <para style="terp_default_8">:""" """ """+(o.name or '')+"""</para>
#                                     <para style="terp_default_8">:""" """</para>
#                                     <para style="terp_default_8">:""" """ """+ str(o.partner_id.sale_term_id.name or '') +"""</para>
#                                     <para style="terp_default_8">:""" """ </para>
#                                 </td>
#                             </tr>
#                         </blockTable>
#                     </td>
#                 </tr>
#             </blockTable>"""
#             return header
#         def count_lines(string, width):
#             line = len(string)/(width*6)
#             line = math.ceil(line)
#             if line == 0:
#                 line += 1
#             return line
#         
#         def middle(o):
#             middle ="""
#             <blockTable colWidths="12.5,120.0,150.0,200.0,72.5" rowHeights="24.0" repeatRows="1" style="Move_Line_Header">
#                 <tr>
#                     <td>
#                         <para style="terp_tblheader_General_Centre">NO</para>
#                     </td>
#                     <td>
#                         <para style="terp_tblheader_General_Centre">S/O NO</para>
#                     </td>
#                     <td>
#                         <para style="terp_tblheader_General_Centre">CUSTOMER PO NO</para>
#                     </td>
#                     <td>
#                         <para style="terp_tblheader_General_Centre">ITEM DESCRIPTION</para>
#                     </td>
#                     <td>
#                     <para style="terp_tblheader_General_Centre">QTY</para>
#                     </td>
#                 </tr>
#             </blockTable>"""
#             return middle
#         
#         def footer(o):
#             
#             footer = """
#             <blockTable colWidths="130.0,127.0,38.00,130.0,130.0" rowHeights = "72.0" style="Table_Country_Detail">
#                 <tr>
#                     <td>
#                         <para style="terp_default_8">COUNTRY OF ORIGIN</para>
#                         <para style="terp_default_8">COUNTRY OF DESTINATION</para>
#                         <para style="terp_default_8">SHIPMENT METHOD</para>
#                         <para style="terp_default_8">SHIPMENT TERM</para>
#                     </td>
#                     <td>
#                         <para style="terp_default_8">:""" """ """+str(o.country_org_id.name or '')+"""</para>
#                         <para style="terp_default_8">:""" """ """+str(o.country_des_id.name or '')+"""</para>
#                         <para style="terp_default_8">:""" """ """ + str(o.ship_method_id.name or '') + """</para>
#                         <para style="terp_default_8">:""" """ """ +str(o.fob_id.name or '') +"""</para>
#                     </td>
#                     <td></td>
#                     <td>
#                         <para style="terp_default_8">NO OF CARTON</para>
#                         <para style="terp_default_8">GROSS WEIGHT</para>
#                         
#                     </td>
#                     <td>
#                         <para style="terp_default_8">:</para>
#                         <para style="terp_default_8">:</para>
#                     </td>
#                 </tr>
#             </blockTable>
#             <blockTable colWidths="257.0,38.0,260.0" rowHeights="12.0,48.0">
#             <tr>
#                <td>
#                     <para style="terp_default_Bold_8">MAXMEGA ELECTRONICS PTE LTD</para>
#                </td>
#                <td></td>
#                <td>
#                     <para style="terp_default_Bold_8">RECEIVED BY</para>
#                </td>
#             </tr>
#             <tr>
#                 <td>
#                     <illustration width="150" height="8">
#                     <lineMode width ="1.0"/>
#                     <lines>-6 5 200 5</lines>
#                     </illustration>
#                 </td>
#                 <td></td>
#                 <td>
#                     <illustration width="150" height="8">
#                     <lineMode width ="1.0"/>
#                     <lines>-6 5 200 5</lines>
#                     </illustration>
#                 </td>
#             </tr>
#             </blockTable>
#             """
#             return footer
#         
#         obj_count = 0
#         for o in do_obj.browse(cr, uid, do_ids):
#             if obj_count > 1:
#                 rml_res += """<pageBreak/>"""
#             
#             consigning_width = 555
#             user_note_width  = 555
#             consigning_lines = str(o.header_picking or "").split('\n')
#             user_note_lines = str(o.footer_picking or "").split('\n')
#             len_consign = len(o.header_picking or "")
#             len_user_note = len(o.footer_picking or "")
#             Total_consigning_line = 0
#             Total_line_note = 0
#             len_line = len(o.move_lines)
#             blank_height = 2.69
#             frame_page_height = 247.22
#             frame_page_height2 = 379.22  
#             total_height_p = 0
#             total_page2 = 0
#             line_height_p = 0
#             number_p = 0
#             total_height = 0
#             count_line = 0
#             number_ = 0
#             line_heights = 0
#             total_page1 = 0
#             page = 1
#             consigning_heights = 0
#             len_note = 0
#             len_consigning = 0
#             user_note_heights = 0
#             
#             if len_user_note > 0:
#                 if len_user_note < 3:
#                     while (len_note < (len_consign + 1)):
#                         len_lines_usernote = []
#                         len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
#                         Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
#                         user_note_heights += Total_line_note
#                         len_note += 1
#                 else:
#                     while (len_note < 3):
#                         len_lines_usernote = []
#                         len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
#                         Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
#                         user_note_heights += Total_line_note
#                         len_note += 1
#                         
#             if len_consign > 0:
#                 if len_consign < 3:
#                     while (len_consigning < (len_consign+1)):
#                         len_lines_consigning = []
#                         len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
#                         Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
#                         consigning_heights += Total_consigning_line
#                         len_consigning += 1
#                 else:
#                     while (len_consigning < 3):
#                         len_lines_consigning = []
#                         len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
#                         Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
#                         consigning_heights += Total_consigning_line
#                         len_consigning += 1
#             
#             if len_line < 1 :
#                 frame_page_height2 = frame_page_height
#                 rml_res += header(o)
#                 total_page = 1
#                 user_note_heights =  0.00
#                 rml_res += """
#                     <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
#                         <tr>
#                             <td>
#                                 <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                             </td>
#                         </tr>
#                     </blockTable>
#                     """
#                 rml_res += middle(o)
#             
#             else:
#                 for l in o.move_lines:
#                     len_note_pn = len(l.note or "")
#                     len_note_pn_remark = 0
#                     if len_note_pn > 1:
#                         pn_note_lines = str(l.note or "").split('\n')
#                         while (len_note_pn_remark < 1):
#                             part_note = str(pn_note_lines[len_note_pn_remark])
#                             len_note_pn_remark += 1
#                             
#                     lines = []
#     
#                     number_p += 1
#                     number_des = str(int(number_p))
#                     number_des_width = 12.5
#                     lines.append(count_lines(str(number_des),number_des_width)) 
#                     
#                     so_number = str(l.sale_id.name)
#                     so_number_width = 120
#                     lines.append (count_lines(str(so_number), so_number_width))
#                     
#                     cust_po_no = str(l.client_order_ref)
#                     cust_po_no_width = 150
#                     lines.append(count_lines(str(cust_po_no), cust_po_no_width))
#                     
#                     if len_note_pn > 0:
#                         description = str(l.product_id.default_code)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#                     else:
#                         description = str(l.product_id.default_code)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#                     
#                     description_width = 200
#                     description_line = str(description).split('\n')
#                     line_des = []
#                     for a in description_line:
#                         line_des.append(count_lines(str(a),description_width))
#                     
#                     len_line_des = len(line_des)
#                     lds = 0
#                     lines_des_int = []
#                     while (lds < len_line_des):
#                         lines_des_int.append(int(line_des[lds]))
#                         lds += 1
#                     total_des_line = (sum(lines_des_int))
#                     lines.append(total_des_line)
#                     
#                     quantity = _qty_format(l.product_qty) + str(l.product_uom.name)
#                     quantity_width = 72.5
#                     lines.append(count_lines(str(quantity), quantity_width))
#                     
#                     lines = sorted(lines)
#                     line_height_p = (lines[(len(lines)-1)] * 12)
#                     total_height_p += line_height_p
#                     
#                 total_height_p = total_height_p + consigning_heights + user_note_heights + blank_height
#                 total_page1 = total_height_p%frame_page_height2
#                 total_page2 = (total_height_p-total_page1)/frame_page_height2
#                 
#                 if total_page1 == frame_page_height:
#                     total_page2 = total_page2 + 1
#                 elif total_page1 <frame_page_height:
#                     total_page2 = total_page2 + 1
#                 else: 
#                     total_page2 = total_page2 + 2
#                     
#                 total_page = int(total_page2)
#                 if page == total_page:
#                     frame_page_height2 = frame_page_height - consigning_heights - blank_height
#                 else:
#                     frame_page_height2 = 379.22 - consigning_heights - blank_height
#                 
#                 rml_res += header(o)
# 
#                 rml_res += """
#                         <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                                 </td>
#                             </tr>
#                         </blockTable>
#                         """
#                 rml_res += middle(o)
#                 consigning_heights = 0
#                 len_consigning = 0
#                 
#                 if len_consign > 0:
#                     if len_consign < 3:
#                         while (len_consigning < (len_consign+1)):
#                             len_lines_consigning = []
#                             len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
#                             Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
#                             consigning_heights += Total_consigning_line
#                             rml_res += """
#                                      <blockTable style="Tableau1" rowHeights=" """+str(Total_consigning_line)+""" " colWidths=" """ +str(consigning_width)+ """ " >
#                                         <tr>
#                                             <td>
#                                                 <para style="terp_default_8">""" +str (consigning_lines[len_consigning]) + """</para>
#                                             </td>
#                                         </tr>
#                                     </blockTable>"""
#                             len_consigning += 1
#                     else:
#                         while (len_consigning < 3):
#                             len_lines_consigning = []
#                             len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
#                             Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
#                             consigning_heights += Total_consigning_line
#                             rml_res += """
#                                      <blockTable style="Tableau1" rowHeights=" """+str(Total_consigning_line)+""" " colWidths=" """ +str(consigning_width)+ """ " >
#                                         <tr>
#                                             <td>
#                                                 <para style="terp_default_8">""" +str (consigning_lines[len_consigning]) + """</para>
#                                             </td>
#                                         </tr>
#                                     </blockTable>"""
#                             len_consigning += 1
#                             
# 
#                 for l in o.move_lines:
#                     len_note_pn = len(l.note or "")
#                     len_note_pn_remark = 0
#                     if len_note_pn > 1:
#                         pn_note_lines = str(l.note or "").split('\n')
#                         while (len_note_pn_remark < 1):
#                             part_note = str(pn_note_lines[len_note_pn_remark])
#                             len_note_pn_remark += 1
#                     lines = []
#                     
#                     number_ += 1
#                     number_des = str(int(number_))
#                     number_des_width = 12.5
#                     lines.append(count_lines(str(number_des),number_des_width)) 
#                      
#                     so_number = str(l.sale_id.name)
#                     so_number_width = 120
#                     lines.append (count_lines(str(so_number), so_number_width))
#                     
#                     cust_po_no = str(l.client_order_ref)
#                     cust_po_no_width = 150
#                     lines.append(count_lines(str(cust_po_no), cust_po_no_width))
# 
#                     if len_note_pn > 0:
#                         description = str(l.product_id.default_code)+'\n'+str(part_note)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#                     else:
#                         description = str(l.product_id.default_code)+'\n' +"CUST P/N:" + str(l.product_customer_id.name)
#                     
#                     description_width = 200
#                     description_line = str(description).split('\n')
#                     line_des = []
#                     for a in description_line:
#                         line_des.append(count_lines(str(a),description_width))
#                     
#                     len_line_des = len(line_des)
#                     lds = 0
#                     lines_des_int = []
#                     while (lds < len_line_des):
#                         lines_des_int.append(int(line_des[lds]))
#                         lds += 1
#                     total_des_line = (sum(lines_des_int))
#                     lines.append(total_des_line)
#                     
#                     quantity = _qty_format(l.product_qty) +""" """ + str(l.product_uom.name)
#                     quantity_width = 72.5
#                     lines.append(count_lines(str(quantity), quantity_width))
#                     
#                     lines = sorted(lines)
#                     line_heights = (lines[(len(lines)-1)] * 12)
#                     total_height += line_heights
#                     
#                     rowHeights = str(line_heights)
#                     
#                     count_line += 1
#                     if total_height > frame_page_height2:
#                         consigning_heights = 0
#                         total_height = line_heights
#                         page += 1
#                         rml_res += """<pageBreak/>"""
#                         rml_res += header(o)
#                         rml_res += """
#                         <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
#                             <tr>
#                                 <td>
#                                     <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                                 </td>
#                             </tr>
#                         </blockTable>
#                         """
#                         rml_res += middle(o)
#                         if page == total_page:
#                             frame_page_height2 = frame_page_height - consigning_heights 
#                         else:
#                             frame_page_height2 = 379.22 - consigning_heights
#                             
#                     colWidths = str(number_des_width)+","+str(so_number_width)+","+str(cust_po_no_width)+","+str(description_width)+","+str(quantity_width)
#         
#                     rml_res +="""
#                     <blockTable style="Table_Content" rowHeights=" """+ rowHeights + """ " colWidths=" """+ colWidths + """ ">
#                         <tr>
#                             <td><para style="terp_default_8">""" + str(number_des) + """</para></td>
#                             <td><para style="terp_default_8">""" + str(so_number) + """ </para></td>
#                             <td><para style="terp_default_8">""" + str(cust_po_no) + """</para></td>
#                             <td><para style="terp_default_8">""" + str(description) + """</para></td>
#                             <td><para style="terp_default_Right_8">""" + str(quantity) + """</para></td>
#                         </tr>
#                     </blockTable>
#                     """
#             if page != total_page:
#                 page += 1
#                 consigning_heights = 0
#                 total_height = 0
#                 frame_page_height2 = frame_page_height
#                 rml_res += """<pageBreak/>"""
#                 rml_res += header(o)
#                 rml_res += """
#                     <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
#                         <tr>
#                             <td>
#                                 <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                             </td>
#                         </tr>
#                     </blockTable>
#                     """
#                 rml_res += middle(o)
#             residual_height = (frame_page_height2 - user_note_heights - consigning_heights - total_height) + blank_height 
#             rml_res += """
#                 <blockTable rowHeights=" """+ str(residual_height) + """ ">
#                     <tr><td><para style="P8"><font color="white"> </font></para></td></tr>
#                 </blockTable>
#             """
#             len_note = 0
#             user_note_heights = 0
#             if len_user_note > 0:
#                 if len_user_note < 3:
#                     while (len_note < (len_user_note + 1)):
#                         len_lines_usernote = []
#                         len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
#                         Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
#                         user_note_heights += Total_line_note
#                         len_note += 1
#                         rml_res += """
#                             <blockTable rowHeights=" """ +str(Total_line_note)+ """ " colWidths="555.0">
#                                 <tr>
#                                     <td>
#                                         <para style="terp_default_8">"""+str(user_note_lines[len_note])+"""</para>
#                                     </td>
#                                 </tr>
#                             </blockTable>
#                             """
#                 else:
#                     while (len_note < 3):
#                         len_lines_usernote = []
#                         len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
#                         Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
#                         user_note_heights += Total_line_note
#                         len_note += 1
#                         rml_res += """
#                             <blockTable rowHeights=" """ +str(Total_line_note)+ """ " colWidths="555.0">
#                                 <tr>
#                                     <td>
#                                         <para style="terp_default_8">"""+str(user_note_lines[len_note])+"""</para>
#                                     </td>
#                                 </tr>
#                             </blockTable>
#                             """
#             rml_res += footer(o)
#         rml="""
# <document filename="Delivery Order.pdf">
#     <template pageSize="(21.59cm, 27.94cm)" title="Delivery Order" author="Yanto Chen (yanto@maxmega.com)" allowSplitting="20">
#         <pageTemplate id="first">
#             <frame id="first" x1="0.3cm" y1="2.8cm" width="20.0cm" height="23.0cm"/>
#             <pageGraphics>"""
#         if (o.company_id and o.company_id.logo):
#             rml += """
#                     <image x="0.8cm" y="26.1cm" height="25.0">""" + o.company_id.logo + """</image>"""
#         rml += """
#                 <setFont name="DejaVu Sans" size="7"/>
#                 <fill color="black"/>
#                 <stroke color="black"/>
#                 """
#         if (o.company_id and o.company_id.rml_header1):
#             rml += """
#                     <drawRightString x="20cm" y="26.3cm">""" + str(o.company_id.rml_header1) + """</drawRightString>"""
# 
#         if (o.company_id and o.company_id.partner_id and o.company_id.partner_id.name):
#             rml += """
#                     <drawString x="9.3cm" y="26.7cm">""" + str(o.company_id.partner_id.name) + """</drawString>"""
# 
#         rml += """
#                 <drawString x="9.3cm" y="26.3cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].street) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].zip) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].city) or '') + """ - """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].country_id and o.company_id.partner_id.address[0].country_id.name) or '') + """</drawString>
#                 <drawString x="9.3cm" y="25.9cm">Phone:</drawString>
#             <drawRightString x="13.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].phone) or '') + """</drawRightString>
#             <drawString x="14.0cm" y="25.9cm">Mail:</drawString>
#             <drawRightString x="18.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].email) or '') + """</drawRightString>
# 
#             <!--page bottom-->
# 
#             <lines>0.5cm 1.95cm 20.2cm 1.95cm</lines>
#                 """
#         if (o.company_id and o.company_id.rml_footer1):
#             rml += """
#                     <drawCentredString x="10.5cm" y="1.6cm">""" + str(o.company_id.rml_footer1) + """</drawCentredString>"""
#         if (o.company_id and o.company_id.rml_footer2):
#             rml += """
#                     <drawCentredString x="10.5cm" y="1.15cm">""" + str(o.company_id.rml_footer2) + """</drawCentredString>"""
# 
#         rml += """
#             <drawCentredString x="10.5cm" y="0.7cm">Contact : """ + str(user_obj.browse(cr, uid, uid, context=None).name) + """ - Page: <pageNumber/> </drawCentredString>
#                 """
#         rml += """
#             </pageGraphics>
#         </pageTemplate>
#     </template>
#     <stylesheet>
#         <blockTableStyle id="Tableau1">
#             <blockAlignment value="LEFT"/>
#             <blockValign value="TOP"/>
#         </blockTableStyle>
#         <blockTableStyle id="Tableau2">
#             <blockAlignment value="LEFT"/>
#             <blockValign value="TOP"/>
#         </blockTableStyle>
#         <blockTableStyle id="Move_Line_Header">
#             <blockAlignment value="LEFT"/>
#             <blockValign value="TOP"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="4,-1" stop="4,-1"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="0,-1" stop="0,-1"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="1,-1" stop="1,-1"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="2,-1" stop="2,-1"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="3,-1" stop="3,-1"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="4,-1" stop="4,-1"/>
#         </blockTableStyle>
#         <blockTableStyle id="Table_Content">
#           <blockAlignment value="LEFT"/>
#           <blockValign value="TOP"/>
#         </blockTableStyle>
#         <blockTableStyle id="Table_Country_Detail">
#             <blockAlignment value="LEFT"/>
#             <blockValign value="TOP"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="3,0" stop="3,0"/>
#             <lineStyle kind="LINEABOVE" colorName="#000000" start="4,0" stop="4,0"/>
#         </blockTableStyle>
#         <blockTableStyle id="Table_Page_Number">
#             <blockAlignment value="RIGHT"/>
#             <blockValign value="TOP"/>
#         </blockTableStyle>
#         <blockTableStyle id="Table_Signature">
#             <blockAlignment value="RIGHT"/>
#             <blockValign value="TOP"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="0,0" stop="0,0"/>
#             <lineStyle kind="LINEBELOW" colorName="#000000" start="2,0" stop="2,0"/>
#         </blockTableStyle>
#     <initialize>
#         <paraStyle name="all" alignment="justify"/>
#     </initialize>
#         <paraStyle name="P8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_tblheader_General_Right" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_tblheader_General_Centre" fontName="Helvetica-Bold" fontSize="8.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_9_Italic_Bold" fontName="Helvetica-BoldOblique" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_9" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_Bold_8" fontName="Helvetica-Bold" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_Right_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
#         <paraStyle name="terp_default_Centre_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
#         <images/>
#     </stylesheet>
#     <story>"""
#         rml += rml_res + """
#   </story>
# </document>"""
#         report_type = datas.get('report_type', 'pdf')
#         create_doc = self.generators[report_type]
#         pdf = create_doc(rml, title=self.title)
#         return (pdf, report_type)
# maxmega_picking_do('report.max.stock.picking.do', 'stock.picking','','')

report_sxw.report_sxw(
    'report.max.stock.picking.do',
    'stock.picking',
    'addons/maxmega_report_addons/report/picking_do.rml',
    parser=maxmega_picking_do, header=False)