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
#from tools import float_round, float_is_zero, float_compare

class param_inventory_free_balance_report(osv.osv_memory):
    _name = 'param.inventory.free.balance.report'
    _description = 'Param Inventory Free Balance Report'
    _columns = {
        #Product Selection
        'product_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'product_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[], required=False),
        'product_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[], required=False),
        'product_input_from': fields.char('Supplier Part No From', size=128),
        'product_input_to': fields.char('Supplier Part No To', size=128),
        'product_ids' :fields.many2many('product.product', 'report_inventory_balance_product_rel', 'report_id', 'product_id', 'Product', domain=[]),
        #Location Selection
        'sl_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Location Filter Selection', required=True),
        'sl_default_from':fields.many2one('stock.location', 'Location From', domain=[('usage', '=', 'internal')], required=False),
        'sl_default_to':fields.many2one('stock.location', 'Location To', domain=[('usage', '=', 'internal')], required=False),
        'sl_input_from': fields.char('Location From', size=128),
        'sl_input_to': fields.char('Location To', size=128),
        'sl_ids' :fields.many2many('stock.location', 'report_inventory_balance_sl_rel', 'report_id', 'sl_id', 'Location', domain=[('usage', '=', 'internal')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'product_selection': 'all_vall',
        'sl_selection': 'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.inventory.ledger.details.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.free.balance.report_landscape',
            'datas': datas,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')

        data['form'] = self.read(cr, uid, ids, ['product_selection','product_default_from','product_default_to', 'product_input_from','product_input_to','product_ids', \
                                                'sl_selection', 'sl_default_from','sl_default_to', 'sl_input_from','sl_input_to','sl_ids', \
                                                ], context=context)[0]
        for field in ['product_selection','product_default_from','product_default_to', 'product_input_from','product_input_to','product_ids', \
                                                'sl_selection', 'sl_default_from','sl_default_to', 'sl_input_from','sl_input_to','sl_ids']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        new_ids = ids
        result = {}
        pp_ids = False
        sl_ids = False
        product_product_obj = self.pool.get('product.product')
        stock_location_obj = self.pool.get('stock.location')
        qry_pp = ''
        val_pp = []
        qry_sl = ''
        val_sl = []

        pp_default_from = data['form']['product_default_from'] or False
        pp_default_to = data['form']['product_default_to'] or False
        pp_input_from = data['form']['product_input_from'] or False
        pp_input_to = data['form']['product_input_to'] or False
        pp_default_from_str = pp_default_to_str = ''
        pp_input_from_str = pp_input_to_str= ''

        if data['form']['product_selection'] == 'all_vall':
            pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        
        elif data['form']['product_selection'] == 'def':
            data_found = False
            if pp_default_from and product_product_obj.browse(cr, uid, pp_default_from) and product_product_obj.browse(cr, uid, pp_default_from).name:
                pp_default_from_str = product_product_obj.browse(cr, uid, pp_default_from).name
                data_found = True
                val_pp.append(('name', '>=', product_product_obj.browse(cr, uid, pp_default_from).name))
            if pp_default_to and product_product_obj.browse(cr, uid, pp_default_to) and product_product_obj.browse(cr, uid, pp_default_to).name:
                pp_default_to_str = product_product_obj.browse(cr, uid, pp_default_to).name
                data_found = True
                val_pp.append(('name', '<=', product_product_obj.browse(cr, uid, pp_default_to).name))
            result['pp_selection'] = '"' + pp_default_from_str + '" - "' + pp_default_to_str + '"'
            if data_found:
                pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        
        elif data['form']['product_selection'] == 'input':
            data_found = False
            if pp_input_from:
                pp_input_from_str = pp_input_from
                cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '>=', qry['name']))
            if pp_input_to:
                pp_input_to_str = pp_input_to
                cr.execute("select name " \
                                "from product_template "\
                                "where name ilike '" + str(pp_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pp.append(('name', '<=', qry['name']))
            result['pp_selection'] = '"' + pp_input_from_str + '" - "' + pp_input_to_str + '"'
            if data_found:
                pp_ids = product_product_obj.search(cr, uid, val_pp, order='name ASC')
        elif data['form']['product_selection'] == 'selection':
            ppr_ids = ''
            if data['form']['product_ids']:
                for ppro in product_product_obj.browse(cr, uid, data['form']['product_ids']):
                    ppr_ids += '"' + str(ppro.name) + '",'
                pp_ids = data['form']['product_ids']
            result['pp_selection'] = '[' + ppr_ids +']'
        result['pp_ids'] = pp_ids

        #Stock Location
        sl_default_from = data['form']['sl_default_from'] or False
        sl_default_to = data['form']['sl_default_to'] or False
        sl_input_from = data['form']['sl_input_from'] or False
        sl_input_to = data['form']['sl_input_to'] or False
        sl_default_from_str = sl_default_to_str = ''
        sl_input_from_str = sl_input_to_str= ''

        if data['form']['sl_selection'] == 'all_vall':
            sl_ids = stock_location_obj.search(cr, uid, val_sl, order='name ASC')

        elif data['form']['sl_selection'] == 'def':
            data_found = False
            if sl_default_from and stock_location_obj.browse(cr, uid, sl_default_from) and stock_location_obj.browse(cr, uid, sl_default_from).name:
                sl_default_from_str = stock_location_obj.browse(cr, uid, sl_default_from).name
                data_found = True
                val_sl.append(('name', '>=', stock_location_obj.browse(cr, uid, sl_default_from).name))
            if sl_default_to and stock_location_obj.browse(cr, uid, sl_default_to) and stock_location_obj.browse(cr, uid, sl_default_to).name:
                sl_default_to_str = stock_location_obj.browse(cr, uid, sl_default_to).name
                data_found = True
                val_sl.append(('name', '<=', stock_location_obj.browse(cr, self.uid, sl_default_to).name))
            result['sl_selection'] = '"' + sl_default_from_str + '" - "' + sl_default_to_str + '"'
            if data_found:
                sl_ids = stock_location_obj.search(cr, uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'input':
            data_found = False
            if sl_input_from:
                sl_input_from_str = sl_input_from
                cr.execute("select name " \
                                "from stock_location "\
                                "where name ilike '" + str(sl_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sl.append(('name', '>=', qry['name']))
            if sl_input_to:
                sl_input_to_str = sl_input_to
                cr.execute("select name " \
                                "from stock_location "\
                                "where name ilike '" + str(sl_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sl.append(('name', '<=', qry['name']))
            result['sl_selection'] = '"' + sl_input_from_str + '" - "' + sl_input_to_str + '"'
            if data_found:
                sl_ids = stock_location.search(cr, uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'selection':
            slc_ids = ''
            if data['form']['sl_ids']:
                for slo in stock_location_obj.browse(cr, uid, data['form']['sl_ids']):
                    slc_ids += '"' + str(slo.name) + '",'
                sl_ids = data['form']['sl_ids']
            result['sl_selection'] = '[' + slc_ids + ' ]'
        result['sl_ids'] = sl_ids

        return result

    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []

        results = []
        cr = cr
        uid = uid
        stock_location_obj = self.pool.get('stock.location')
        product_product_obj = self.pool.get('product.product')
        plw_obj = self.pool.get('product.location.wizard')
        pp_ids = form['pp_ids'] or False
        sl_ids = form['sl_ids'] or False
#         if pp_ids and len(pp_ids) > 3000:
#             raise osv.except_osv(_('Data Limitation !'), _('the product data has limit to 3000 product, pls select the product to view with least than 3000 product'))
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND id = " + str(sl_ids[0]) + " ") or "AND id IN " + str(tuple(sl_ids)) + " ")) or "AND id IN (0) "

        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Free Balance Report' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += 'SPN No;Qty On Hand;Qty GRN Allocated;Qty GRN Un-Allocated;Total SO Qty;Qty On Hand Free;Qty On Hand Allocated;Quantity Free Balance' + " \n"

        if pp_ids:
            data_found = False
            ctx = {'location_id': sl_ids}
            cpf_loc = plw_obj.stock_location_get(cr, uid, pp_ids, context=ctx)
            if cpf_loc:
                for res_f1 in cpf_loc:
#                 if data_found == False:
#                     header += str(r['sl_name'] or '') + "\n"
#                     data_found = True
#                 if data_found == True and 
#                 raise osv.except_osv(_('Data Limitation !'), _('the product data has limit to 3000 product, pls select the product to view with least than 3000 product'))
                    if data_found == False:
                        header += str(res_f1['location_name'] or '') + "\n"
                        data_found = str(res_f1['location_id'] or '')
                        qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
                        qty_onhand += res_f1['qty_available'] or 0.00
                        qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
                        qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
                        total_so_qty += res_f1['qty_booked'] or 0.00
                        qty_on_hand_free += res_f1['qty_free'] or 0.00
                        qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
                        qty_free_balance += res_f1['qty_free_balance'] or 0.00
                        header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
                                        + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
                                        + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
                                        + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"
                
                    else:
                        if data_found == str(res_f1['location_id'] or ''):
                            qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
                            qty_onhand += res_f1['qty_available'] or 0.00
                            qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
                            qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
                            total_so_qty += res_f1['qty_booked'] or 0.00
                            qty_on_hand_free += res_f1['qty_free'] or 0.00
                            qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
                            qty_free_balance += res_f1['qty_free_balance'] or 0.00
                            header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
                                            + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
                                            + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
                                            + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"
                        else:
                            header += str(res_f1['location_name'] or '') + "\n"
                            data_found = str(res_f1['location_id'] or '')
                            qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
                            qty_onhand += res_f1['qty_available'] or 0.00
                            qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
                            qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
                            total_so_qty += res_f1['qty_booked'] or 0.00
                            qty_on_hand_free += res_f1['qty_free'] or 0.00
                            qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
                            qty_free_balance += res_f1['qty_free_balance'] or 0.00
                            header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
                                            + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
                                            + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
                                            + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"


#         cr.execute("select id as sl_id, name as sl_name \
#         from stock_location \
#         where id not in (select distinct location_id from stock_location WHERE location_id IS NOT NULL) "\
#         + sl_qry  +\
#         "order by name")
# 
#         qry2 = cr.fetchall()
#         if qry2:
#             for r in qry2:
#                 if pp_ids:
#                     data_found = False
# #                     for product_id in product_product_obj.browse(cr, uid, pp_ids):
#                     ctx = {'location_id': r['sl_id']}
#                     cpf_loc = plw_obj.stock_location_get(cr, uid, pp_ids, context=ctx)
#                     if cpf_loc:
#                         for res_f1 in cpf_loc:
#                             if data_found == False:
#                                 header += str(res_f1['sl_name'] or '') + "\n"
#                                 data_found = str(res_f1['sl_name'] or '')
#                                 qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
#                                 qty_onhand += res_f1['qty_available'] or 0.00
#                                 qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
#                                 qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
#                                 total_so_qty += res_f1['qty_booked'] or 0.00
#                                 qty_on_hand_free += res_f1['qty_free'] or 0.00
#                                 qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
#                                 qty_free_balance += res_f1['qty_free_balance'] or 0.00
#                                 header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
#                                                 + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
#                                                 + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
#                                                 + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"
#                         
#                             else:
#                                 if data_found == str(res_f1['sl_name'] or ''):
#                                     qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
#                                     qty_onhand += res_f1['qty_available'] or 0.00
#                                     qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
#                                     qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
#                                     total_so_qty += res_f1['qty_booked'] or 0.00
#                                     qty_on_hand_free += res_f1['qty_free'] or 0.00
#                                     qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
#                                     qty_free_balance += res_f1['qty_free_balance'] or 0.00
#                                     header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
#                                                     + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
#                                                     + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
#                                                     + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"
#                                 else:
#                                     header += str(res_f1['sl_name'] or '') + "\n"
#                                     data_found = str(res_f1['sl_name'] or '')
#                                     qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
#                                     qty_onhand += res_f1['qty_available'] or 0.00
#                                     qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
#                                     qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
#                                     total_so_qty += res_f1['qty_booked'] or 0.00
#                                     qty_on_hand_free += res_f1['qty_free'] or 0.00
#                                     qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
#                                     qty_free_balance += res_f1['qty_free_balance'] or 0.00
#                                     header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
#                                                     + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
#                                                     + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
#                                                     + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"

#                         for res_f1 in cpf_loc:
#                             qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
#                             qty_onhand += res_f1['qty_available'] or 0.00
#                             qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
#                             qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
#                             total_so_qty += res_f1['qty_booked'] or 0.00
#                             qty_on_hand_free += res_f1['qty_free'] or 0.00
#                             qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
#                             qty_free_balance += res_f1['qty_free_balance'] or 0.00
#                             header += ";" + str(res_f1['prod_name'] or '') + ";" + str("%.2f" % qty_onhand or 0) + ";" \
#                                             + str("%.2f" % qty_grn_allocated or 0) + ";" + str("%.2f" % qty_grn_unallocated or 0) + ";" \
#                                             + str("%.2f" % total_so_qty or 0) + ";" + str("%.2f" % qty_on_hand_free or 0) + ";" \
#                                             + str("%.2f" % qty_on_hand_allocated or 0) + ";" + str("%.2f" % qty_free_balance or 0) + " \n"



#         if sl_ids:
#             for location in stock_location_obj.browse(cr, uid, sl_ids):
#                 sl_checking = stock_location_obj.search(cr, uid, [('location_id','=',location.id)])
#                 if sl_checking:
#                     continue
#                 res = {}
#                 vals_ids = []
#                 total_cost = 0
#                 total_qty = 0
#                 if pp_ids:
#                     for product_id in product_product_obj.browse(cr, uid, pp_ids):
#                         ctx = {'location_id': location.id}
#                         cpf_loc = plw_obj.stock_location_get(cr, uid, product_id.id, context=ctx)
#                         if cpf_loc:
#                             qty_onhand = qty_grn_allocated = qty_grn_unallocated = total_so_qty = qty_on_hand_free = qty_on_hand_allocated = qty_free_balance = 0
#                             for res_f1 in cpf_loc:
#                                 qty_onhand += res_f1['qty_available'] or 0.00
#                                 qty_grn_allocated += res_f1['qty_incoming_booked'] or 0.00
#                                 qty_grn_unallocated += res_f1['qty_incoming_non_booked'] or 0.00
#                                 total_so_qty += res_f1['qty_booked'] or 0.00
#                                 qty_on_hand_free += res_f1['qty_free'] or 0.00
#                                 qty_on_hand_allocated += res_f1['qty_allocated'] or 0.00
#                                 qty_free_balance += res_f1['qty_free_balance'] or 0.00
#                             
#                             vals_ids.append({
#                             'prod_name' : product_id.name,
#                             'qty_onhand' : qty_onhand,
#                             'qty_grn_allocated' : qty_grn_allocated,
#                             'qty_grn_unallocated' : qty_grn_unallocated,
#                             'total_so_qty' : total_so_qty,
#                             'qty_on_hand_free' : qty_on_hand_free,
#                             'qty_on_hand_allocated' : qty_on_hand_allocated,
#                             'qty_free_balance' : qty_free_balance,
#                             })
#                             
#                     if not vals_ids:
#                         continue
#                     res['pro_lines'] = vals_ids
#                     res['loc_name'] = location.name or ''
#                     header += str(res['loc_name'] or '') + "\n"
#                     for pro_lines in res['pro_lines']:
#                         header += str(pro_lines['prod_name'] or '') + ";" + str("%.2f" % pro_lines['qty_onhand'] or 0) + ";" \
#                                             + str("%.2f" % pro_lines['qty_grn_allocated'] or 0) + ";" + str("%.2f" % pro_lines['qty_grn_unallocated'] or 0) + ";" \
#                                             + str("%.2f" % pro_lines['total_so_qty'] or 0) + ";" + str("%.2f" % pro_lines['qty_on_hand_free'] or 0) + ";" \
#                                             + str("%.2f" % pro_lines['qty_on_hand_allocated'] or 0) + ";" + str("%.2f" % pro_lines['qty_free_balance'] or 0) + " \n"
#                     results.append(res)

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Inventory Free Balance Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','inventory_free_balance_report_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Inventory Free Balance Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.inventory.free.balance.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_inventory_free_balance_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
