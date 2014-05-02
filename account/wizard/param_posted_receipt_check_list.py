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

class param_posted_receipt_check_list(osv.osv_memory):
    _name = 'param.posted.receipt.check.list'
    _description = 'Param Posted Receipt Check List'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'partner_code_from':fields.many2one('res.partner', 'Customer Code From', domain=[('customer','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Customer Code To', domain=[('customer','=',True)], required=False),
        'filter_selection': fields.selection([('cust_code','Customer Code'),('cust_code_input', 'Customer Input Code'),('selection_code','Customer Selection Code')],'Cust Filter Selection', required=True),
        'customer_code_from': fields.char('Customer Code From', size=128),
        'customer_code_to': fields.char('Customer Code To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_receipt_partner_rel', 'report_id', 'partner_id', 'Customer', domain=[('customer','=',True)]),
        'journal_ids' :fields.many2many('account.journal', 'report_receipt_journal_rel', 'report_id', 'journal_id', 'Journals'),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'filter_selection': 'cust_code',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.posted.receipt.check.list'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'posted.receipt.check.list_landscape',
            'datas': datas,
            'nodestroy':True,
        }

param_posted_receipt_check_list()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
