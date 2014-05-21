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
import pooler
import base64
from tools.translate import _

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
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
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

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        res = {}
        res_partner_obj = self.pool.get('res.partner')
        purchase_order_obj = self.pool.get('purchase.order')
        period_obj = self.pool.get('account.period')
        qry_supp = ''
        val_part = []
        qry_po = ''
        val_po = []
        
        partner_ids = False
        po_ids = False
        
        data_search = data['form']['supplier_search_vals']
        
        if data['form']['supp_selection'] == 'all':
            qry_supp = 'supplier = True'
            val_part.append(('supplier', '=', True))
        elif data['form']['supp_selection'] == 'supplier':
            qry_supp = 'supplier = True and sundry = False'
            val_part.append(('supplier', '=', True))
            val_part.append(('sundry', '=', False))
        elif data['form']['supp_selection'] == 'sundry':
            qry_supp = 'supplier = True and sundry = True'
            val_part.append(('supplier', '=', True))
            val_part.append(('sundry', '=', True))

        partner_default_from = data['form']['partner_default_from'] and data['form']['partner_default_from'][0] or False
        partner_default_to = data['form']['partner_default_to'] and data['form']['partner_default_to'][0] or False
        partner_input_from = data['form']['partner_input_from'] or False
        partner_input_to = data['form']['partner_input_to'] or False

        if data_search == 'code':
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).ref:
                    data_found = True
                    val_part.append(('ref', '>=', res_partner_obj.browse(cr, uid, partner_default_from).ref))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).ref:
                    data_found = True
                    val_part.append(('ref', '<=', res_partner_obj.browse(cr, uid, partner_default_to).ref))
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_from) + "%' " \
                                    "order by ref limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '>=', qry['ref']))
                if partner_input_to:
                    cr.execute("select ref " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "ref ilike '" + str(partner_input_to) + "%' " \
                                    "order by ref desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('ref', '<=', qry['ref']))
                #print val_part
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='ref ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        elif data_search == 'name':
            if data['form']['filter_selection'] == 'all_vall':
                partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            if data['form']['filter_selection'] == 'def':
                data_found = False
                if partner_default_from and res_partner_obj.browse(cr, uid, partner_default_from) and res_partner_obj.browse(cr, uid, partner_default_from).name:
                    data_found = True
                    val_part.append(('name', '>=', res_partner_obj.browse(cr, uid, partner_default_from).name))
                if partner_default_to and res_partner_obj.browse(cr, uid, partner_default_to) and res_partner_obj.browse(cr, uid, partner_default_to).name:
                    data_found = True
                    val_part.append(('name', '<=', res_partner_obj.browse(cr, uid, partner_default_to).name))
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'input':
                data_found = False
                if partner_input_from:
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_from) + "%' " \
                                    "order by name limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '>=', qry['name']))
                if partner_input_to:
                    cr.execute("select name " \
                                    "from res_partner "\
                                    "where " + qry_supp + " and " \
                                    "name ilike '" + str(partner_input_to) + "%' " \
                                    "order by name desc limit 1")
                    qry = cr.dictfetchone()
                    if qry:
                        data_found = True
                        val_part.append(('name', '<=', qry['name']))
                if data_found:
                    partner_ids = res_partner_obj.search(cr, uid, val_part, order='name ASC')
            elif data['form']['filter_selection'] == 'selection':
                if data['form']['partner_ids']:
                    partner_ids = data['form']['partner_ids']
        result['partner_ids'] = partner_ids
        
        #Period

        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

