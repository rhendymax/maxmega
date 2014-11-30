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
from tools import amount_to_text_en
import locale
locale.setlocale(locale.LC_ALL, '')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class maxmega_sale_order(report_rml):

    def create(self, cr, uid, ids, datas, context):
        pool           = pooler.get_pool(cr.dbname)
        so_obj         = pool.get('sale.order')
        user_obj       = pool.get('res.users')
        so_ids         = ids
        rml_res        = ''
         
         
        def _number_format(amount):
            res = {'amount': amount}
            return locale.format("%(amount).5f", res,1)
         
        def _number_format_total(amount):
            res = {'amount': amount}
            return locale.format("%(amount).2f", res,1)
 
        def _qty_format(qty1):
            q1 = {'qty1' : qty1}
            return locale.format("%(qty1).f", q1,1)
         
        def header(o):
            header = """
            <blockTable colWidths="257.0,38.00,260.0" style="Tableau1">
                <tr>
                    <td>
                        <blockTable colWidths="257.0" rowHeights="100.0,100.0" style="Tableau2">
                            <tr>
                                <td>
                                    <para style="terp_default_8">
                                    <font color="white"> </font>
                                    </para>
                                    <para style="terp_default_Bold_8">BILL TO :</para>
                                    <para style="terp_default_8">""" + str((o.partner_id and o.partner_id.title and o.partner_id.title.name) or '') + """ """ + str((o.partner_id and o.partner_id.name) or '') +  """</para>"""
            disaddress = False
            if o.partner_order_id:
                address = o.partner_order_id
                address_format = address.country_id and address.country_id.address_format or \
                     '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
                args = {
                    'state_code': address.state_id and address.state_id.code or '',
                    'state_name': address.state_id and address.state_id.name or '',
                    'country_code': address.country_id and address.country_id.code or '',
                    'country_name': address.country_id and address.country_id.name or '',
                }
                address_field = ['title', 'street', 'street2', 'zip', 'city']
                for field in address_field :
                    args[field] = getattr(address, field) or ''
                disaddress = address_format % args
            if disaddress:
                header += """ <para style="terp_default_8">""" + str(disaddress) + """</para>
                 
                """
            if (o.partner_order_id and o.partner_order_id.phone):
                header += """
                    <para style="terp_default_8">Tél. : """ + str (o.partner_order_id.phone) + """</para> """
            if (o.partner_order_id and o.partner_order_id.fax):
                header += """
                    <para style="terp_default_8">Fax : """ + str (o.partner_order_id.fax) + """</para>"""
             
            attention = False
            if (o.partner_order_id and o.partner_order_id.name):
                attention = str(o.partner_order_id.name)
            if (o.partner_order_id and o.partner_order_id.email):
                if attention:
                    attention += ' ' + str(o.partner_order_id.email)
                else:
                    attention = str(o.partner_order_id.email)
            if attention:
                header += """
                    <para style="terp_default_8">Attn : """ + attention + """</para> """
            header += """
                     
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <para style="terp_default_Bold_8">SHIP TO :</para>"""
                                     
            if (o.partner_shipping_id.name):
                header += """
                    <para style="terp_default_8">""" + str (o.partner_shipping_id.name) + """</para> """
            if (o.partner_shipping_id and o.partner_shipping_id.partner_id.name):
                header += """
                    <para style="terp_default_8">""" + str (o.partner_shipping_id and o.partner_shipping_id.partner_id.name)+"""</para> """
 
            disaddress2 = False
            if o.partner_shipping_id:
                address2 = o.partner_shipping_id
                address_format2 = address2.country_id and address2.country_id.address_format or \
                     '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
                args2 = {
                    'state_code': address2.state_id and address2.state_id.code or '',
                    'state_name': address2.state_id and address2.state_id.name or '',
                    'country_code': address2.country_id and address2.country_id.code or '',
                    'country_name': address2.country_id and address2.country_id.name or '',
                }
                address_field2 = ['title', 'street', 'street2', 'zip', 'city']
                for field2 in address_field2:
                    args2[field2] = getattr(address2, field2) or ''
                disaddress2 = address_format2 % args2
 
 
            if (disaddress2):
                header += """            <para style="terp_default_8">""" + str(disaddress2) + """</para>
                                        """
             
            if (o.partner_shipping_id and o.partner_shipping_id.phone):
                header += """            <para style="terp_default_8">Tél  :""" + str(o.partner_shipping_id.phone) + """</para>
                                        """
            if (o.partner_shipping_id and o.partner_shipping_id.fax):
                header += """            <para style="terp_default_8">Fax  :""" + str(o.partner_shipping_id.fax) + """</para>
                                        """
             
            attention2 = False
            if (o.partner_shipping_id and o.partner_shipping_id.name):
                attention2 = str(o.partner_shipping_id.name)
            if (o.partner_shipping_id and o.partner_shipping_id.email):
                if attention2:
                    attention2 += ' ' + str(o.partner_shipping_id.email)
                else:
                    attention2 = str(o.partner_shipping_id.email)
   
            if attention2:
                header += """
                    <para style="terp_default_8">Attn : """ + attention2 + """</para> """
 
            header += """
                                </td>
                            </tr>
                        </blockTable>
                    </td>
                    <td>
                        <para style="terp_default_8">
                            <font color="white"> </font>
                        </para>
                    </td>
                    <td>
                        <blockTable colWidths="120.0,140.0" rowHeights="12.00,145" style="Tableau2">
                            <tr>
                                <td>
                                    <para style="terp_default_9_Italic_Bold">SALE ORDER</para>
                                </td>
                                <td>
                                    <para style="terp_default_8">
                                    <font color="white"> </font>
                                    </para>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <para style="terp_default_Bold_8">SO NO</para>
                                    <para style="terp_default_Bold_8">SO DATE</para>
                                    <para style="terp_default_Bold_8">GST REG NO</para>
                                    <para style="terp_default_Bold_8">SHIPMENT METHOD</para>
                                    <para style="terp_default_Bold_8">SHIPMENT TERM</para>
                                    <para style="terp_default_Bold_8">CUSTOMER PO</para>
                                    <para style="terp_default_Bold_8">SALESMAN</para>
                                    <para style="terp_default_Bold_8">PAYMENT TERM</para>
                                </td>
                                <td>
                                    <para style="terp_default_8">:""" + str(o.name or '' ) + """</para>"""
            fr_date = str(o.date_order[0:10])
            conv = time.strptime(fr_date, "%Y-%m-%d")
            date_order = time.strftime("%d-%b-%Y", conv)
 
            header += """
                                    <para style="terp_default_8">:""" + str(date_order) + """</para>
                                    <para style="terp_default_8">:""" + str((o.company_id and o.company_id.company_registry) or '') + """</para>
                                    <para style="terp_default_8">:""" + str(o.ship_method_id and o.ship_method_id.name or '') + """</para>
                                    <para style="terp_default_8">:""" + str(o.fob_id and o.fob_id.description or '') + """</para>
                                    <para style="terp_default_8">:""" + str(o.client_order_ref) + """</para>
                                    <para style="terp_default_8">:""" + str(o.user_id and o.user_id.name) + """</para>
                                    <para style="terp_default_8">:""" + str(o.sale_term_id and o.sale_term_id.name or '') + """</para>
                                </td>
                            </tr>
                        </blockTable>
                    </td>
                </tr>
            </blockTable>"""
            return header
         
        def middle(o):
 
            middle ="""
                <blockTable colWidths="12.5,272.5,62.5,70.0,62.5,75.0" rowHeights="24.0" repeatRows="1" style="Table_Header_Pur_ord_Line">
                    <tr>
                        <td>
                            <para style="terp_tblheader_General_Centre">NO</para>
                        </td>
                        <td>
                            <para style="terp_tblheader_General_Centre">ITEM DESCRIPTION</para>
                        </td>
                        <td>
                            <para style="terp_tblheader_General_Centre">DELIVERY DATE</para>
                        </td>
                        <td>
                            <para style="terp_tblheader_General_Centre">QTY</para>
                        </td>
                        <td>
                        <para style="terp_tblheader_General_Centre">UNIT PRICE """+str (o.pricelist_id.currency_id.name or '' )+"""</para>
                        </td>
                        <td>
                        <para style="terp_tblheader_General_Centre">TOTAL AMOUNT """+str (o.pricelist_id.currency_id.name or '' )+"""</para>
                        </td>
                    </tr>
                </blockTable>"""
            return middle
     
         
        def footer(o):
            amount_untaxed = _number_format_total(o.amount_untaxed)
            amount_tax = _number_format_total(o.amount_tax)
            amount_total = _number_format_total(o.amount_total)
            amt_en = amount_to_text_en.amount_to_text(o.amount_total,'en',o.pricelist_id.currency_id.name)
            footer = """
                     
                    <blockTable colWidths="290.0,145.0,20.0,100.0" rowHeights="60.0" style="Table_All_Total_Detail">
                    <tr>
                        <td>
                            <para style="terp_default_Bold_8">ISSUE BY</para>
                           
                             
                        </td>
                        <td>
                            <para style="terp_default_Bold_8">SUBTOTAL</para>
                            """
            fiscal = (o.fiscal_position and o.fiscal_position.name) or False
            if fiscal:
                txt = fiscal
            else:
                txt = "GST 7%"
            footer += """
                            <para style="terp_default_Bold_8">""" + str(txt) + """</para>
                            <para style="terp_default_8">
                                <font color="white"> </font>
                            </para>
                            <para style="terp_default_Bold_8">TOTAL AMOUNT</para>
                             
                        </td>
                        <td>
                            <para style="terp_default_8">:</para>
                            <para style="terp_default_8">:</para>
                            <para style="terp_default_8">
                                <font color="white"> </font>
                            </para>
                            <para style="terp_default_8">:</para>
 
                        </td>
                        <td>
                            <para style="terp_default_Right_8">"""+str (amount_untaxed)+""" """+str (o.pricelist_id.currency_id.symbol or '')+"""</para>
                            <para style="terp_default_Right_8">"""+str (amount_tax)+""" """+str (o.pricelist_id.currency_id.symbol or '' )+"""</para>
                            <illustration width="150" height="11">
                            <lineMode width ="1.0"/>
                            <lines>-6 5 95 5</lines>
                            </illustration>
                            <para style="terp_tblheader_General_Right">"""+str (amount_total)+""" """+str (o.pricelist_id.currency_id.symbol or '' )+"""</para>
                            <illustration width="150" height="11">
                            <lineMode width ="1.0"/>
                            <lines>-6 5 95 5</lines>
                            <lineMode width ="1.0"/>
                            <lines>-6 3.2 95 3.2</lines>
                            </illustration>
                             
                        </td>
                    </tr>
                </blockTable>
                <blockTable colWidths="290.0,265.0" rowHeights="24.0" style="Tableau2">
                <tr>
                    <td>
                        <illustration width="150" height="8">
                        <lineMode width ="1.0"/>
                        <lines>-6 5 200 5</lines>
                        </illustration>
                        <para style="terp_default_9">MAXMEGA ELECTRONICS PTE LTD</para>
                        <para style="terp_default_Bold_8">This is a computer generated Sale Order</para>
                        <para style="terp_default_Bold_8">No Signature is required</para>
                         
                    </td>
                    <td>
                        <para style="terp_default_Right_8">"""+str (amt_en)+"""</para>
                    </td>
                </tr>
                </blockTable>
                """
            return footer
         
        def count_lines(string, width):
            line = len(string)/(width/6.25)
            line = math.ceil(line)
            if line == 0:
                line += 1
            return line
 
        obj_count = 0
        for o in so_obj.browse(cr, uid, so_ids):
            if obj_count > 1:
                rml_res += """<pageBreak/>"""
             
            consigning_width = 555
            user_note_width  = 555
            consigning_lines = str(o.header_so or "").split('\n')
            user_note_lines = str(o.footer_so or "").split('\n')
            len_consign = len(o.header_so or "")
            len_user_note = len(o.footer_so or "")
            Total_consigning_line = 0
            Total_line_note = 0
            len_line = len(o.order_line)
            blank_height = 2.69
            frame_page_height = 283.22
            frame_page_height2 = 379.22  
            total_height_p = 0
            total_page2 = 0
            line_height_p = 0
            number_p = 0
            total_height = 0
            count_line = 0
            number_ = 0
            line_heights = 0
            total_page1 = 0
            page = 1
            consigning_heights = 0
            len_note = 0
            len_consigning = 0
            user_note_heights = 0
             
            if len_consign > 0:
                if len_consign < 3:
                    while (len_consigning < (len_consign+1)):
                        len_lines_consigning = []
                        len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
                        Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
                        consigning_heights += Total_consigning_line
                        len_consigning += 1
                else:
                    while (len_consigning < 3):
                        len_lines_consigning = []
                        len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
                        Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
                        consigning_heights += Total_consigning_line
                        len_consigning += 1
                     
            if len_user_note > 0:
                if len_user_note < 3:
                    while (len_note < (len_user_note + 1)):
                        len_lines_usernote = []
                        len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
                        Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
                        user_note_heights += Total_line_note
                        len_note += 1
                else:
                    while (len_note < 3):
                        len_lines_usernote = []
                        len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
                        Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
                        user_note_heights += Total_line_note
                        len_note += 1
             
            if len_line < 1 :
                frame_page_height2 = 283.22
                rml_res += header(o)
                page = 1
                total_page = 1
                user_note_heights =  0.00
                rml_res += """
                    <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
                        <tr>
                            <td>
                                <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
                            </td>
                        </tr>
                    </blockTable>
                    """
                rml_res += middle(o)
                 
            else:
                for l in o.order_line: 
                    lines = []
     
                    number_p += 1
                    number_des = str(int(number_p))
                    number_des_width = 12.5
                    lines.append(count_lines(str(number_des),number_des_width)) 
                     
                    description = str(l.product_id.default_code)+ '\n' + "CPN:"+ str(l.product_customer_id.name)
                    description_width = 272.5
                    description_line = str(description).split('\n')
                    line_des = []
                    for a in description_line:
                        line_des.append(count_lines(str(a),description_width))
                     
                    len_line_des = len(line_des)
                    lds = 0
                    lines_des_int = []
                    while (lds < len_line_des):
                        lines_des_int.append(int(line_des[lds]))
                        lds += 1
                         
                         
                    total_des_line = (sum(lines_des_int))
                    lines.append(total_des_line)
     
                    date_des = str(l.customer_rescheduled_date[0:10])
                    date_des_width = 62.5
                    lines.append(count_lines(str(date_des), date_des_width))
                     
                    quantity = _qty_format(l.product_uom_qty) + str(l.product_uom.name)
                    quantity_width = 70.0
                    lines.append(count_lines(str(quantity), quantity_width))
                     
                    unit_price = _number_format(l.price_unit)
                    unit_price_width = 62.5
                    lines.append(count_lines(str(unit_price), unit_price_width))
                     
                    amount = _number_format_total(l.price_subtotal)
                    amount_width = 75.0
                    lines.append(count_lines(str(amount), amount_width))
 
                    lines = sorted(lines)
                    line_height_p = (lines[(len(lines)-1)] * 12.00)
                    total_height_p += line_height_p
                     
 
     
                total_height_p = total_height_p + consigning_heights + user_note_heights + blank_height
                total_page1 = total_height_p%frame_page_height2
                total_page2 = (total_height_p-total_page1)/frame_page_height2
                 
                if total_page1 == frame_page_height:
                    total_page2 = total_page2 + 1
                elif total_page1 <frame_page_height:
                    total_page2 = total_page2 + 1
                else: 
                    total_page2 = total_page2 + 2
     
                total_page = int(total_page2)
                 
                if page == total_page:
                    frame_page_height2 = 283.22 - consigning_heights - blank_height
                else:
                    frame_page_height2 = 379.22 - consigning_heights - blank_height
                 
                rml_res += header(o)
                rml_res += """
                        <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
                            <tr>
                                <td>
                                    <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
                                </td>
                            </tr>
                        </blockTable>
                        """
                rml_res += middle(o)
                consigning_heights = 0
                len_consigning = 0
 
                if len_consign > 0:
                    if len_consign < 3:
                        while (len_consigning < (len_consign+1)):
                            len_lines_consigning = []
                            len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
                            Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
                            consigning_heights += Total_consigning_line
                            rml_res += """
                                     <blockTable style="Tableau1" rowHeights=" """+str(Total_consigning_line)+""" " colWidths=" """ +str(consigning_width)+ """ " >
                                        <tr>
                                            <td>
                                                <para style="terp_default_8">""" +str (consigning_lines[len_consigning]) + """</para>
                                            </td>
                                        </tr>
                                    </blockTable>"""
                            len_consigning += 1
                    else:
                        while (len_consigning < 3):
                            len_lines_consigning = []
                            len_lines_consigning.append(count_lines(str(consigning_lines[len_consigning]),consigning_width))
                            Total_consigning_line = (len_lines_consigning[len(len_lines_consigning)-1]*12.00)
                            consigning_heights += Total_consigning_line
                            rml_res += """
                                     <blockTable style="Tableau1" rowHeights=" """+str(Total_consigning_line)+""" " colWidths=" """ +str(consigning_width)+ """ " >
                                        <tr>
                                            <td>
                                                <para style="terp_default_8">""" +str (consigning_lines[len_consigning]) + """</para>
                                            </td>
                                        </tr>
                                    </blockTable>"""
                            len_consigning += 1
 
                for l in o.order_line:
                    lines = []
                    number_ += 1
                    number_des = str(int(number_))
                    number_des_width = 12.5
                    lines.append(count_lines(str(number_des),number_des_width)) 
                      
                    description = str(l.product_id.default_code)+ '\n' + "CPN:" +str(l.product_customer_id.name)
                    description_width = 272.5
                    description_line = str(description).split('\n')
                    line_des = []
                    for a in description_line:
                        line_des.append(count_lines(str(a),description_width))
                     
                    len_line_des = len(line_des)
                    lds = 0
                    lines_des_int = []
                    while (lds < len_line_des):
                        lines_des_int.append(int(line_des[lds]))
                        lds += 1
                         
                         
                    total_des_line = (sum(lines_des_int))
                    lines.append(total_des_line)
     
                    date_des = str(l.customer_rescheduled_date[0:10])
                    date_des_width = 62.5
                    lines.append(count_lines(str(date_des), date_des_width))
                     
                    quantity = _qty_format(l.product_uom_qty)+ """ """ + str(l.product_uom.name)
                    quantity_width = 70.0
                    lines.append(count_lines(str(quantity), quantity_width))
                     
                    unit_price = _number_format(l.price_unit)
                    unit_price_width = 62.5
                    lines.append(count_lines(str(unit_price), unit_price_width))
                     
                    amount = _number_format_total(l.price_subtotal)
                    amount_width = 75.0
                    lines.append(count_lines(str(amount), amount_width))
     
                    lines = sorted(lines)
                    line_heights = (lines[(len(lines)-1)] * 12.0)
                    total_height += line_heights
                     
                    rowHeights = str(line_heights)
                    colWidths = str(number_des_width)+","+str(description_width)+","+str(date_des_width)+","+str(quantity_width)+","+str(unit_price_width)+","+str(amount_width)
                     
                    count_line += 1
                     
                    if total_height > frame_page_height2:
                        consigning_heights = 0
                        total_height = line_heights
                        page += 1
                        rml_res += """<pageBreak/>"""
                        rml_res += header(o)
                        rml_res += """
                        <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
                            <tr>
                                <td>
                                    <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
                                </td>
                            </tr>
                        </blockTable>
                        """
                        rml_res += middle(o)
                        if page == total_page:
                            frame_page_height2 = 283.22 - consigning_heights 
                        else:
                            frame_page_height2 = 379.22 - consigning_heights
                             
                    rml_res +="""
                        <blockTable style="Table_Content" rowHeights=" """+ rowHeights +""" " colWidths=" """+ colWidths + """ ">
                            <tr>
                                <td><para style="terp_default_Centre_8">""" + str(number_des) + """</para></td>
                                <td><para style="terp_default_8">""" + str(description) + """</para></td>
                                <td><para style="terp_default_Right_8">""" + str(date_des) + """</para></td>
                                <td><para style="terp_default_Right_8">""" + str(quantity) + """ </para></td>
                                <td><para style="terp_default_Right_8">""" + str(unit_price) + """</para></td>
                                <td><para style="terp_default_Right_8">""" + str(amount) + """</para></td>
                            </tr>
                        </blockTable>
                    """
            if page != total_page:
                page += 1
                total_height = 0
                frame_page_height2 = 283.22
                rml_res += """<pageBreak/>"""
                rml_res += header(o)
                rml_res += """
                    <blockTable style="Table_Page_Number" rowHeights="12.00" colWidths="555.0">
                        <tr>
                            <td>
                                <para style="terp_default_Right_8">Page """+str(page)+""" of """+str(total_page)+"""</para>
                            </td>
                        </tr>
                    </blockTable>
                    """
                rml_res += middle(o)
                 
            residual_height = (frame_page_height2 - user_note_heights-consigning_heights-total_height) + blank_height 
            rml_res += """
                <blockTable rowHeights=" """+ str(residual_height) + """ ">
                    <tr><td><para style="P8"><font color="white"> </font></para></td></tr>
                </blockTable>
            """
            len_note = 0
            user_note_heights = 0
            if len_user_note > 0:
                if len_user_note < 3:
                    while (len_note < (len_user_note + 1)):
                        len_lines_usernote = []
                        len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
                        Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
                        user_note_heights += Total_line_note
                        len_note += 1
                        rml_res += """
                            <blockTable rowHeights=" """ +str(Total_line_note)+ """ " colWidths="555.0">
                                <tr>
                                    <td>
                                        <para style="terp_default_8">"""+str(user_note_lines[len_note])+"""</para>
                                    </td>
                                </tr>
                            </blockTable>
                            """
                else:
                    while (len_note < 3):
                        len_lines_usernote = []
                        len_lines_usernote.append(count_lines(str(user_note_lines[len_note]),user_note_width))
                        Total_line_note = (len_lines_usernote[len(len_lines_usernote)-1]*12.0)
                        user_note_heights += Total_line_note
                        len_note += 1
                        rml_res += """
                            <blockTable rowHeights=" """ +str(Total_line_note)+ """ " colWidths="555.0">
                                <tr>
                                    <td>
                                        <para style="terp_default_8">"""+str(user_note_lines[len_note])+"""</para>
                                    </td>
                                </tr>
                            </blockTable>
                            """
 
            rml_res += footer(o)
 
        rml="""
<document filename="Sale Order.pdf">
    <template pageSize="(21.59cm, 27.94cm)" title="Sale Order" author="Yanto Chen" allowSplitting="20">
        <pageTemplate id="first">
            <frame id="first" x1="0.3cm" y1="2.8cm" width="20.0cm" height="23.0cm"/>
            <pageGraphics>"""
        if (o.company_id and o.company_id.logo):
            rml += """
                    <image x="0.8cm" y="26.1cm" height="25.0">""" + o.company_id.logo + """</image>"""
        rml += """
                <setFont name="DejaVu Sans" size="7"/>
                <fill color="black"/>
                <stroke color="black"/>
                """
        if (o.company_id and o.company_id.rml_header1):
            rml += """
                    <drawRightString x="20cm" y="26.3cm">""" + str(o.company_id.rml_header1) + """</drawRightString>"""
 
        if (o.company_id and o.company_id.partner_id and o.company_id.partner_id.name):
            rml += """
                    <drawString x="9.3cm" y="26.7cm">""" + str(o.company_id.partner_id.name) + """</drawString>"""
 
        rml += """
                <drawString x="9.3cm" y="26.3cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].street) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].zip) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].city) or '') + """ - """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].country_id and o.company_id.partner_id.address[0].country_id.name) or '') + """</drawString>
                <drawString x="9.3cm" y="25.9cm">Phone:</drawString>
            <drawRightString x="13.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].phone) or '') + """</drawRightString>
            <drawString x="14.0cm" y="25.9cm">Mail:</drawString>
            <drawRightString x="18.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].email) or '') + """</drawRightString>
 
            <!--page bottom-->
 
            <lines>0.5cm 1.95cm 20.2cm 1.95cm</lines>
                """
        if (o.company_id and o.company_id.rml_footer1):
            rml += """
                    <drawCentredString x="10.5cm" y="1.6cm">""" + str(o.company_id.rml_footer1) + """</drawCentredString>"""
        if (o.company_id and o.company_id.rml_footer2):
            rml += """
                    <drawCentredString x="10.5cm" y="1.15cm">""" + str(o.company_id.rml_footer2) + """</drawCentredString>"""
 
        rml += """
            <drawCentredString x="10.5cm" y="0.7cm">Contact : """ + str(user_obj.browse(cr, uid, uid, context=None).name) + """ - Page: <pageNumber/> </drawCentredString>
                """
        rml += """
            </pageGraphics>
        </pageTemplate>
    </template>
    <stylesheet>
        <blockTableStyle id="Tableau1">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Tableau2">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Table_Header_Pur_ord_Line">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="4,-1" stop="4,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="5,-1" stop="5,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="5,-1" stop="6,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,-1" stop="0,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,-1" stop="1,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,-1" stop="2,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,-1" stop="3,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="4,-1" stop="4,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,-1" stop="5,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,-1" stop="6,-1"/>
        </blockTableStyle>
        <blockTableStyle id="Table_Content">
          <blockAlignment value="LEFT"/>
          <blockValign value="TOP"/>
        </blockTableStyle>
        <!--lineStyle kind="LINEBELOW" colorName="#e6e6e6"/-->
        <blockTableStyle id="Table_Page_Number">
            <blockAlignment value="RIGHT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Table_All_Total_Detail">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,0" stop="3,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,2" stop="3,2"/>
        </blockTableStyle>
        <initialize>
            <paraStyle name="all" alignment="justify"/>
        </initialize>
        <paraStyle name="P8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="0.0"/>
        <paraStyle name="terp_tblheader_General_Right" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_tblheader_General_Centre" fontName="Helvetica-Bold" fontSize="8.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_9_Italic_Bold" fontName="Helvetica-BoldOblique" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_9" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_Bold_8" fontName="Helvetica-Bold" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_Right_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
        <paraStyle name="terp_default_Centre_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
        <images/>
    </stylesheet>
    <story>"""
        rml += rml_res + """
  </story>
</document>"""
        report_type = datas.get('report_type', 'pdf')
        create_doc = self.generators[report_type]
        pdf = create_doc(rml, title=self.title)
        return (pdf, report_type)
maxmega_sale_order('report.max.sale.order', 'sale.order','','')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

