import time
from report import report_sxw
import pooler
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

class maxmega_invoice(report_rml):
    def create(self, cr, uid, ids, datas, context):
        pool           = pooler.get_pool(cr.dbname)
        inv_obj        = pool.get('account.invoice')
        comp_obj       = pool.get('res.company')
        inv_ids        = ids
        rml_res        = ''
        
        
        def _number_format(amount):
            res = {'amount': amount}
            return locale.format("%(amount).2f", res,1)
        
        def header(o):
            
            header= """
    <para style="terp_default_8"><seqReset/></para>    
        <blockTable colWidths="250.0,30.0,240.0" style="Table_Partner_Address">
            <tr>
                <td>
                    <blockTable colWidths="250.0" style="Table8">
                    <tr>
                            <td>
                                    <para style="terp_default_9">
                                    <font color="white"> </font>
                                    </para>
                                    <para style="terp_default_Bold_9">BILL TO :</para>
                                    <para style="terp_default_9">""" + str(o.partner_id and o.partner_id.title and o.partner_id.title.name or '') + """ """ + str(o.partner_id and o.partner_id.name or '') + """</para>
                                    <para style="terp_default_9">Tel """ + str(o.partner_id.phone ) + """</para>
                            </td>
                    </tr>
                                    <para style="terp_default_9">
                                    <font color="white"> </font>
                                    </para>
                    <tr>
                            <td>
                                    <para style="terp_default_Bold_9">SHIP TO :</para>
                                    <para style="terp_default_9">""" + str(o.partner_id and o.partner_id.title and o.partner_id.title.name or '') + """ """ + str(o.partner_id and o.partner_id.name or '') + """</para>
                                    <para style="terp_default_9">Tel """ + str(o.partner_id.phone ) + """</para>
                            </td>
                    </tr>
                    </blockTable>
             </td>
             <td>
                    <para style="terp_default_9">
                    <font color="white"> </font>
                    </para>
            </td>
            <td>
                <blockTable colWidths="110.0,130.0" style="Table8">
                    <tr>
                        <td>
                            <para style="terp_default_10_Italic_Bold">TAX INVOICE</para>
                        </td>
                        <td>
                            <para style="terp_default_9">
                            <font color="white"> </font>
                            </para>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <para style="terp_default_Bold_8">GST REG.NO</para>
                            <para style="terp_default_Bold_8">NO</para>
                            <para style="terp_default_Bold_8">DATE</para>
                            <para style="terp_default_Bold_8">D/O NO</para>
                            <para style="terp_default_Bold_8">REFERENCE NO</para>
                            <para style="terp_default_Bold_8">CUSTOMER CODE</para>
                            <para style="terp_default_Bold_8">SHIPMENT METHOD</para>
                            <para style="terp_default_Bold_8">SHIPMENT TERM</para>
                            <para style="terp_default_Bold_8">PAYMENT TERM</para>
                            <para style="terp_default_Bold_8">SALES PERSON</para>
                        </td>
                        <td>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:""" + str(o.date_invoice[0:10]) + """</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:</para>
                            <para style="terp_default_8_Left">:""" + str(o.sale_term_id or '') + """</para>
                            <para style="terp_default_8_Left">:</para>
                        </td>
                    </tr>
                    </blockTable>
                </td>
            </tr>
</blockTable>
"""
            return header
        def middle(o):
                middle ="""
                <blockTable colWidths="20.0,155.0,100.0,80.0,65.0,100.0" style="Table7">
                  <tr>
                     <td>
                      <para style="terp_tblheader_General_Centre">No</para>
                    </td>
                    
                    <td>
                      <para style="terp_tblheader_General_Centre">ITEM DESCRIPTION</para>
                    </td>
                    <td>
                      <para style="terp_tblheader_General_Centre">CUSTOMER P/O NO</para>
                    </td>
                    <td>
                      <para style="terp_tblheader_General_Centre">QTY</para>
                    </td>
                    <td>
                      <para style="terp_tblheader_General_Centre">UNIT PRICE """+ str(o.currency_id.name or '') + """</para>
                    </td>
                    <td>
                      <para style="terp_tblheader_General_Centre">TOTAL AMOUNT """+ str(o.currency_id.name or '') + """</para>
                    </td>
                  </tr>
                </blockTable>
             """
                return middle
        
        def footer(o):
                amount_untaxed = _number_format(o.amount_untaxed)
                amount_tax = _number_format(o.amount_tax)
                residual_amount = _number_format(o.residual)
                footer= """ 
                
                <blockTable colWidths="110.0,20.0,120.0,20.0,110.0,20.0,120.0" style="Table_Account_Detail">
        <tr>
            <td>
                <para style="terp_default_Bold_8">SGD EXCHANGE RATE</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">@</para>
            </td>
            <td>
                <para style="terp_default_8">""" + str (o.rate or '') + """</para>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_8"> </para>
            </td>
        </tr>
        <tr>
            <td>
                <para style="terp_default_Bold_8">TOTAL IN SGD</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_8">""" + str (amount_untaxed) + """</para>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_Bold_8">TOTAL IN """ + str (o.currency_id.name) + """</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_8">""" + str (amount_untaxed) + """</para>
            </td>
        </tr>
        <tr>
            <td>
                <para style="terp_default_Bold_8">TAX</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_8">""" + str (amount_tax) + """</para>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_Bold_8">TAX</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_8">""" + str (amount_tax) + """</para>
            </td>
        </tr>
        <tr>
            <td>
                <para style="terp_default_Bold_8">TOTAL AMOUNT SGD</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_Bold_Right_9">""" + str (residual_amount) + """</para>
                <illustration width="150" height="8">
                <lineMode width ="1.0"/>
                <lines>-6 5 115 5</lines>
                <lineMode width ="1.0"/>
                <lines>-6 3.2 115 3.2</lines>
                </illustration>
            </td>
            <td>
                <para style="terp_default_Bold_8"> </para>
            </td>
            <td>
                <para style="terp_default_Bold_8">TOTAL AMOUNT """ + str (o.currency_id.name) + """</para>
            </td>
            <td>
                <para style="terp_default_Bold_8">:</para>
            </td>
            <td>
                <para style="terp_default_Bold_Right_9">""" + str (residual_amount) + """</para>
                <illustration width="150" height="8">
                <lineMode width ="1.0"/>
                <lines>-6 5 115 5</lines>
                <lineMode width ="1.0"/>
                <lines>-6 3.2 115 3.2</lines>
                </illustration>
            </td>
        </tr>
        </blockTable>
            <blockTable colWidths="250.0,270.0" style="Table_Signature_Line">
                <tr>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                </tr>
                <tr>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                </tr>
                <tr>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                </tr>
                <tr>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                </tr>
                <tr>
                    <td>
                        <para style="terp_default_9">MAXMEGA ELECTRONICS PTE LTD</para>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                    </td>
                    <td>
                        <para style="terp_default_9">
                            <font color="white"> </font>
                        </para>
                    </td>
                </tr>
            </blockTable>
                
                """
                return footer
            
        
            
            
            
            
        obj_count = 0
        for o in inv_obj.browse(cr, uid, inv_ids):
            max_line = 16
            number_line = 8
            number_format = 1
            Total_page = 1
            number_page = 1
            obj_count += 1
