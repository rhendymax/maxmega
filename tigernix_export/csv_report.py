# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


import base64
from osv import fields,osv
from tools.translate import _
import time

class csv_report(osv.osv_memory):
    """
    Wizard to create custom report
    """
    _name = "csv.report"
    _description = "Create Report"
    _columns = {
                'data': fields.binary('File', readonly=True),
                'name': fields.char('Filename', 16, readonly=True),
                'state': fields.selection( ( ('choose','choose'),   # choose date
                     ('get','get'),         # get the file
                   ) ),
                }
    
#    def create_report(self,cr,uid,ids,context={}):
#        this = self.browse(cr, uid, ids)[0]
#        output = 'Start;Ende'
#        output += '\n' + this.start_date + ';' + this.end_date
#        print this.start_date
#        out=base64.encodestring(output)
#        return self.write(cr, uid, ids, {'state':'get',  'data':out,'name':'test.csv'}, context=context)

    def create_report(self, cr, uid, ids, context=None):
        record_id = context and context.get('active_id', False) or False

        export_obj = self.pool.get('tigernix.export')
        export     = export_obj.browse(cr, uid, record_id, context=context)

        model_obj = self.pool.get(export.model_id.model)

        # data filtering by domain
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
        
        #Change this value if u want to enlarge the filesize
        if len(model_ids) > 30000:
            raise wizard.except_wizard(_('UserError'),_('Data size too big for export, Please filter more condition!'))
        
        # Header defination
        header = ""
        lines   = export.field_ids
        for line in lines:
            header += line.field_description + ","
        header += "\n"
#            raise wizard.except_wizard(_('UserError'),_('Data size too big for export, Please filter more condition!'))
#        
        # Content
        csv_content = ''
        for model in model_obj.browse(cr,uid,model_ids):
            res = {}
            for line in lines:
                if line.ttype == 'many2one':
                    m2o_id = eval('model' + '.' + eval('line.name')).id
                    field_data = str(eval('model' + '.' + eval('line.name')).name).replace(","," ")
                else:
                    field_data = str(eval('model' + '.' + eval('line.name'))).replace(","," ")
                    
#                to prevent FALSE
                if field_data == 'False':
                    field_data = ''
                csv_content += (field_data) + ","
            csv_content += "\n"


        out=base64.encodestring(header + csv_content)
        return self.write(cr, uid, ids, {
            'state':'get',
            'data':out,
            'name':export.name + ".csv"
            }, context=context)

    _defaults = { 
                 'state': lambda *a: 'choose',
                }


csv_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

