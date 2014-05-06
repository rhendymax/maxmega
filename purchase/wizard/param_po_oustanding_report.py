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

class param_po_oustanding_report(osv.osv_memory):
    _name = 'param.po.oustanding.report'
    _description = 'Param PO Oustanding Report'
    _columns = {
        'supp_selection': fields.selection([('all','Supplier & Sundry'),('supplier', 'Supplier Only'),('sundry','Sundry Only')],'Supplier Selection', required=True),
        'supplier_search_vals': fields.selection([('code','Supplier Code'),('name', 'Supplier Name')],'Supplier Search Values', required=True),
        'filter_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supp Filter Selection', required=True),
        'partner_default_from':fields.many2one('res.partner', 'Supplier From', domain=[('supplier','=',True)], required=False),
        'partner_default_to':fields.many2one('res.partner', 'Supplier To', domain=[('supplier','=',True)], required=False),
        'partner_input_from': fields.char('Supplier From', size=128),
        'partner_input_to': fields.char('Supplier To', size=128),
        'partner_ids' :fields.many2many('res.partner', 'report_oustanding_supplier_rel', 'report_id', 'partner_id', 'Supplier', domain=[('supplier','=',True)]),
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'po_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'PO Filter Selection', required=True),
        'po_default_from':fields.many2one('purchase.order', 'PO From', domain=[('state','=','approved')], required=False),
        'po_default_to':fields.many2one('purchase.order', 'PO To', domain=[('state','=','approved')], required=False),
        'po_input_from': fields.char('PO From', size=128),
        'po_input_to': fields.char('Po To', size=128),
        'po_ids' :fields.many2many('purchase.order', 'report_oustanding_po_rel', 'report_id', 'po_id', 'Purchase Order', domain=[('state','=','approved')]),
    }

    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d')
        'date_selection': 'none_sel',
        'supp_selection': 'all',
        'supplier_search_vals': 'code',
        'filter_selection': 'all_vall',
        'po_selection': 'all_vall',
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
        return res
    
    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.po.oustanding.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'po.oustanding.report_landscape',
            'datas': datas,
        }

param_po_oustanding_report()

#class purchase_order_line(osv.osv):
#    _inherit = "purchase.order.line"
#    _description = "Purchase Order Line"
#
#    def _qty_oustanding(self, cr, uid, ids, name, arg, context=None):
#        if not ids: return {}
#        res = {}
#        stock_move_obj = self.pool.get("stock.move")
#        product_uom_obj = self.pool.get("product.uom")
#        qty_oustanding = 0.00
#        for obj in self.browse(cr, uid, ids, context=context):
#            qty_delivery = 0
#            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',obj.id),('state','=','done')])
#            if move_ids:
#                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
#                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
#            res[obj.id] = obj.product_qty - qty_delivery
#        return res
#
#    _columns = {
#        'oustanding_qty': fields.function(_qty_oustanding, type='float', string='Total oustanding_qty'),
#    }
#
#purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
