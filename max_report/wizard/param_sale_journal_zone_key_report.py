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

class report(osv.osv_memory):
    _name = "param.sale.journal.zone.key.report"
    _description = "Param Sale Journal Zone, Customer Key Report"

    _columns = {
        'report_type': fields.char('Report Type', size=128, invisible=True,required=True),
        'cust_search_vals': fields.selection([('code','Customer Code'),('name', 'Customer Name')],'Customer Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Customer Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Customer From', domain=[('customer','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Customer To', domain=[('customer','=',True)], required=False),
        'partner_input_from': fields.char('Customer From', size=128),
        'partner_input_to': fields.char('Customer To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_sale_journal_z_customer_rel', 'report_id', 'partner_id', 'Customer', domain=[('customer','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('period_sel','Period'),('date_sel', 'Date')],'Type Selection', required=True),
        'period_filter_selection': fields.selection([('def','Default'),('input', 'Input')],'Period Filter Selection'),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'period_default_from':fields.many2one('account.period', 'Period From'),
        'period_default_to':fields.many2one('account.period', 'Period To'),
        'period_input_from': fields.char('Period From', size=128),
        'period_input_to': fields.char('Period To', size=128),
        'sale_zone_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Zone Filter Selection', required=True),
        'sale_zone_default_from':fields.many2one('res.partner.sales.zone', 'Zone From', required=False),
        'sale_zone_default_to':fields.many2one('res.partner.sales.zone', 'Zone To', required=False),
        'sale_zone_input_from': fields.char('Zone From', size=128),
        'sale_zone_input_to': fields.char('Zone To', size=128),
        'sale_zone_ids' :fields.many2many('res.partner.sales.zone', 'report_sale_journal_z_zone_rel', 'report_id', 'zone_id', 'Zone'),
    }

    _defaults = {
        'report_type' : 'receivable',
        'date_selection': 'none_sel',
        'cust_search_vals': 'code',
        'filter_selection': 'all_vall',
        'sale_zone_selection': 'all_vall'
    }
    
    def onchange_date_selection(self, cr, uid, ids, date_selection, context=None):
        if context is None:
            context = {}
        res = {}
        if date_selection:
            if date_selection == 'period_sel':
                res['value'] = {'period_filter_selection': 'def',
                                 }
            else:
                res['value'] = {'period_filter_selection': False,
                                 }
        return res

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas               = {'ids': context.get('active_ids', [])}
        datas['model']      = 'param.sale.journal.zone.key.report'
        datas['form']       = self.read(cr, uid, ids)[0]
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : 'sale.journal.zone.key_landscape',
            'datas'         : datas,
            'nodestroy'     : True,
        }

report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
