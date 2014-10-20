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

#class maxmega_tax_invoice(report_rml):
#    def create(self, cr, uid, ids, datas, context):
#        pool           = pooler.get_pool(cr.dbname)
#        ti_obj         = pool.get('account.invoice')
#        user_obj       = pool.get('res.users')
#        ti_ids         = ids
#        rml_res        = ''
#
#        def _number_format(amount):
#            res = {'amount': amount}
#            return locale.format("%(amount).2f", res,1)
#        
#        def _qty_format(qty1):
#            q1 = {'qty1' : qty1}
#            return locale.format("%(qty1).f", q1,1)
#        
#        
#        
#        def header(o):
#            header = """
#            <blockTable colWidths="257.0,78.00,240.0" style="Tableau1">
#                <tr>
#                    <td>
#                        <blockTable colWidths="257.0" rowHeights="100.0,100.0" style="Tableau2">
#                            <tr>
#                                <td>
#                                    <para style="terp_default_9">
#                                    <font color="white"> </font>
#                                    </para>
#                                    <para style="terp_default_Bold_9">BILL TO :</para>
#                                    <para style="terp_default_9">""" + str((o.partner_id and o.partner_id.title and o.partner_id.title.name) or '') + """ """ + str((o.partner_id and o.partner_id.name) or '') +  """</para>"""
#            disaddress = False
#            if o.address_invoice_id:
#                address = o.address_invoice_id
#                address_format = address.country_id and address.country_id.address_format or \
#                     '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
#                args = {
#                    'state_code': address.state_id and address.state_id.code or '',
#                    'state_name': address.state_id and address.state_id.name or '',
#                    'country_code': address.country_id and address.country_id.code or '',
#                    'country_name': address.country_id and address.country_id.name or '',
#                }
#                address_field = ['title', 'street', 'street2', 'zip', 'city']
#                for field in address_field :
#                    args[field] = getattr(address, field) or ''
#                disaddress = address_format % args
#            if disaddress:
#                header += """            <para style="terp_default_9">""" + str(disaddress) + """</para>
#                                        """
#            if (o.address_invoice_id and o.address_invoice_id.phone):
#                header += """
#                    <para style="terp_default_9">Tél. : """ + str (o.address_invoice_id.phone) + """</para> """
#            if (o.address_invoice_id and o.address_invoice_id.fax):
#                header += """
#                    <para style="terp_default_9">Fax : """ + str (o.address_invoice_id.fax) + """</para> """
#            attention = False
#            if (o.address_invoice_id and o.address_invoice_id.name):
#                attention = str(o.address_invoice_id.name)
#            if (o.address_invoice_id and o.address_invoice_id.email):
#                if attention:
#                    attention += ' ' + str(o.address__invoice_id.email)
#                else:
#                    attention = str(o.address_invoice_id.email)
#            if attention:
#                header += """
#                    <para style="terp_default_9">Attn : """ + attention + """</para> """
#            header += """
#                                </td>
#                            </tr>
#                            <tr>
#                                <td>
#                                    <para style="terp_default_Bold_9">SHIP TO :</para>
#                                    
#                                </td>
#                            </tr>
#                        </blockTable>
#                    </td>
#                    <td>
#                        <para style="terp_default_9">
#                            <font color="white"> </font>
#                        </para>
#                    </td>
#                    <td>
#                        <blockTable colWidths="120.0,120.0" rowHeights="16.11,145" style="Tableau2">
#                            <tr>
#                                <td>
#                                    <para style="terp_default_10_Italic_Bold">TAX INVOICE</para>
#                                </td>
#                                <td>
#                                    <para style="terp_default_9">
#                                    <font color="white"> </font>
#                                    </para>
#                                </td>
#                            </tr>
#                            <tr>
#                                <td>
#                                    <para style="terp_default_Bold_8">GST REG.NO</para>
#                                    <para style="terp_default_Bold_8">NO</para>
#                                    <para style="terp_default_Bold_8">DATE</para>
#                                    <para style="terp_default_Bold_8">D/O NO</para>
#                                    <para style="terp_default_Bold_8">REFERENCE NO</para>
#                                    <para style="terp_default_Bold_8">CUSTOMER CODE</para>
#                                    <para style="terp_default_Bold_8">SHIPMENT METHOD</para>
#                                    <para style="terp_default_Bold_8">SHIPMENT TERM</para>
#                                    <para style="terp_default_Bold_8">PAYMENT TERM</para>
#                                    <para style="terp_default_Bold_8">SALES PERSON</para>
#                                </td>
#                                <td>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                    <para style="terp_default_8">:</para>
#                                </td>
#                            </tr>
#                        </blockTable>
#                    </td>
#                </tr>
#            </blockTable>"""
#            return header
#        
#        def middle(o):
#
#                middle ="""
#                <blockTable colWidths="20.0,200.0,70.0,100.0,65.0,100.0" rowHeights="25.0" repeatRows="1" style="Table_Header_tax_inv_Line">
#                    <tr>
#                        <td>
#                            <para style="terp_tblheader_General_Centre">NO</para>
#                        </td>
#                        <td>
#                            <para style="terp_tblheader_General_Centre">ITEM DESCRIPTION</para>
#                        </td>
#                        <td>
#                            <para style="terp_tblheader_General_Centre">CUSTOMER P/O NO</para>
#                        </td>
#                        <td>
#                            <para style="terp_tblheader_General_Centre">QTY</para>
#                        </td>
#                        <td>
#                        <para style="terp_tblheader_General_Centre">UNIT PRICE """+str (o.currency_id.name or '' )+"""</para>
#                        </td>
#                        <td>
#                        <para style="terp_tblheader_General_Centre">TOTAL AMOUNT """+str (o.currency_id.name or '' )+"""</para>
#                        </td>
#                    </tr>
#                </blockTable>"""
#                return middle
#        
#        def footer(o):
#            footer= """ 
#            <blockTable colWidths="555.0" style="Table_All_Total_Detail">
#                    <tr>
#                        <td>
#                            <para style="terp_default_Bold_9">SGD EXCHANGE RATE @</para>
#                        </td>
#                    </tr>
#            </blockTable>
#            <blockTable colWidths="100.0,10.0,137.0,78.0,100.0,10.0,120.0" rowHeights="12.11,12.11,12.11,12.11" style="Table_All_Total_Detail1">
#                    <tr>
#                        <td>
#                            <para style="terp_default_Bold_9">TOTALL IN SGD</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                        <td></td>
#                        <td>
#                            <para style="terp_default_Bold_9">TOTALL IN SGD</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                    </tr>
#                    <tr>
#                        <td>
#                            <para style="terp_default_Bold_9">ZERO</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                        <td></td>
#                        <td>
#                            <para style="terp_default_Bold_9">ZERO</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                    </tr>
#                    <tr>
#                        <td>
#                            <para style="terp_default_Bold_9">TOTAL</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                        <td></td>
#                        <td>
#                            <para style="terp_default_Bold_9">TOTAL</para>
#                        </td>
#                        <td>:</td>
#                        <td></td>
#                    </tr>
#                    <tr>
#                        <td>
#                            <para style="terp_default_Bold_9">AMOUNT</para>
#                        </td>
#                        <td>:</td>
#                        <td>
#                            <illustration width="150" height="20">
#                            <lineMode width ="1.0"/>
#                            <lines>-6 5 132 5</lines>
#                            <lineMode width ="1.0"/>
#                            <lines>-6 3.2 132 3.2</lines>
#                            </illustration>
#                        </td>
#                        <td></td>
#                        <td>
#                            <para style="terp_default_Bold_9">AMOUNT</para>
#                        </td>
#                        <td>:</td>
#                        <td>
#                            <illustration width="150" height="20">
#                            <lineMode width ="1.0"/>
#                            <lines>-6 5 115 5</lines>
#                            <lineMode width ="1.0"/>
#                            <lines>-6 3.2 115 3.2</lines>
#                            </illustration>
#                        </td>
#                    </tr>
#            </blockTable>
#    
#                <blockTable colWidths="245.0,310.0" rowHeights="70.0,10.11" style="Table_Signature_Line">
#                    <tr>
#                         <td></td>
#                         <td>
#                            <para style="terp_default_9">
#                                <font color="white"> </font>
#                            </para>
#                        </td>
#                    </tr>
#                    <tr>
#                        <td>
#                            <para style="terp_default_9">MAXMEGA ELECTRONICS PTE LTD</para>
#                        </td>
#                        <td>
#                            <para style="terp_default_9">
#                                <font color="white"> </font>
#                            </para>
#                        </td>
#                        
#                    </tr>
#                    
#                </blockTable>
#                """
#            return footer
#        
#        def count_lines(string, width):
#            line = len(string)/(width*6)
#            line = math.ceil(line)
#            if line == 0:
#                line += 1
#            return line
#        
#        obj_count = 0
#        for o in ti_obj.browse(cr, uid, ti_ids):
#            obj_count += 1
#            if obj_count > 1:
#                rml_res += """<pageBreak/>"""
#                
#            len_line = len(o.invoice_line)
#            blank_height = 2.69
#            frame_page_height = 241.65
#            frame_page_height2 = 379.22
#            
#            count_line_p = 0
#            total_height_p = 0
#            total_page2 = 0
#            line_height_p = 0
#            number_p = 0
#            
#            for l in o.invoice_line: 
#                lines = []
#
#                number_p += 1
#                number_des = str(int(number_p))
#                number_des_width = 20
#                number_des_w = 0.52
#                lines.append(count_lines(str(number_des),number_des_w)) 
#                 
#                description = str(l.product_id.name)
#                description_width = 200
#                lines.append (count_lines(str(description), description_width))
#                
#                cust_po_no = """ """
#                cust_po_no_width = 70
#                lines.append(count_lines(str(cust_po_no), cust_po_no_width))
#                
#                quantity = _qty_format(l.quantity) + str(l.uos_id.name)
#                quantity_width = 100
#                lines.append(count_lines(str(quantity), quantity_width))
#                
#                unit_price = _number_format(l.price_unit)
#                unit_price_width = 65
#                lines.append(count_lines(str(unit_price), unit_price_width))
#                
#                amount = _number_format(l.price_subtotal)
#                amount_width = 100
#                lines.append(count_lines(str(amount), amount_width))
##                 one record is 0.6 cm
#                lines = sorted(lines)
#                line_height_p = (lines[(len(lines)-1)] * 16.11)
#                total_height_p += line_height_p
#                
#                count_line_p += 1
#            
#            total_page1 = total_height_p%frame_page_height2
#            total_page2 = (total_height_p-total_page1)/frame_page_height2
#             
#            if total_page1 == frame_page_height:
#                total_page2 = total_page2 + 1
#            elif total_page1 <frame_page_height:
#                total_page2 = total_page2 + 1
#            else: 
#                total_page2 = total_page2 + 2
#                
#            total_page = int(total_page2)
#            
#            page = 1
#            total_height = 0
#            count_line = 0
#            number_ = 0
#            line_heights = 0
#            rml_res += header(o)
#            rml_res += """
#                    <blockTable style="Table_Page_Number" rowHeights="16.11" colWidths="555.0">
#                        <tr>
#                            <td>
#                                <para style="terp_default_Right_9">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                            </td>
#                        </tr>
#                    </blockTable>
#                    """
#            rml_res += middle(o)
#            
#            for l in o.invoice_line:
#                lines = []
#                
#                number_ += 1
#                number_des = str(int(number_))
#                number_des_width = 20
#                number_des_w = 0.52 
#                lines.append(count_lines(str(number_des),number_des_w)) 
#                 
#                description = str(l.product_id.name)
#                description_width = 200
#                lines.append (count_lines(str(description), description_width))
#                
#                cust_po_no = """ """
#                cust_po_no_width = 70
#                lines.append(count_lines(str(cust_po_no), cust_po_no_width))
#                
#                quantity = _qty_format(l.quantity) +""" """ + str(l.uos_id.name)
#                quantity_width = 100
#                lines.append(count_lines(str(quantity), quantity_width))
#                
#                unit_price = _number_format(l.price_unit)
#                unit_price_width = 65
#                lines.append(count_lines(str(unit_price), unit_price_width))
#                
#                amount = _number_format(l.price_subtotal)
#                amount_width = 100
#                lines.append(count_lines(str(amount), amount_width))
#                
##                 one record is 0.6 cm
#                lines = sorted(lines)
#                line_heights = (lines[(len(lines)-1)] * 16.11)
#                total_height += line_heights
#                
#                count_line += 1
#                
#                if page != total_page:
#                    if total_height > frame_page_height2:
#                            total_height = 16.11
#                            page += 1
#                            rml_res += """<pageBreak/>"""
#                            rml_res += header(o)
#                            rml_res += """
#                            <blockTable style="Table_Page_Number" rowHeights="16.11" colWidths="555.0">
#                                <tr>
#                                    <td>
#                                        <para style="terp_default_Right_9">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                                    </td>
#                                </tr>
#                            </blockTable>
#                            """
#                            rml_res += middle(o)
#                    elif total_height > frame_page_height:
#                            total_height = 16.11
#                            page += 1
#                            rml_res += """<pageBreak/>"""
#                            rml_res += header(o)
#                            rml_res += """
#                            <blockTable style="Table_Page_Number" rowHeights="16.11" colWidths="555.0">
#                                <tr>
#                                    <td>
#                                        <para style="terp_default_Right_9">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                                    </td>
#                                </tr>
#                            </blockTable>
#                            """
#                            rml_res += middle(o)
#                if page == total_page:
#                    if total_height > frame_page_height:
#                        total_height = 16.11
#                        page += 1
#                        rml_res += """<pageBreak/>"""
#                        rml_res += header(o)
#                        rml_res += """
#                        <blockTable style="Table_Page_Number" rowHeights="16.11" colWidths="555.0">
#                            <tr>
#                                <td>
#                                    <para style="terp_default_Right_9">Page """+str(page)+""" of """+str(total_page)+"""</para>
#                                </td>
#                            </tr>
#                        </blockTable>
#                        """
#                        rml_res += middle(o)
#
#                colWidths = str(number_des_width)+","+str(description_width)+","+str(cust_po_no_width)+","+str(quantity_width)+","+str(unit_price_width)+","+str(amount_width)
#                
#                rml_res +="""
#                <blockTable style="Table_Content" rowHeights="16.11" colWidths=" """+ colWidths + """ ">
#                    <tr>
#                        <td><para style="terp_default_Centre_9">""" + str(number_des) + """</para></td>
#                        <td><para style="terp_default_9">""" + str(description) + """</para></td>
#                        <td><para style="tterp_default_Right_9">""" + str(cust_po_no) + """</para></td>
#                        <td><para style="terp_default_Right_9">""" + str(quantity) + """</para></td>
#                        <td><para style="terp_default_Right_9">""" + str(unit_price) + """</para></td>
#                        <td><para style="terp_default_Right_9">""" + str(amount) + """</para></td>
#                    </tr>
#                </blockTable>
#                """
#            residual_height = (frame_page_height - total_height) + blank_height 
#            residual_heights = str(residual_height)
#            rml_res += """
#                <blockTable rowHeights=" """+ (residual_heights) + """ ">
#                    <tr><td><para style="P8"><font color="white"> </font></para></td></tr>
#                </blockTable>
#            """
#            rml_res += footer(o)
#           
#        rml="""
#<document filename="Invoices.pdf">
#  <template pageSize="(21.59cm, 27.94cm)" title="Invoices" author="Yanto Chen" allowSplitting="20">
#    <pageTemplate id="first">
#      <frame id="first" x1="0.3cm" y1="2.8cm" width="20.0cm" height="23.0cm"/>
#            <pageGraphics>"""
#        if (o.company_id and o.company_id.logo):
#            rml += """
#                    <image x="0.8cm" y="26.1cm" height="25.0">""" + o.company_id.logo + """</image>"""
#
#        rml += """
#                <setFont name="DejaVu Sans" size="7"/>
#                <fill color="black"/>
#                <stroke color="black"/>
#                """
#        if (o.company_id and o.company_id.rml_header1):
#            rml += """
#                    <drawRightString x="20cm" y="26.3cm">""" + str(o.company_id.rml_header1) + """</drawRightString>"""
#
#        if (o.company_id and o.company_id.partner_id and o.company_id.partner_id.name):
#            rml += """
#                    <drawString x="9.3cm" y="26.7cm">""" + str(o.company_id.partner_id.name) + """</drawString>"""
#
#        rml += """
#                <drawString x="9.3cm" y="26.3cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].street) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].zip) or '') + """ """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].city) or '') + """ - """ + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].country_id and o.company_id.partner_id.address[0].country_id.name) or '') + """</drawString>
#                <drawString x="9.3cm" y="25.9cm">Phone:</drawString>
#            <drawRightString x="13.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].phone) or '') + """</drawRightString>
#            <drawString x="14.0cm" y="25.9cm">Mail:</drawString>
#            <drawRightString x="18.0cm" y="25.9cm">""" + str((o.company_id and o.company_id.partner_id and o.company_id.partner_id.address and o.company_id.partner_id.address[0].email) or '') + """</drawRightString>
#
#            <!--page bottom-->
#
#            <lines>0.5cm 1.95cm 20.2cm 1.95cm</lines>
#                """
#        if (o.company_id and o.company_id.rml_footer1):
#            rml += """
#                    <drawCentredString x="10.5cm" y="1.6cm">""" + str(o.company_id.rml_footer1) + """</drawCentredString>"""
#        if (o.company_id and o.company_id.rml_footer2):
#            rml += """
#                    <drawCentredString x="10.5cm" y="1.15cm">""" + str(o.company_id.rml_footer2) + """</drawCentredString>"""
#
#        rml += """
#            <drawCentredString x="10.5cm" y="0.7cm">Contact : """ + str(user_obj.browse(cr, uid, uid, context=None).name) + """ - Page: <pageNumber/> </drawCentredString>
#                """
#
#        rml += """
#            </pageGraphics>
#    </pageTemplate>
#  </template>
#  <stylesheet>
#          <blockTableStyle id="Table_Page_Number">
#            <blockAlignment value="RIGHT"/>
#            <blockValign value="TOP"/>
#        </blockTableStyle>
#        <blockTableStyle id="Table_All_Total_Detail">
#            <blockAlignment value="LEFT"/>
#            <blockValign value="TOP"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,0" stop="3,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="4,0" stop="4,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,0" stop="5,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="6,0" stop="6,0"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,2" stop="2,2"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="6,2" stop="6,2"/>
#        </blockTableStyle>
#        <blockTableStyle id="Table_All_Total_Detail1">
#            <blockAlignment value="LEFT"/>
#            <blockValign value="TOP"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,2" stop="2,2"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="6,2" stop="6,2"/>
#        </blockTableStyle>
#        <blockTableStyle id="Tableau1">
#            <blockAlignment value="LEFT"/>
#            <blockValign value="TOP"/>
#        </blockTableStyle>
#        <blockTableStyle id="Table_Content">
#          <blockAlignment value="LEFT"/>
#          <blockValign value="TOP"/>
#        </blockTableStyle>
#        <blockTableStyle id="Table_Header_tax_inv_Line">
#            <blockAlignment value="LEFT"/>
#            <blockValign value="TOP"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="4,-1" stop="4,-1"/>
#            <lineStyle kind="LINEBELOW" colorName="#000000" start="5,-1" stop="5,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,-1" stop="0,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,-1" stop="1,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,-1" stop="2,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,-1" stop="3,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="4,-1" stop="4,-1"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,-1" stop="5,-1"/>
#        </blockTableStyle>
#        <blockTableStyle id="Tableau2">
#            <blockAlignment value="LEFT"/>
#            <blockValign value="TOP"/>
#        </blockTableStyle>
#        <blockTableStyle id="Table_Signature_Line">
#            <blockAlignment value="RIGHT"/>
#            <blockValign value="TOP"/>
#            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,1" stop="0,1"/>
#        </blockTableStyle>
#    <initialize>
#    <paraStyle name="all" alignment="justify"/>
#    </initialize>
#    <paraStyle name="Standard" fontName="Helvetica"/>
#    <paraStyle name="Text body" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
#    <paraStyle name="List" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
#    <paraStyle name="Table Contents" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
#    <paraStyle name="Table Heading" fontName="Helvetica" alignment="CENTER" spaceBefore="0.0" spaceAfter="6.0"/>
#    <paraStyle name="Caption" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="Index" fontName="Helvetica"/>
#    <paraStyle name="Heading" fontName="Helvetica" fontSize="15.0" leading="19" spaceBefore="12.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_header" fontName="Helvetica-Bold" fontSize="12.0" leading="15" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_default_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="Footer" fontName="Helvetica"/>
#    <paraStyle name="Horizontal Line" fontName="Helvetica" fontSize="6.0" leading="8" spaceBefore="0.0" spaceAfter="14.0"/>
#    <paraStyle name="Heading 9" fontName="Helvetica-Bold" fontSize="75%" leading="NaN" spaceBefore="12.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_tblheader_General" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_tblheader_Details" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
#   <paraStyle name="terp_default_Bold_8" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_tblheader_General_Centre" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_tblheader_General_Right" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_tblheader_Details_Centre" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_tblheader_Details_Right" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_default_Right_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_Centre_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_header_Right" fontName="Helvetica-Bold" fontSize="15.0" leading="19" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_header_Centre" fontName="Helvetica-Bold" fontSize="12.0" leading="15" alignment="CENTER" spaceBefore="12.0" spaceAfter="6.0"/>
#    <paraStyle name="terp_default_address" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="10.0" leading="13" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_Bold_9" rightIndent="0.0" leftIndent="-3.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_Centre_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_Right_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_Bold_Right_9" rightIndent="0.0" leftIndent="-3.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_White_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0" textColor="#ffffff"/>
#    <paraStyle name="terp_default_Note" rightIndent="0.0" leftIndent="9.0" fontName="Helvetica-Oblique" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="Table" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
#    <paraStyle name="User Index 10" rightIndent="0.0" leftIndent="127.0" fontName="Helvetica"/>
#    <paraStyle name="Preformatted Text" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="0.0" spaceAfter="0.0"/>
#     <paraStyle name="terp_default_10_Italic_Bold" fontName="Helvetica-BoldOblique" fontSize="10.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_8_Italic" fontName="Helvetica-Oblique" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    <paraStyle name="terp_default_8_Left" fontName="Helvetica" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
#    
#    <images/>
#  </stylesheet>
#  <story>"""
#        rml += rml_res + """
#  </story>
#</document>"""
#        report_type = datas.get('report_type', 'pdf')
#        create_doc = self.generators[report_type]
#        pdf = create_doc(rml, title=self.title)
#        return (pdf, report_type)
#maxmega_tax_invoice('report.max.maxmega.invoice', 'account.invoice','','')

class maxmega_tax_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(maxmega_tax_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_cust_po': self.get_cust_po,
        })

    def get_cust_po(self, invoice_id):
        cust_po_no = False
        invoice_qry = ''
        if invoice_id:
            invoice_qry = "AND ail.id = %s "%invoice_id
        else:
            invoice_qry = "AND ail.id IN (0) "
        self.cr.execute("select so.client_order_ref from account_invoice_line ail " \
                        "inner join stock_move sm on ail.stock_move_id = sm.id " \
                        "inner join sale_order_line sol on sm.sale_line_id = sol.id " \
                        "inner join sale_order so on so.id = sol.order_id " \
                        + invoice_qry)

        qry = self.cr.dictfetchall()
        if qry:
            for s in qry:
                if cust_po_no == False:
                    cust_po_no = str(s['client_order_ref'])
                else:
                    cust_po_no += ', %s'%s['client_order_ref']
        return cust_po_no

report_sxw.report_sxw(
    'report.max.maxmega.invoice2',
    'account.invoice',
    'addons/maxmega_report_addons/report/account_print_invoice.rml',
    parser=maxmega_tax_invoice, header=True)