#purchase order
        qry_po = 'state = "approved"'
        val_po.append(('state','=', 'approved'))

        po_default_from = data['form']['po_default_from'] and data['form']['po_default_from'][0] or False
        po_default_to = data['form']['po_default_to'] and data['form']['po_default_to'][0] or False
        po_input_from = data['form']['po_input_from'] or False
        po_input_to = data['form']['po_input_to'] or False

        if data['form']['po_selection'] == 'all_vall':
            po_ids = purchase_order_obj.search(cr, uid, val_po, order='name ASC')

        if data['form']['po_selection'] == 'def':
            data_found = False
            if po_default_from and purchase_order_obj.browse(cr, uid, po_default_from) and purchase_order_obj.browse(cr, uid, po_default_from).name:
                data_found = True
                val_po.append(('name', '>=', purchase_order_obj.browse(cr, uid, po_default_from).name))
            if po_default_to and purchase_order_obj.browse(cr, uid, po_default_to) and purchase_order_obj.browse(cr, uid, po_default_to).name:
                data_found = True
                val_po.append(('name', '<=', purchase_order_obj.browse(cr, uid, po_default_to).name))
            if data_found:
                po_ids = purchase_order_obj.search(cr, uid, val_po, order='name ASC')
        elif data['form']['po_selection'] == 'input':
            data_found = False
            if po_input_from:
                cr.execute("select name " \
                                "from purchase_order "\
                                "where " + qry_po + " and " \
                                "name ilike '" + str(po_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_po.append(('name', '>=', qry['name']))
            if po_input_to:
                cr.execute("select name " \
                                "from purchase_order "\
                                "where " + qry_po + " and " \
                                "name ilike '" + str(po_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_po.append(('name', '<=', qry['name']))
            if data_found:
                po_ids = purchase_order_obj.search(cr, uid, val_po, order='name ASC')
        elif data['form']['po_selection'] == 'selection':
            if data['form']['po_ids']:
                po_ids = data['form']['po_ids']
        result['po_ids'] = po_ids
        return result

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                                                'date_selection', 'date_from', 'date_to', \
                                                'po_selection','po_default_from','po_default_to', 'po_input_from','po_input_to','po_ids' \
                                                ], context=context)[0]
        for field in ['supp_selection', 'supplier_search_vals', 'filter_selection', 'partner_default_from','partner_default_to','partner_input_from','partner_input_to','partner_ids', \
                    'date_selection', 'date_from', 'date_to', \
                    'po_selection','po_default_from','po_default_to', 'po_input_from','po_input_to','po_ids'\
                    ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        oustanding = 0
        res_partner_obj = self.pool.get('res.partner')
        voucher_obj = self.pool.get('account.voucher')
        pol_obj = self.pool.get('purchase.order.line')

        partner_ids = form['partner_ids'] or False
        partner_qry = (partner_ids and ((len(partner_ids) == 1 and "AND po.partner_id = " + str(partner_ids[0]) + " ") or "AND po.partner_id IN " + str(tuple(partner_ids)) + " ")) or "AND po.partner_id IN (0) "

        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        date_from_qry = date_from and "And po.date_order >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And po.date_order <= '" + str(date_to) + "' " or " "

        po_ids = form['po_ids'] or False
        po_qry = (po_ids and ((len(po_ids) == 1 and "AND po.id = " + str(po_ids[0]) + " ") or "AND po.id IN " + str(tuple(po_ids)) + " ")) or "AND po.id IN (0) "

        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Supplier Delivery Outstanding Purchase Order' + " \n"
        header += 'Supplier Key;Supplier Name;PO Number;Item Description;ETD Date;Order Qty(PCS);Unit Price;Oustanding Qty' + " \n"

        cr.execute(
            "SELECT pol.id as line_id, pt.name as prod_name, po.name as po_name, rp.name as rp_name, rp.ref as rp_ref, " \
            "(pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) as oustanding " \
            "FROM purchase_order_line pol " \
            "LEFT JOIN purchase_order po on pol.order_id = po.id " \
            "LEFT JOIN res_partner rp on po.partner_id = rp.id " \
            "LEFT JOIN product_template pt on pol.product_id = pt.id " \
            "WHERE po.state IN ('approved') " \
            "And (pol.product_qty - coalesce((select sum(sm.product_qty) from stock_move sm where sm.purchase_line_id = pol.id group by sm.product_id),0)) > 0 " \
            + partner_qry \
            + date_from_qry \
            + date_to_qry \
            + po_qry + \
            "order by po.name")
        qry3 = cr.dictfetchall()

        if qry3:
            for t in qry3:
                pol = pol_obj.browse(cr, uid, t['line_id'])
                header += str(t['rp_name'] or '') + ";" + str(t['rp_ref'] or '') + ";" + str(t['po_name'] or '') + ";" + str(t['prod_name'] or '') + ";" + str(pol.estimated_time_departure or '') + ";" + str(pol.product_qty or 0.00) + ";" + str(pol.price_unit or 0.00)+ ";" + str(t['oustanding'] or 0.00) + "\n"

                oustanding += (t['oustanding'] or 0)
        header += "Report Total;;;;;;;" + str(oustanding)  + " \n"

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'PO Outstanding Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','po_outstanding_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'PO Outstanding Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.po.oustanding.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
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
