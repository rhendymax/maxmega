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
from datetime import datetime, timedelta
import base64

class param_inventory_stock_aging_report(osv.osv_memory):
    _name = 'param.inventory.stock.aging.report'
    _description = 'Param Inventory Stock Aging Report'
    _columns = {
        #Brand Selection
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Inventory Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Inventory Brand From', domain=[]),
        'brand_default_to':fields.many2one('product.brand', 'Inventory Brand To', domain=[]),
        'brand_input_from': fields.char('Inventory Brand From', size=128),
        'brand_input_to': fields.char('Inventory Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_inventory_stock_pb_rel', 'report_id', 'product_id', 'Brand', domain=[]),
        #Product Selection
        'product_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'product_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[]),
        'product_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[]),
        'product_input_from': fields.char('Supplier Part No From', size=128),
        'product_input_to': fields.char('Supplier Part No To', size=128),
        'product_ids' :fields.many2many('product.product', 'report_inventory_stock_product_rel', 'report_id', 'product_id', 'Product', domain=[]),
        #Location Selection
        'sl_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Location Filter Selection', required=True),
        'sl_default_from':fields.many2one('stock.location', 'Location From', domain=[('usage', '=', 'internal')]),
        'sl_default_to':fields.many2one('stock.location', 'Location To', domain=[('usage', '=', 'internal')]),
        'sl_input_from': fields.char('Location From', size=128),
        'sl_input_to': fields.char('Location To', size=128),
        'sl_ids' :fields.many2many('stock.location', 'report_inventory_stock_sl_rel', 'report_id', 'sl_id', 'Product', domain=[('usage', '=', 'internal')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
                'brand_selection':'all_vall',
                'product_selection':'all_vall',
                'sl_selection':'all_vall',
              }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.inventory.stock.aging.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.stock.aging.report_landscape',
            'datas': datas,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')

        data['form'] = self.read(cr, uid, ids, ['brand_selection','brand_default_from','brand_default_to','brand_input_from', \
                                                'brand_input_to','brand_ids','product_selection','product_default_from', \
                                                'product_default_to', 'product_input_from','product_input_to','product_ids','sl_selection', \
                                                'sl_default_from','sl_default_to','sl_input_from','sl_input_to','sl_ids'], context=context)[0]
                                                
        for field in ['brand_selection','brand_default_from','brand_default_to','brand_input_from', \
                                                'brand_input_to','brand_ids','product_selection','product_default_from', \
                                                'product_default_to', 'product_input_from','product_input_to','product_ids','sl_selection', \
                                                'sl_default_from','sl_default_to','sl_input_from','sl_input_to','sl_ids']:
            
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        product_brand_obj = self.pool.get('product.brand')
        product_product_obj = self.pool.get('product.product')
        stock_location_obj = self.pool.get('stock.location')

        qry_pb = ''
        val_pb = []
        qry_pp = ''
        val_pp = []
        qry_sl = "usage='internal'"
        val_sl = [('usage', '=','internal')]
        pb_ids = False
        pp_ids = False
        sl_ids = False

#product_product
        brand_default_from = data['form']['brand_default_from'] or False
        brand_default_to = data['form']['brand_default_to'] or False
        brand_input_from = data['form']['brand_input_from'] or False
        brand_input_to = data['form']['brand_input_to'] or False
        brand_default_from_str = brand_default_to_str = ''
        brand_input_from_str = brand_input_to_str= ''

        if data['form']['brand_selection'] == 'all_vall':
            pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')

        elif data['form']['brand_selection'] == 'def':
            data_found = False
            if brand_default_from and product_brand_obj.browse(cr, uid, brand_default_from) and product_brand_obj.browse(cr, uid, brand_default_from).name:
                brand_default_from_str = product_brand_obj.browse(cr, uid, brand_default_from).name
                data_found = True
                val_pb.append(('name', '>=', product_brand_obj.browse(cr, uid, brand_default_from).name))
            if brand_default_to and product_brand_obj.browse(cr, uid, brand_default_to) and product_brand_obj.browse(cr, uid, brand_default_to).name:
                brand_default_to_str = product_brand_obj.browse(cr, uid, brand_default_to).name
                data_found = True
                val_pb.append(('name', '<=', product_brand_obj.browse(cr, uid, brand_default_to).name))
            result['brand_selection'] = '"' + brand_default_from_str + '" - "' + brand_default_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        
        elif data['form']['brand_selection'] == 'input':
            data_found = False
            if brand_input_from:
                brand_input_from_str = brand_input_from
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(brand_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '>=', qry['name']))
            if brand_input_to:
                brand_input_to_str = brand_input_to
                cr.execute("select name " \
                                "from product_brand "\
                                "where name ilike '" + str(brand_input_to) + "%' " \
                                "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_pb.append(('name', '<=', qry['name']))
            result['brand_selection'] = '"' + brand_input_from_str + '" - "' + brand_input_to_str + '"'
            if data_found:
                pb_ids = product_brand_obj.search(cr, uid, val_pb, order='name ASC')
        elif data['form']['brand_selection'] == 'selection':
            pbr_ids = ''
            if data['form']['brand_selection']:
                for pbro in product_brand_obj.browse(cr, uid, data['form']['brand_ids']):
                    pbr_ids += '"' + str(pbro.name) + '",'
                pb_ids = data['form']['brand_ids']
            result['brand_selection'] = '[' + pbr_ids +']'
        result['pb_ids'] = pb_ids

#product_product
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
                val_sl.append(('name', '<=', stock_location_obj.browse(cr, uid, sl_default_to).name))
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
                sl_ids = stock_location_obj.search(cr, uid, val_sl, order='name ASC')
        elif data['form']['sl_selection'] == 'selection':
            slc_ids = ''
            if data['form']['sl_ids']:
                for slo in stock_location_obj.browse(cr, uid, data['form']['sl_ids']):
                    slc_ids += '"' + str(slo.name) + '",'
                sl_ids = data['form']['sl_ids']
            result['sl_selection'] = '[' + slc_ids + ' ]'
        result['sl_ids'] = sl_ids
        return result

    def _get_tplines(self, cr, uid, ids, data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []

        results = []
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        stock_move_obj = self.pool.get('stock.move')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        obj_currency_rate = self.pool.get('res.currency.rate')

        pb_ids = form['pb_ids'] or []
        pp_ids = form['pp_ids'] or []

        product_ids = product_product_obj.search(cr, uid, [('brand_id','in',pb_ids),('id','in',pp_ids)], order='name ASC')
        pp_qry = (product_ids and ((len(product_ids) == 1 and "AND sm.product_id = " + str(product_ids[0]) + " ") or "AND sm.product_id IN " + str(tuple(product_ids)) + " ")) or "AND sm.product_id IN (0) "
        
        sl_ids = form['sl_ids'] or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sld.id = " + str(sl_ids[0]) + " ") or "AND sld.id IN " + str(tuple(sl_ids)) + " ")) or "AND sld.id IN (0) "


#         pb_qry = (pb_ids and ((len(pb_ids) == 1 and "AND sld.id = " + str(sl_ids[0]) + " ") or "AND sld.id IN " + str(tuple(sl_ids)) + " ")) or "AND sld.id IN (0) "


        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Aging Report' + " \n"
        header += ('brand_selection' in form and 'Brand Filter Selection : ' + form['brand_selection'] + " \n") or ''
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += 'Inv Key;Location;Qty O-H;Cost($);< 30;US$ < 30;31-60;US$ 31-60;61-90;US$ 61-90;91-120;US$ 91-120;121-150;US$ 121-150;151-180;US$ 151-180;> 180;US$ > 180' + " \n"
        #check oustanding qty and balance
        #in
        product_combine_ids = {}

        incoming_list = physical_list = internal_list = []
        #in
        cr.execute(
            "select pb.name as brand_name, pb.id as brand_id, sld.id as location_id, sld.name as location_name, coalesce(sp.do_date, sp.date ::timestamp::date) as document_date, " \
            "sm.product_id as product_id, pt.name as product_name, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) as oustanding_qty, " \
            "round(((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit * (" \
            "select rate from res_currency_rate where currency_id = rc.currency_id and name <= sp.do_date order by name desc limit 1) / " \
            "(select rate from res_currency_rate where currency_id = pr_p.currency_id and name <= sp.do_date order by name desc limit 1) " \
            "),2) as total_cost " \
            "from stock_move sm " \
            "left join stock_location sld on sld.id = sm.location_dest_id " \
            "left join stock_location sl on sl.id = sm.location_id " \
            "left join stock_picking sp on sm.picking_id = sp.id " \
            "left join product_template pt on sm.product_id = pt.id " \
            "left join product_product pp on sm.product_id = pp.id " \
            "left join product_brand pb on pp.brand_id = pb.id " \
            "left join res_company rc on sp.company_id = rc.id " \
            "left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
            "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) > 0 " \
            "and sp.type != 'internal' and sm.picking_id is not null " \
            + pp_qry + sl_qry + \
            "order by sm.product_id ")

        incoming_list = cr.dictfetchall()

        #Physical


        cr.execute(
            "select pb.name as brand_name, pb.id as brand_id, sld.id as location_id, sld.name as location_name, si.date ::timestamp::date as document_date, " \
            "sm.product_id as product_id, pt.name as product_name, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) as oustanding_qty, " \
            "round((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit,2) as total_cost " \
            "from stock_move sm " \
            "left join stock_location sld on sld.id = sm.location_dest_id " \
            "left join stock_location sl on sl.id = sm.location_id " \
            "left join product_template pt on sm.product_id = pt.id " \
            "left join stock_inventory si on si.id = (select inventory_id from stock_inventory_move_rel where move_id = sm.id) " \
            "left join product_product pp on sm.product_id = pp.id " \
            "left join product_brand pb on pp.brand_id = pb.id " \
            "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) > 0 " \
            "and sm.picking_id is null " \
            + pp_qry + sl_qry + \
            "order by sm.product_id ")
        physical_list = cr.dictfetchall()

        list_combine = incoming_list + physical_list


#         #Internal
        cr.execute(
            "select pb.name as brand_name, pb.id as brand_id, sld.id as location_id, sld.name as location_name, coalesce(sp.do_date, sp.date ::timestamp::date) as document_date, sm.product_id as product_id, pt.name as product_name, sm.id as id "
            "from stock_move sm " \
            "left join stock_location sld on sld.id = sm.location_dest_id " \
            "left join stock_location sl on sl.id = sm.location_id " \
            "left join stock_picking sp on sm.picking_id = sp.id " \
            "left join product_template pt on sm.product_id = pt.id " \
            "left join product_product pp on sm.product_id = pp.id " \
            "left join product_brand pb on pp.brand_id = pb.id " \
            "left join res_company rc on sp.company_id = rc.id " \
            "left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
            "where sm.state = 'done' and sld.usage = 'internal' " \
            "and sp.type = 'internal' and sm.picking_id is not null " \
            + pp_qry + sl_qry + \
            "order by sm.product_id ")
        internal_qry = cr.dictfetchall()
        for int_q in internal_qry:
            product_id = int_q['product_id']
            internal_move_control_ids = cost_price_fifo_obj.internal_get(cr, uid, int_q['id'])
            if internal_move_control_ids:
                int_res = []
                for int in internal_move_control_ids:
                    int_sm = stock_move_obj.browse(cr, uid, int['move_id'], context=context)
                    if int_sm.picking_id:
                        int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_sm.picking_id.company_id.id, context=context).currency_id.id
##############
                        rate_id = False
                        int_p_curr_id = int_sm.picking_id.pricelist_id.currency_id.id
                        int_res.append({
                                         'doc_no' : int_sm.picking_id.name,
                                         'doc_curr_id' : int_p_curr_id,
                                         'home_curr_id' : int_ptype_src,
                                         'document_date': int_sm.picking_id.do_date,
                                         'move_id' : int_sm.id,
                                         'product_qty' : int['product_qty'],
                                         'unit_cost_price' : int_sm.price_unit,
                                         })
                    else:
                        if int_sm.stock_inventory_ids:
                            for int_si in int_sm.stock_inventory_ids:
                                int_ptype_src = self.pool.get('res.company').browse(cr, uid, int_si.company_id.id, context=context).currency_id.id
                                int_res.append({
                                                 'doc_no' : int_si.name,
                                                 'doc_curr_id' : int_ptype_src,
                                                 'home_curr_id' : int_ptype_src,
                                                 'document_date': int_si.date,
                                                 'move_id' : int_sm.id,
                                                 'product_qty' : int['product_qty'],
                                                 'unit_cost_price' : int_sm.price_unit,
                                                 })
                int_res = int_res and sorted(int_res, key=lambda val_res: val_res['document_date']) or []
                if int_res:
#                                raise osv.except_osv(_('Debug !'), _(str(int_res2)))
#                                if sm.picking_id.name == '1300597MTF':
#                                    print 'yess'
#                                    print int_res2
                    for int_temp2 in int_res:
                        int_qty_out = 0.00
#                             int_fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('in_move_id','=',sm.id), ('int_in_move_id','=',int_temp2['move_id'])]), context=context)
                        cr.execute(
                           "select coalesce(sum(fc.quantity),0) as quantity from fifo_control fc " \
                            "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                            "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                            "where fc.in_move_id = " + str(int_q['id']) + " and fc.int_in_move_id = " + str(int_temp2['move_id']))
                        int_fifo_control_ids = cr.dictfetchall()
                        if int_fifo_control_ids:
 
                            for int_val in int_fifo_control_ids:
                                int_qty_out += int_val['quantity']
                        qty_internal = int_temp2['product_qty']
                        int_qty_sisa = qty_internal - int_qty_out
                        if int_qty_sisa > 0:
                            x_ptype_src = int_temp2['home_curr_id']
    ########################
                            x_rate_id = False
                            x_p_curr_id = int_temp2['doc_curr_id']
                            if x_p_curr_id != x_ptype_src:
                                x_tgl = int_temp2['document_date']
                                x_tgl = datetime.strptime(x_tgl, '%Y-%m-%d %H:%M:%S').date()
                                x_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_p_curr_id),
                                                                              ('name','<=', x_tgl)
                                                                              ])
                                if x_rate_ids:
                                    x_rate_id = x_rate_ids[0]
                                else:
                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                x_home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', x_ptype_src),
                                                                              ('name','<=', x_tgl)
                                                                              ])
                                if x_home_rate_ids:
                                    x_home_rate_id = x_home_rate_ids[0]
                                else:
                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
     
                            if x_rate_id:
                                x_total_unit_cost_price = (int_qty_sisa * int_temp2['unit_cost_price']) * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                            else:
                                x_total_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, (int_qty_sisa * int_temp2['unit_cost_price']), round=False)
                            x_total_unit_cost_price = product_product_obj.round_p(cr, uid, x_total_unit_cost_price, 'Purchase Price',)
                            
 
                            list_combine.append({
                                                 'brand_id': int_q['brand_id'],
                                                 'brand_name': int_q['brand_name'],
                                                 'location_id': int_q['location_id'],
                                                 'location_name': int_q['location_name'],
                                                 'document_date': int_q['document_date'],
                                                 'product_id': int_q['product_id'],
                                                 'product_name': int_q['product_name'],
                                                 'oustanding_qty' : int_qty_sisa,
                                                 'total_cost' : x_total_unit_cost_price
                                                 }
                                                )

        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['document_date']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['location_name']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['product_name']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['brand_name']) or []
