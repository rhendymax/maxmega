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
import pooler
from mx import DateTime as dt
from report.interface import report_rml
from tools import to_xml
import calendar
import math
from datetime import datetime
import locale
#locale.setlocale(locale.LC_ALL, '')
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import cgi
import re
from tools.translate import _

#class order2(report_sxw.rml_parse):
#    def __init__(self, cr, uid, name, context):
#        super(order2, self).__init__(cr, uid, name, context=context)
#        self.localcontext.update({
#                                  'time': time,
#                                  'locale': locale,
#                                  })
#        #raise osv.except_osv(_('Debug !'), _('----' + '' + '----' + ''))

#locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
#
#report_sxw.report_sxw('report.max.purchase.order','purchase.order','addons/max_report_addons/report/order.rml',parser=order2)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
class pdf_report(report_rml):
    def create(self, cr, uid, ids, datas, context):
        pool           = pooler.get_pool(cr.dbname)
        export_obj     = pool.get('tigernix.export')
        export_id      = ids
        rml_res        = ''

    
        def print_header(o):
            header="""
            <para style="Heading"> """ + o.name + """</para>
            <para style="Heading"></para>"""
            
            field_lines = o.field_ids
            width       = str(756 / len(field_lines)) + ","
            width       = width * len(field_lines)
            
            header += """<blockTable style="table_header" colWidths="30, """ + width[:-1] + """ ">
                <tr>
                <td><para style="terp_default_Bold_9">No</para></td>
            """
            
            for field_line in field_lines:
                header += """ <td><para style="terp_default_Bold_9"> """ + field_line.field_description + """ \
                </para></td>"""
            
            header += """ </tr></blockTable> """
            
            return header

        def _replace_symbol(string):
            if type(string) == unicode:
                if string and '&' in string:
                    string = string.replace('&','&amp;')
            return string
                
        def _explode_name(chaine,length):
            # We will test if the size is less then account
            full_string = ''
            if (len(chaine) <= length):
                return chaine
            #
            else:
                #chaine = unicode(chaine,'utf8').encode('iso-8859-1')
                rup = 0
                for carac in chaine:
                    rup = rup + 1
                    if rup == length:
                        full_string = full_string + '\n'
                        full_string = full_string + carac
                        rup = 0
                    else:
                        full_string = full_string + carac

            return full_string
        
        def comma_me(amount):
            #print "#" + str(amount) + "#"
            if not amount:
                amount = 0.0
            if  type(amount) is float :
                amount = str('%.2f'%amount)
            else :
                amount = str(amount)
            if (amount == '0'):
                 return ' '
            orig = amount
            new = re.sub("^(-?\d+)(\d{3})", "\g<1>,\g<2>", amount)
            if orig == new:
                return new
            else:
                return comma_me(new)
        
        def print_content(o):
            export = export_obj.browse(cr,uid,o.id)
            model_obj = pool.get(export.model_id.model)
            
            # Define date
            lang = pool.get('res.users').browse(cr,uid,uid).context_lang
            date_search = pool.get('res.lang').search(cr, uid,[('code','=',lang)])
            date_find = pool.get('res.lang').browse(cr, uid,date_search[0])
            date_find_format        = date_find.date_format
            datetime_find_format    = date_find_format + " " + date_find.time_format
            
            # Getting Data
            list = []
            for filter in export.filter_line:
                operand = filter.operand and str(filter.operand) or ''
                # Filter the type of field
                if filter.field_id.ttype in ('float','integer'):
                    domain = eval("('%s', '%s', %s)" % (filter.field_id.name, filter.operator,
                                filter.operand))
                elif filter.field_id.ttype in ('many2one'):
                    domain = eval("('%s.name', '%s', '%s')" % (filter.field_id.name, filter.operator,
                                filter.operand))
                elif filter.field_id.ttype in ('boolean'):
                    domain = eval("('%s', '%s', %s)" % (filter.field_id.name, filter.operator,
                                filter.operand_bool))
                else:
                    domain = eval("('%s', '%s', '%s')" % (filter.field_id.name, filter.operator,
                                filter.overall_operand))
                list.append(domain)

            model_ids = model_obj.search(cr,uid,eval('list'))
            
            lines   = export.field_ids
            
            field_lines = export.field_ids
            width       = str(756 / len(field_lines)) + ","
            width       = width * len(field_lines)
            
            string_len  = math.ceil((756 / len(field_lines)) / 6.25)
            
            if not model_ids:
                return ''
        
            content = """<blockTable style="table_content" colWidths="30, """ + width[:-1] + """ "> """
            no = 1
            for model in model_obj.browse(cr,uid,model_ids):
                content += """ 
                    <tr><td>""" + str(no)  + """</td> 
                """
                no += 1
                res = {}
                for line in lines:
                    val = eval('model' + '.' + eval('line.name'))
                    if line.ttype == 'many2one':
                        m2o_id = eval('model' + '.' + eval('line.name')).id
                        field_data = str(val.name).replace(","," ")
                    elif line.ttype in ('float','integer'):
                        field_data = comma_me(val)
                    elif line.ttype == 'date' and val:
                        field_data = time.strftime(date_find_format,time.strptime(val,'%Y-%m-%d')) or '-'
                    elif line.ttype == 'datetime' and val:
                        field_data = time.strftime(datetime_find_format,time.strptime(val,'%Y-%m-%d %H:%M:%S')) or '-'
                    else:
                        field_data = val

    #                to prevent FALSE
                    if field_data == 'False' or not field_data:
                        field_data = '-'

                    content += "<td><para style='terp_default_9'>" + to_xml(_explode_name(str(field_data), string_len)) + "</para></td>"
                content += "</tr>"
            content += "</blockTable>"
            
            return content




        def header(o):
            partner_title = ''
            partner_name = ''
            if o.partner_id:
                partner_title = o.partner_id.title and str(o.partner_id.title.name)
                partner_name = str(o.partner_id.name)
            if partner_title: partner_title = partner_title.replace('&','&amp;')
            if partner_name: partner_name = partner_name.replace('&','&amp;')
            
            partner_shipping_name = ''
            partner_shipping_id_name = ''
            partner_shipping_name = o.partner_shipping_id.name
            if o.partner_shipping_id:
                partner_shipping_id_name = str(o.partner_shipping_id.partner_id.name)
            if partner_shipping_name : partner_shipping_name = partner_shipping_name.replace('&','&amp;')
            if partner_shipping_id_name: partner_shipping_id_name = partner_shipping_id_name.replace('&','&amp;')
            partner_order_name = ''
            if o.partner_order_id:
                partner_order_name = str(o.partner_order_id.name)
            if partner_order_name: partner_order_name = partner_order_name.replace('&','&amp;')
            
            header = """
            <blockTable colWidths="257.0,38.00,260.0" style="Tableau1">
                <tr>
                    <td>
                        <blockTable colWidths="257.0" rowHeights="100.0,100.0" style="Tableau2">
                            <tr>
                                <td>
                                    <para style="terp_default_Bold_8">TO :</para>
                                    <para style="terp_default_8">""" + str((o.partner_id and partner_title) or '') + """ """ + str((o.partner_id and partner_name) or '') +  """</para>"""
            disaddress = False
            if o.partner_order_id:
                address = o.partner_order_id
                address_format = address.country_id and address.country_id.address_format or \
                     '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
                args = {
                    'state_code': str(address.state_id and address.state_id.code) or '',
                    'state_name': str(address.state_id and address.state_id.name) or '',
                    'country_code': str(address.country_id and address.country_id.code) or '',
                    'country_name': str(address.country_id and address.country_id.name) or '',
                }
                address_field = ['title', 'street', 'street2', 'zip', 'city']
                for field in address_field :
                    args[field] = getattr(address, field) or ''
                disaddress = address_format % args
                disaddress_1 = ''
                disaddress_1 = disaddress
                if disaddress_1: disaddress_1 = disaddress_1.replace('&','&amp;')
            
            if disaddress:
                header += """            <para style="terp_default_8">""" + str(disaddress_1) + """</para>
                                        """
            if (o.partner_order_id and o.partner_order_id.phone):
                header += """
                    <para style="terp_default_8">Tél. : """ + str (o.partner_order_id.phone) + """</para> """
            if (o.partner_order_id and o.partner_order_id.fax):
                header += """
                    <para style="terp_default_8">Fax : """ + str (o.partner_order_id.fax) + """</para> """
            attention = False
            if (o.partner_order_id and partner_order_name):
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
            if (partner_shipping_name):
                header += """
                    <para style="terp_default_8">""" + str (partner_shipping_name) + """</para> """
            if ((o.partner_shipping_id and partner_shipping_id_name) or (o.shop_id and o.shop_id.warehouse_id and o.shop_id.warehouse_id.name)):
                header += """
                    <para style="terp_default_8">""" + str ((o.partner_shipping_id and partner_shipping_id_name) or (o.shop_id and o.shop_id.warehouse_id and o.shop_id.warehouse_id.name))+"""</para> """
            
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
                disaddress_2 = ''
                disaddress_2 = disaddress2
                if disaddress_2: disaddress_2 = disaddress_2.replace('&','&amp;')
            disaddress3 = False
            if o.warehouse_id:
                address3 = o.warehouse_id.partner_address_id
                address_format3 = address3.country_id and address3.country_id.address_format or \
                     '%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s'
                args3 = {
                    'state_code': address3.state_id and address3.state_id.code or '',
                    'state_name': address3.state_id and address3.state_id.name or '',
                    'country_code': address3.country_id and address3.country_id.code or '',
                    'country_name': address3.country_id and address3.country_id.name or '',
                }
                address_field3 = ['title', 'street', 'street2', 'zip', 'city']
                for field3 in address_field3:
                    args3[field3] = getattr(address3, field3) or ''
                disaddress3 = address_format3 % args3
                disaddress_3 = ''
                disaddress_3 = disaddress3
                if disaddress_3: disaddress_3 = disaddress_3.replace('&','&amp;')
            if (disaddress2 or disaddress3):
                header += """            <para style="terp_default_8">""" + str(disaddress_2 or disaddress_3) + """</para>
                                        """
            if (o.partner_order_id and o.partner_order_id.phone):
                header += """            <para style="terp_default_8">Tél  :""" + str(o.partner_order_id.phone) + """</para>
                                        """
            if (o.partner_order_id and o.partner_order_id.fax):
                header += """            <para style="terp_default_8">Fax  :""" + str(o.partner_order_id.fax) + """</para>
                                        """
            attention2 = False
            if ((o.partner_order_id and o.partner_order_id.name) or (o.warehouse_id and o.warehouse_id.partner_address_id and o.warehouse_id.partner_address_id.name)):
                attention2 = str((o.partner_order_id and o.partner_order_id.name) or (o.warehouse_id and o.warehouse_id.partner_address_id and o.warehouse_id.partner_address_id.name))
            if ((o.partner_order_id and o.partner_order_id.email) or (o.warehouse_id and o.warehouse_id.partner_address_id and o.warehouse_id.partner_address_id.email)):
                if attention2:
                    attention2 += ' ' + str((o.partner_order_id and o.partner_order_id.email) or (o.warehouse_id and o.warehouse_id.partner_address_id and o.warehouse_id.partner_address_id.email))
                else:
                    attention2 = str((o.partner_order_id and o.partner_order_id.email) or (o.warehouse_id and o.warehouse_id.partner_address_id and o.warehouse_id.partner_address_id.email))
            if attention2:
                header += """
                    <para style="terp_default_8">Attn : """ + attention2 + """</para> """

            header += """
                                </td>
                            </tr>
                        </blockTable>
                    </td>
                    <td>
                    </td>
                    <td>
                        <blockTable colWidths="120.0,140.0" rowHeights="12.00,145" style="Tableau2">
                            <tr>
                                <td>
                                    <para style="terp_default_9_Italic_Bold">PURCHASE ORDER</para>
                                </td>
                                <td>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <para style="terp_default_Bold_8">PO NO</para>
                                    <para style="terp_default_Bold_8">PO DATE</para>
                                    <para style="terp_default_Bold_8">GST REG NO</para>
                                    <para style="terp_default_Bold_8">SHIPMENT METHOD</para>
                                    <para style="terp_default_Bold_8">SHIPMENT TERM</para>
                                    <para style="terp_default_Bold_8">REFERENCE NO</para>
                                    <para style="terp_default_Bold_8">REQUISITOR</para>
                                    <para style="terp_default_Bold_8">BUYER</para>
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
                                    <para style="terp_default_8">:""" + str(o.partner_ref or '' ) + """</para>
                                    <para style="terp_default_8">:""" + str(o.requisitor_id and o.requisitor_id.name or '' ) + """</para>
                                    <para style="terp_default_8">:""" + str(o.buyer_id and o.buyer_id.name or '') + """</para>
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
                            <para style="terp_tblheader_General_Centre">REQUIRED DATE</para>
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
#        
        def footer(o):
            amount_untaxed = _number_format(o.amount_untaxed)
            amount_tax = _number_format(o.amount_tax)
            amount_total = _number_format(o.amount_total)
            amt_en = amount_to_text_en.amount_to_text(o.amount_total,'en',o.pricelist_id.currency_id.name)
            footer = """
                    """
            footer+= """ 
                    
                    <blockTable colWidths="290.0,145.0,20.0,100.0" rowHeights="60.00" style="Table_All_Total_Detail">
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
                            <illustration width="150" height="8">
                            <lineMode width ="1.0"/>
                            <lines>-6 5 95 5</lines>
                            </illustration>
                            <para style="terp_tblheader_General_Right">"""+str (amount_total)+""" """+str (o.pricelist_id.currency_id.symbol or '' )+"""</para>
                            <illustration width="150" height="8">
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
                        <para style="terp_default_Bold_8">This is a computer generated Purchase Order</para>
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
            # font-size 9px 1cm = 5 letters upper case
            # font-size 9px 1cm = 6 letters lower case
            line = len(string) / (width * 6)
            return math.ceil(line)

        obj_count = 0
        for o in export_obj.browse(cr, uid, export_id):
            model_obj      = pool.get(o.model_id.model)
            list = []
            for filter in o.filter_line:
                operand = filter.operand and str(filter.operand) or ''
                # Filter the type of field
                if filter.field_id.ttype in ('float','integer'):
                    domain = eval("('%s', '%s', %s)" % (filter.field_id.name, filter.operator,
                                filter.operand))
                elif filter.field_id.ttype in ('many2one'):
                    domain = eval("('%s.name', '%s', '%s')" % (filter.field_id.name, filter.operator,
                                filter.operand))
                elif filter.field_id.ttype in ('boolean'):
                    domain = eval("('%s', '%s', %s)" % (filter.field_id.name, filter.operator,
                                filter.operand_bool))
                else:
                    domain = eval("('%s', '%s', '%s')" % (filter.field_id.name, filter.operator,
                                filter.overall_operand))
                list.append(domain)
        
            model_ids = model_obj.search(cr,uid,eval('list'))
        
            #Change this value if u want to enlarge the filesize
            if len(model_ids) > 30000:
                raise wizard.except_wizard(_('UserError'),_('Data size too big for export, Please filter more condition!'))
        
            field_lines = o.field_ids
        
            if len(field_lines) > 9:
                raise wizard.except_wizard(_('UserError'),_('Too many fields for A4 paper, please select not more than 9 fields!'))


            obj_count += 1
            if obj_count > 1:
                rml_res += """<pageBreak/>"""
            rml_res += print_header(o)
            rml_res += print_content(o)

        rml="""
<document filename="Invoice.pdf">
    <template pageSize="(842.0,595.0)" title="Test" author="Martin Simon" allowSplitting="20">
        <pageTemplate id="first">
          <frame id="first" x1="34.0" y1="28.0" width="786" height="530"/>
        </pageTemplate>
  </template>
  <stylesheet>
    <blockTableStyle id="Standard_Outline">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Partner_Address">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Invoice_General_Header">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBEFORE" colorName="#e6e6e6" start="0,0" stop="0,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#e6e6e6" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="#e6e6e6" start="1,0" stop="1,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#e6e6e6" start="1,0" stop="1,0"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="#e6e6e6" start="2,0" stop="2,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#e6e6e6" start="2,0" stop="2,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#e6e6e6" start="2,0" stop="2,0"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="2,-1" stop="2,-1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_General_Detail_Content">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Header_Invoice_Line">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="4,-1" stop="4,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="5,-1" stop="5,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="6,-1" stop="6,-1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Invoice_Line_Content">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Format_2">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="0,0" stop="0,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="1,0" stop="1,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="1,0" stop="1,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="2,0" stop="2,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="2,0" stop="2,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="3,0" stop="3,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="3,0" stop="3,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="3,0" stop="3,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="3,-1" stop="3,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="4,0" stop="4,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="5,0" stop="5,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="6,0" stop="6,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="10,0" stop="10,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="11,0" stop="11,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="12,0" stop="12,0"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="0,1" stop="0,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="0,1" stop="0,1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="1,1" stop="1,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="1,1" stop="1,1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="0,2" stop="0,2"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="1,2" stop="1,2"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="2,2" stop="2,2"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="0,4" stop="0,4"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="1,4" stop="1,4"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="2,4" stop="2,4"/>
    </blockTableStyle>
    <blockTableStyle id="Table_format_Table_Line_total">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="0,0" stop="0,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="1,0" stop="1,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="1,0" stop="1,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_eclu_Taxes_Total">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Taxes_Total">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Total_Include_Taxes">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="1,0" stop="1,0"/>
      <lineStyle kind="LINEABOVE" colorName="#000000" start="2,0" stop="2,0"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Main_Table">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="0,0" stop="0,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="0,0" stop="0,-1"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="3,-1" stop="3,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="#ffffff" start="0,2" stop="0,-1"/>
      <lineStyle kind="LINEAFTER" colorName="#ffffff" start="0,2" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="3,-1" stop="3,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="2,-1" stop="2,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="3,-1" stop="3,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="2,-1" stop="2,-1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Tax_Header">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#000000" start="2,-1" stop="2,-1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Content">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <!--lineStyle kind="LINEBELOW" colorName="#e6e6e6"/-->
    </blockTableStyle>
    <blockTableStyle id="Table_Table_Border_White">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="0,-1" stop="0,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="1,-1" stop="1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="#ffffff" start="2,-1" stop="2,-1"/>
    </blockTableStyle>
    <blockTableStyle id="table_header">
      <blockAlignment value="LEFT"/>
      <blockValign value="MIDDLE"/>
      <lineStyle kind="LINEABOVE" colorName="black" thickness="0" start="0,1" stop="-1,1" />
    </blockTableStyle>
    <blockTableStyle id="table_content">
      <blockAlignment value="LEFT"/>
      <blockValign value="MIDDLE"/>
      <lineStyle kind="LINEABOVE" colorName="#dddddd" thickness="0" start="0,1"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Final_Border">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="0,0" stop="0,0"/>
      <lineStyle kind="LINEABOVE" colorName="#ffffff" start="1,0" stop="1,0"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Coment_Payment_Term">casa_invoice
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <blockTableStyle id="Table_Payment_Terms">
      <blockAlignment value="LEFT"/>
      <blockValign value="TOP"/>
    </blockTableStyle>
    <initialize>
      <paraStyle name="all" alignment="justify"/>
    </initialize>
    <paraStyle name="Standard" fontName="Times-Roman"/>
    <paraStyle name="Text body" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="List" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Table Contents" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Table Heading" fontName="Times-Roman" alignment="CENTER" spaceBefore="0.0" spaceAfter="6.0"/>
    <paraStyle name="Caption" fontName="Times-Roman" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="Index" fontName="Times-Roman"/>
    <paraStyle name="Heading" fontName="Helvetica" fontSize="15.0" leading="19" spaceBefore="12.0" alignment="CENTER" spaceAfter="6.0"/>
    <paraStyle name="terp_header" fontName="Helvetica-Bold" fontSize="12.0" leading="15" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="Footer" fontName="Times-Roman"/>
    <paraStyle name="PDynamic" fontName="Helvetica" fontSize="8.0" leading="12" alignment="LEFT" spaceBefore="6.0" spaceAfter="0.0"/>
    <paraStyle name="P8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="0.0"/>
    <paraStyle name="P12" fontName="Helvetica" fontSize="12.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="0.0"/>
    <paraStyle name="Horizontal Line" fontName="Times-Roman" fontSize="6.0" leading="8" spaceBefore="0.0" spaceAfter="14.0"/>
    <paraStyle name="Heading 9" fontName="Helvetica-Bold" fontSize="75%" leading="NaN" spaceBefore="12.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_General" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_tblheader_Details" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
    <paraStyle name="terp_default_Bold_8" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
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
    <paraStyle name="terp_default_Bold_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Centre_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Right_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Bold_Right_9" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_10" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="10.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Bold_10" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="10.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Centre_10" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="10.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Right_10" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="10.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Bold_Right_10" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica-Bold" fontSize="10.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_White_2" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="2.0" leading="3" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
    <paraStyle name="terp_default_Note" rightIndent="0.0" leftIndent="9.0" fontName="Helvetica-Oblique" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
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
pdf_report('report.max.export.report', 'tigernix.export','','')