#            if obj_count > 1:
#                rml_res += """<pageBreak/>"""
            
            
            for l in o.invoice_line:
                if number_line == 0:
                        Total_page += 1
                number_line = number_line-1
#            if obj_count > 1:
#                rml_res += """<pageBreak/>"""
            rml_res += header(o)
            rml_res += """
                        <blockTable colWidths="520.0" style="Table_Page_Number">
                          <tr>
                              <td>
                                  <para style="terp_default_Right_9">Page """ +str(number_page)+""" of """+str(Total_page)+"""</para>
                              </td>
                          </tr>
                        </blockTable>
                        """
            rml_res += middle(o)
            number_line = 8
            for l in o.invoice_line :
                unit_price = _number_format(l.price_unit)
                subtotal_price = _number_format(l.price_subtotal)
                if number_line == 0:
                   ml_res += """<pageBreak/>"""
                   number_page = number_page+1
                   rml_res += header(o)
                   
                   rml_res += """
                        <blockTable colWidths="520.0" style="Table_Page_Number">
                          <tr>
                              <td>
                                  <para style="terp_default_Right_9">Page """ +str(number_page)+""" of """+str(Total_page)+"""</para>
                              </td>
                          </tr>
                        </blockTable>
                        """
                   rml_res += middle(o)
                   number_line += 1
                rml_res += """
                          <blockTable colWidths="20.0,155.0,100.0,80.0,65.0,100.0" style="Table8">
                            <tr>
                               <td>
                                <para style="terp_default_9">"""+ str (number_format)+ """</para>
                              </td>
                              
                              <td>
                                <para style="terp_default_9">""" + str (l.name ) + """</para>
                              </td>
                              <td>
                                <para style="terp_default_Centre_9">"""+ str (Total_page)+ """</para>
                              </td>
                              <td>
                                <para style="terp_default_Right_9">""" + str (l.quantity) + """ """ + str ((l.uos_id and l.uos_id.name) or '') + """</para>
                              </td>
                              <td>
                                <para style="terp_default_Right_9">"""+ str (unit_price) + """""" + str (o.currency_id.symbol) + """</para>
                              </td>
                              <td>
                                <para style="terp_default_Right_9">"""+ str (subtotal_price) + """""" + str (o.currency_id.symbol) + """</para>
                              </td>
                            </tr>
                          </blockTable>
                      """
                number_format += 1
                number_line = number_line-1
               
                
            sisa = max_line-number_format
            count = 0
            while (count < sisa):
                count = count + 1
                rml_res += """
                        <blockTable colWidths="520.0" style="Table9">
                            <tr>
                                <td>
                                    <para style="terp_default_9">
                                        <font color="white">""" + str (count) + """</font>
                                    </para>
                                </td>
                            </tr>
                          </blockTable>"""
            rml_res += footer(o)


        rml="""
<document filename="Invoice.pdf">
    <template pageSize="(21.59cm, 27.94cm)" title="Purchase Order" author="Yanto Chen" allowSplitting="20">
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

            <lines>1.2cm 2.15cm 19.9cm 2.15cm</lines>
            """
            
        if (o.company_id and o.company_id.rml_footer1):
            rml += """
                    <drawCentredString x="10.5cm" y="1.6cm">""" + str(o.company_id.rml_footer1) + """</drawCentredString>"""
        if (o.company_id and o.company_id.rml_footer2):
            rml += """
                    <drawCentredString x="10.5cm" y="1.15cm">""" + str(o.company_id.rml_footer2) + """</drawCentredString>"""
        
        rml += """
            <drawCentredString x="10.5cm" y="0.7cm">Contact :  - Page: <pageNumber/> </drawCentredString>
                """
        
        rml += """
            </pageGraphics>
        </pageTemplate>
  </template>
  <stylesheet>
        <blockTableStyle id="Table_Partner_Address">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Table7">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="4,-1" stop="4,-1"/>
            <lineStyle kind="LINEBELOW" colorName="#000000" start="5,-1" stop="5,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,-1" stop="0,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,-1" stop="1,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,-1" stop="2,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,-1" stop="3,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="4,-1" stop="4,-1"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,-1" stop="5,-1"/>
        </blockTableStyle>
        <blockTableStyle id="Table8">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Table9">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
        <blockTableStyle id="Table_Account_Detail">
            <blockAlignment value="LEFT"/>
            <blockValign value="TOP"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="3,0" stop="3,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="4,0" stop="4,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="5,0" stop="5,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="6,0" stop="6,0"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="2,3" stop="2,3"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="6,3" stop="6,3"/>
        </blockTableStyle>
        <blockTableStyle id="Table_Signature_Line">
            <blockAlignment value="RIGHT"/>
            <blockValign value="TOP"/>
            <lineStyle kind="LINEABOVE" colorName="#000000" start="0,4" stop="0,4"/>
        </blockTableStyle>
        <blockTableStyle id="Table_Page_Number">
            <blockAlignment value="RIGHT"/>
            <blockValign value="TOP"/>
        </blockTableStyle>
    <initialize>
    <paraStyle name="all" alignment="justify"/>
    </initialize>
    <paraStyle name="Standard" fontName="Helvetica"/>
    <paraStyle name="Text body" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="List" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Table Contents" fontName="Helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Table Heading" fontName="Helvetica" alignment="CENTER" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Caption" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="Index" fontName="Helvetica"/>
    <paraStyle name="Heading" fontName="Helvetica" fontSize="15.0" leading="19" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_header" fontName="Helvetica-Bold" fontSize="12.0" leading="15" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="Footer" fontName="Helvetica"/>
    <paraStyle name="Horizontal Line" fontName="Helvetica" fontSize="6.0" leading="8" spaceBefore="0.0" spaceAfter="14.0"/>
    <paraStyle name="Heading 9" fontName="Helvetica-Bold" fontSize="75%" leading="NaN" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_General" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_Details" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_Bold_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_tblheader_General_Centre" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_General_Right" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_Details_Centre" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_Details_Right" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_Right_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Centre_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_header_Right" fontName="Helvetica-Bold" fontSize="15.0" leading="19" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_header_Centre" fontName="Helvetica-Bold" fontSize="12.0" leading="15" alignment="CENTER" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_address" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="10.0" leading="13" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Bold_9" rightIndent="0.0" leftIndent="-3.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Centre_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Right_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Bold_Right_9" rightIndent="0.0" leftIndent="-3.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_White_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0" textColor="#ffffff"/>
    <paraStyle name="terp_default_Note" rightIndent="0.0" leftIndent="9.0" fontName="Helvetica-Oblique" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="Table" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="User Index 10" rightIndent="0.0" leftIndent="127.0" fontName="Helvetica"/>
    <paraStyle name="Preformatted Text" fontName="Helvetica" fontSize="10.0" leading="13" spaceBefore="0.0" spaceAfter="0.0"/>
     <paraStyle name="terp_default_10_Italic_Bold" fontName="Helvetica-BoldOblique" fontSize="10.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_8_Italic" fontName="Helvetica-Oblique" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_8" fontName="Helvetica" fontSize="8.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_8_Left" fontName="Helvetica" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    
    <images/>
  </stylesheet>
    <images/>
  <story>"""
        rml += rml_res + """
  </story>
</document>"""
        report_type = datas.get('report_type', 'pdf')
        create_doc = self.generators[report_type]
        pdf = create_doc(rml, title=self.title)
        return (pdf, report_type)
maxmega_invoice('report.maxmega.invoice', 'account.invoice','','')