#         print list_combine
        if list_combine:
            brand_id = False
            brand_name = ''
            total_qty = 0
            total_cost = 0
            for lst in list_combine:

                d = datetime.strptime(lst['document_date'], '%Y-%m-%d')
                d = d.date()
                delta = datetime.now().date() - d
                daysremaining = delta.days
                if lst['brand_id'] != brand_id:
                    if brand_id:
                        header += ";Total for Brand %s;%s;%s; \n"%(brand_name,total_qty,total_cost)
                    total_qty = lst['oustanding_qty']
                    total_cost = lst['total_cost']
                    brand_id = lst['brand_id']
                    brand_name = lst['brand_name']
                    header += "%s \n"%lst['brand_name']
#                     header += 'Inv Key;Location;Qty O-H;Cost($);< 30;US$ < 30;31-60;US$ 31-60;61-90;US$ 61-90;91-120;US$ 91-120;121-150;US$ 121-150;151-180;US$ 151-180;> 180;US$ > 180' + " \n"
                    header += "%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s; \n"%(lst['product_name'],lst['location_name'],lst['oustanding_qty'],lst['total_cost'] \
                                                 ,daysremaining < 31 and lst['oustanding_qty'] or 0, daysremaining < 31 and lst['total_cost'] or 0 \
                                                 ,((daysremaining > 30 and daysremaining < 61) and lst['oustanding_qty']) or 0, ((daysremaining > 30 and daysremaining < 61) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 60 and daysremaining < 91) and lst['oustanding_qty']) or 0, ((daysremaining > 60 and daysremaining < 91) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 90 and daysremaining < 121) and lst['oustanding_qty']) or 0, ((daysremaining > 90 and daysremaining < 121) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 120 and daysremaining < 151) and lst['oustanding_qty']) or 0, ((daysremaining > 120 and daysremaining < 151) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 150 and daysremaining < 181) and lst['oustanding_qty']) or 0, ((daysremaining > 150 and daysremaining < 181) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 180) and lst['oustanding_qty']) or 0, ((daysremaining > 180) and lst['total_cost'])  or 0 \
                                                 )
                else:
                    total_qty += lst['oustanding_qty']
                    total_cost += lst['total_cost']
                    header += "%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s;%s; \n"%(lst['product_name'],lst['location_name'],lst['oustanding_qty'],lst['total_cost'] \
                                                 ,daysremaining < 31 and lst['oustanding_qty'] or 0, daysremaining < 31 and lst['total_cost'] or 0 \
                                                 ,((daysremaining > 30 and daysremaining < 61) and lst['oustanding_qty']) or 0, ((daysremaining > 30 and daysremaining < 61) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 60 and daysremaining < 91) and lst['oustanding_qty']) or 0, ((daysremaining > 60 and daysremaining < 91) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 90 and daysremaining < 121) and lst['oustanding_qty']) or 0, ((daysremaining > 90 and daysremaining < 121) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 120 and daysremaining < 151) and lst['oustanding_qty']) or 0, ((daysremaining > 120 and daysremaining < 151) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 150 and daysremaining < 181) and lst['oustanding_qty']) or 0, ((daysremaining > 150 and daysremaining < 181) and lst['total_cost'])  or 0 \
                                                 ,((daysremaining > 180) and lst['oustanding_qty']) or 0, ((daysremaining > 180) and lst['total_cost'])  or 0 \
                                                 )
            if brand_id:
                header += ";Total for Brand %s;%s;%s; \n"%(brand_name,total_qty,total_cost)

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Inventory Aging Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','inventory_stock_aging_report_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Inventory Aging Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.inventory.stock.aging.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }
param_inventory_stock_aging_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
