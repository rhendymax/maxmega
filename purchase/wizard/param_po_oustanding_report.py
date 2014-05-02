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
        'date_from': fields.date("From Date", required=True),
        'date_to': fields.date("To Date", required=True),
        'partner_code_from':fields.many2one('res.partner', 'Supplier Code From', domain=[('supplier','=',True)], required=False),
        'partner_code_to':fields.many2one('res.partner', 'Supplier Code To', domain=[('supplier','=',True)], required=False),
        'po_from':fields.many2one('purchase.order', 'PO From', required=False),
        'po_to':fields.many2one('purchase.order', 'PO To', required=False),
        # 'product_id': fields.many2one('product.product', 'Item Code', domain=[('sale_ok','=',True)], change_default=True),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d')
    }

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

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    def _qty_oustanding(self, cr, uid, ids, name, arg, context=None):
        if not ids: return {}
        res = {}
        stock_move_obj = self.pool.get("stock.move")
        product_uom_obj = self.pool.get("product.uom")
        qty_oustanding = 0.00
        for obj in self.browse(cr, uid, ids, context=context):
            qty_delivery = 0
            move_ids = stock_move_obj.search(cr, uid, [('purchase_line_id','=',obj.id),('state','=','done')])
            if move_ids:
                for mv in stock_move_obj.browse(cr, uid, move_ids, context=context):
                    qty_delivery = qty_delivery + product_uom_obj._compute_qty(cr, uid, mv.product_uom.id, mv.product_qty, mv.product_id.uom_id.id)
            res[obj.id] = obj.product_qty - qty_delivery
        return res

    _columns = {
        'oustanding_qty': fields.function(_qty_oustanding, type='float', string='Total oustanding_qty'),
    }

purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
