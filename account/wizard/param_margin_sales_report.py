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
import time

class param_margin_sales_report(osv.osv_memory):
    _name = 'param.margin.sales.report'
    _description = 'Param Margin Sales Report'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'invoice_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Invoice Filter Selection', required=True),
        'invoice_default_from':fields.many2one('account.invoice', 'Invoice From', domain=[('type','=','out_invoice'),('state','in',('open','paid'))], required=False),
        'invoice_default_to':fields.many2one('account.invoice', 'Invoice To', domain=[('type','=','out_invoice'),('state','in',('open','paid'))], required=False),
        'invoice_input_from': fields.char('Invoice From', size=128),
        'invoice_input_to': fields.char('Invoice To', size=128),
        'invoice_ids' :fields.many2many('account.invoice', 'report_monthly_sale_invoice_rel', 'report_id', 'invoice_id', 'Invoice No', domain=[('type','=','out_invoice'),('state','in',('open','paid'))]),
    }

    _defaults = {
         'date_selection':'none_sel',
         'invoice_selection':'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.margin.sales.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'margin.sales.report_landscape',
            'datas': datas,
        }

param_margin_sales_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
