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

class param_posted_payment_check_list(osv.osv_memory):
    _name = 'param.posted.payment.check.list'
    _description = 'Param Posted Payment Check List'
    _columns = {
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'filter_selection': fields.selection([('supp_code','Supplier Code'),('supp_code_input', 'Supplier Input Code'),('selection_code','Supplier Selection Code')],'Supp Filter Selection', required=True),
        'partner_code_from':fields.many2one('res.partner', 'Supplier Code From', domain=[('supplier','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Supplier Code To', domain=[('supplier','=',True)], required=False),
        'supplier_code_from': fields.char('Supplier Code From', size=128),
        'supplier_code_to': fields.char('Supplier Code To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_partner_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
        'journal_ids' :fields.many2many('account.journal', 'report_journal_rel', 'report_id', 'journal_id', 'Journals'),
#        'payment_from':fields.many2one('account.voucher', 'Payment From', domain=[('type','=','payment')], required=False),
#        'payment_to':fields.many2one('account.voucher', 'Payment To', domain=[('type','=','payment')], required=False),
#         'product_id': fields.many2one('product.product', 'Item Code', domain=[('sale_ok','=',True)], change_default=True),
    }

    def onchange_supp_selection(self, cr, uid, ids, supp_selection, context=None):
        if context is None:
            context = {}
        
        res = {'value': {'partner_code_from': False, 'partner_code_to':False, 'partner_ids':False}}

        if supp_selection:
            if supp_selection == 'all':
                res['domain'] = {'partner_code_from': [('supplier','=',True)],
                                 'partner_code_to': [('supplier','=',True)],
                                 'partner_ids': [('supplier','=',True)],
                                 }
            elif supp_selection == 'supplier':
                res['domain'] = {'partner_code_from': [('supplier','=',True),('sundry', '=', False)],
                                 'partner_code_to': [('supplier','=',True),('sundry', '=', False)],
                                 'partner_ids': [('supplier','=',True),('sundry', '=', False)],
                                 }
            elif supp_selection == 'sundry':
                res['domain'] = {'partner_code_from': [('sundry','=',True),('supplier', '=', True)],
                                 'partner_code_to': [('sundry','=',True),('supplier', '=', True)],
                                 'partner_ids': [('sundry','=',True),('supplier', '=', True)],
                                 }
#            pricelist_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context=None).property_product_pricelist_purchase.id
#            return {'value':{'pricelist_id': pricelist_id}}
        return res

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'supp_selection': 'all',
        'filter_selection': 'supp_code',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.posted.payment.check.list'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'posted.payment.check.list_landscape',
            'datas': datas,
            'nodestroy':True,
        }

param_posted_payment_check_list()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
