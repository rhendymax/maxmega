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
from tools import float_round, float_is_zero, float_compare
from tools.translate import _

class param_inventory_valuation_report(osv.osv_memory):
    _name = 'param.inventory.valuation.report'
    _description = 'Param Inventory Valuation Report Checking'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        #Product Selection
        'product_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'product_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[]),
        'product_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[]),
        'product_input_from': fields.char('Supplier Part No From', size=128),
        'product_input_to': fields.char('Supplier Part No To', size=128),
        'product_ids' :fields.many2many('product.product', 'report_inv_valdetail_product_rel', 'report_id', 'product_id', 'Product', domain=[]),
        #Location Selection
        'sl_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Location Filter Selection', required=True),
        'sl_default_from':fields.many2one('stock.location', 'Location From', domain=[('usage', '=', 'internal')]),
        'sl_default_to':fields.many2one('stock.location', 'Location To', domain=[('usage', '=', 'internal')]),
        'sl_input_from': fields.char('Location From', size=128),
        'sl_input_to': fields.char('Location To', size=128),
        'sl_ids' :fields.many2many('stock.location', 'report_inv_valdetail_sl_rel', 'report_id', 'sl_id', 'Location', domain=[('usage', '=', 'internal')]),
        'valid': fields.selection([('valid','Valid'),('non_valid','Non Valid'),],'Valid'),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
#        'date_from': fields.date("From Date", required=True),
#        'date_to': fields.date("To Date", required=True),
#        'product_from':fields.many2one('product.product', 'Supplier Part No From', required=False),
#        'product_to':fields.many2one('product.product', 'Supplier Part No To', required=False),
#        'location_from':fields.many2one('stock.location', 'Location From', required=False),
#        'location_to':fields.many2one('stock.location', 'Location To', required=False),
#        'valid': fields.selection([
#            ('valid','Valid'),
#            ('non_valid','Non Valid'),
#            ],'Valid'),
#         'product_id': fields.many2one('product.product', 'Item Code', domain=[('sale_ok','=',True)], change_default=True),
    }

    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d')
        'date_selection':'none_sel',
        'product_selection': 'all_vall',
        'sl_selection': 'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.inventory.valuation.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.valuation.report_landscape',
            'datas': datas,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')

        data['form'] = self.read(cr, uid, ids, ['date_selection', 'date_from', 'date_to','product_selection','product_default_from', \
                                                'product_default_to', 'product_input_from','product_input_to','product_ids','sl_selection', \
                                                'sl_default_from','sl_default_to','sl_input_from','sl_input_to','sl_ids','valid'], context=context)[0]
                                                
        for field in ['date_selection', 'date_from', 'date_to','product_selection','product_default_from','product_default_to', \
                      'product_input_from','product_input_to','product_ids','sl_selection','sl_default_from','sl_default_to', \
                      'sl_input_from','sl_input_to','sl_ids','valid']:
            
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        product_product_obj = self.pool.get('product.product')
        stock_location_obj = self.pool.get('stock.location')

        qry_pp = ''
        val_pp = []
        qry_sl = "usage='internal'"
        val_sl = [('usage', '=', 'internal')]
        pp_ids = False
        sl_ids = False
        result['date_selection'] = data['form']['date_selection']
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to']
#Valid Selection
        valid= False
        if data['form']['valid'] == 'valid':
           valid = 'Valid'
        elif data['form']['valid'] == 'non_valid':
            valid = 'Non Valid'
        result['valid_selection'] = valid
        result['valid'] = data['form']['valid'] or False
        
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
                qry = self.cr.dictfetchone()
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
                                "where " + qry_sl + " and " \
                                "name ilike '" + str(sl_input_from) + "%' " \
                                "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_sl.append(('name', '>=', qry['name']))
            if sl_input_to:
                sl_input_to_str = sl_input_to
                cr.execute("select name " \
                                "from stock_location "\
                                "where " + qry_sl + " and " \
                                "name ilike '" + str(sl_input_to) + "%' " \
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

    def _get_tplines(self, cr, uid, ids,data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        count = 0
        results = []
        val_product = []
        val_location = []
        valid_x = form['valid'] or False
        
        date_selection = form['date_selection'] or False
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False

        date_from_qry = date_from and "And sp.do_date >= '" + str(date_from) + "' " or " "
        date_to_qry = date_to and "And sp.do_date <= '" + str(date_to) + "' " or " "
        date_from_qry_si = date_from and "And si.date ::timestamp::date >= '" + str(date_from) + "' " or " "
        date_to_qry_si = date_to and "And si.date ::timestamp::date <= '" + str(date_to) + "' " or " "
        date_from_qry_int = date_from and "And sp.date ::timestamp::date >= '" + str(date_from) + "' " or " "
        date_to_qry_int = date_to and "And sp.date ::timestamp::date  <= '" +str(date_to) + "' " or " "
        pp_ids = form['pp_ids'] or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND sm.product_id = " + str(pp_ids[0]) + " ") or "AND sm.product_id IN " + str(tuple(pp_ids)) + " ")) or "AND sm.product_id IN (0) "
        
        sl_ids = form['sl_ids'] or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sld.id = " + str(sl_ids[0]) + " ") or "AND sld.id IN " + str(tuple(sl_ids)) + " ")) or "AND sld.id IN (0) "
        
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        stock_move_obj = self.pool.get('stock.move')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        obj_currency_rate = self.pool.get('res.currency.rate')
        move_allocated_control_obj = self.pool.get('move.allocated.control')
        valid_selection = form['valid_selection'] or False
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Valuation Report' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('date_showing' in form and 'Date : ' + str(form['date_showing']) + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += (valid_selection and 'Valid Selection : ' + str(valid_selection) + " \n") or ''
        header += 'Source Internal No;Document No;Date;Location;Qty On Hand(PCS);Unit Cost;Total Cost' + " \n"
        
#        if product_from and product_product_obj.browse(cr, uid, product_from) and product_product_obj.browse(cr, uid, product_from).name:
#            val_product.append(('name', '>=', product_product_obj.browse(cr, uid, product_from).name))
#        if product_to and product_product_obj.browse(cr, uid, product_to) and product_product_obj.browse(cr, uid, product_to).name:
#            val_product.append(('name', '<=', product_product_obj.browse(cr, uid, product_to).name))
#        if location_from and stock_location_obj.browse(cr, uid, location_from) and stock_location_obj.browse(cr, uid, location_from).name:
#            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
#        if location_to and stock_location_obj.browse(cr, uid, location_to) and stock_location_obj.browse(cr, uid, location_to).name:
#            val_location.append(('name', '<=', stock_location_obj.browse(cr, uid, location_to).name))

#        product_ids = product_product_obj.search(cr, uid, pp_ids,order='name')
#        location_ids = stock_location_obj.search(cr, uid, sl_ids)
#        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)
        incoming_list = physical_list = internal_list = []
        cr.execute(
            "select '' as int_doc_no, False as int_move_id, sm.product_id as product_id, pt.name as product_name, " \
            "round(sm.price_unit * (select rate from res_currency_rate where currency_id = rc.currency_id and name <= sp.do_date order by name desc limit 1) /  " \
            "(select rate from res_currency_rate where currency_id = pr_p.currency_id and name <= sp.do_date order by name desc limit 1),5) as unit_cost_price, " \
            "pr_p.currency_id as doc_curr_id, rc.currency_id as home_curr_id, sp.do_date as document_date, sp.name as document_no, sm.id as move_id, " \
            "sm.location_dest_id as location_id, sld.name as location_name, sm.price_unit as doc_ucp, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit as doc_total_ucp, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) as product_qty, round(((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit *  " \
            "(select rate from res_currency_rate where currency_id = rc.currency_id and name <= sp.do_date order by name desc limit 1) /  " \
            "(select rate from res_currency_rate where currency_id = pr_p.currency_id and name <= sp.do_date order by name desc limit 1) ),2) as total_cost_price, " \
            "coalesce((select sum(mal.quantity - case when mal.int_move_id is null then coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.int_in_move_id = mal.int_move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) else coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "END) as grand_total from move_allocated_control mal where mal.move_id = sm.id),0) as allocated_qty, " \
            "(sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) - coalesce((select sum(mal.quantity - case when mal.int_move_id is null then coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.int_in_move_id = mal.int_move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "else coalesce((select sum((select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "END) as grand_total from move_allocated_control mal where mal.move_id = sm.id),0) as qty_onhand_free " \
            "from stock_move sm left join stock_location sld on sld.id = sm.location_dest_id left join stock_location sl on sl.id = sm.location_id " \
            "left join product_template pt on sm.product_id = pt.id " \
            "left join stock_picking sp on sm.picking_id = sp.id left join res_company rc on sp.company_id = rc.id left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
            "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) > 0 and sp.type != 'internal' and sm.picking_id is not null " \
            + date_from_qry \
            + date_to_qry \
            + sl_qry + \
            pp_qry + \
            "order by sld.name, sld.id")


        incoming_list = cr.dictfetchall()

        cr.execute(
            "select '' as int_doc_no, False as int_move_id, sm.product_id as product_id, pt.name as product_name," \
            "sm.price_unit as unit_cost_price, " \
            "rc.currency_id as doc_curr_id, rc.currency_id as home_curr_id, si.date ::timestamp::date as document_date, si.name as document_no, sm.id as move_id, " \
            "sm.location_dest_id as location_id, sld.name as location_name, sm.price_unit as doc_ucp, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit as doc_total_ucp, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) as product_qty, round(((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc  " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id  " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id)  " \
            "where fc.in_move_id = sm.id),0)) * sm.price_unit),2) as total_cost_price, " \
            "coalesce((select sum(mal.quantity - case when mal.int_move_id is null then coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.int_in_move_id = mal.int_move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) else coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "END) as grand_total from move_allocated_control mal where mal.move_id = sm.id),0) as allocated_qty, " \
            "(sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) - coalesce((select sum(mal.quantity - case when mal.int_move_id is null then coalesce((select sum( " \
            "(select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.int_in_move_id = mal.int_move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "else coalesce((select sum((select sum(fc.quantity) from fifo_control fc where fc.in_move_id = mal.move_id and fc.out_move_id = sm_out.id) " \
            ") from stock_move sm_out where sm_out.sale_line_id =  mal.so_line_id and sm_out.state = 'done'), 0) " \
            "END) as grand_total from move_allocated_control mal where mal.move_id = sm.id),0) as qty_onhand_free " \
            "from stock_move sm left join stock_location sld on sld.id = sm.location_dest_id left join stock_location sl on sl.id = sm.location_id " \
            "left join product_template pt on sm.product_id = pt.id " \
            "left join stock_inventory si on si.id = (select inventory_id from stock_inventory_move_rel where move_id = sm.id) left join res_company rc on si.company_id = rc.id " \
            "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
            "left join stock_move sm_out on fc.out_move_id = sm_out.id left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
            "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
            "where fc.in_move_id = sm.id),0)) > 0 and sm.picking_id is null " \
            + date_from_qry_si \
            + date_to_qry_si \
            + sl_qry + \
            pp_qry + \
            "order by sld.name, sld.id")
        physical_list = cr.dictfetchall()


        cr.execute(
            "select sm.product_id as product_id, sm.id as id, sp.date ::timestamp::date as sm_date "
            "from stock_move sm " \
            "left join stock_location sld on sld.id = sm.location_dest_id " \
            "left join stock_location sl on sl.id = sm.location_id " \
            "left join stock_picking sp on sm.picking_id = sp.id " \
            "left join res_company rc on sp.company_id = rc.id " \
            "left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
            "where sm.state = 'done' and sld.usage = 'internal' " \
            "and sp.type = 'internal' and sm.picking_id is not null " \
            + date_from_qry_int \
            + date_to_qry_int \
            + sl_qry + \
            pp_qry + \
            "order by sm.product_id ")
        internal_qry = cr.dictfetchall()
        for int_q in internal_qry:
            internal_move_control_ids = cost_price_fifo_obj.internal_get(cr, uid, int_q['id'])
            sm = stock_move_obj.browse(cr, uid, int_q['id'], context=None)
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
                    for int_temp2 in int_res:
                        int_qty_allocated = 0
                        int_move_allocated_control_ids = move_allocated_control_obj.browse(cr, uid, move_allocated_control_obj.search(cr, uid, [('move_id','=',int_q['id']), ('int_move_id','=',int_temp2['move_id'])]), context=context)
                        if int_move_allocated_control_ids:
                            for int_all_c in int_move_allocated_control_ids:
        #                                raise osv.except_osv(_('Debug !'), _(' \'%s\' \'%s\'!') %(all_c.id, all_c.rec_quantity))
                                int_qty_allocated += (int_all_c.quantity - int_all_c.rec_quantity)
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
                                x_unit_cost_price = int_temp2['unit_cost_price'] * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                                x_total_unit_cost_price = (int_qty_sisa * int_temp2['unit_cost_price']) * obj_currency_rate.browse(cr, uid, x_home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, x_rate_id, context=None).rate)
                            else:
                                x_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, int_temp2['unit_cost_price'], round=False)
                                x_total_unit_cost_price = currency_obj.compute(cr, uid, x_p_curr_id, x_ptype_src, (int_qty_sisa * int_temp2['unit_cost_price']), round=False)
                            x_unit_cost_price = product_product_obj.round_p(cr, uid, x_unit_cost_price, 'Purchase Price',)
                            x_total_unit_cost_price = product_product_obj.round_p(cr, uid, x_total_unit_cost_price, 'Purchase Price',)
                            allo_input = 0
                            if int_qty_allocated > 0:
                                if int_qty_sisa > int_qty_allocated:
                                    allo_input = int_qty_allocated
                                    int_qty_allocated = 0
                                else:
                                    allo_input = int_qty_sisa
                                    int_qty_allocated = int_qty_allocated - int_qty_sisa
                            internal_list.append({
                                'product_id' : sm.product_id.id,
                                'product_name' : sm.product_id.name,
                                'int_doc_no' : int_temp2['doc_no'],
                                'int_move_id' : int_temp2['move_id'],
                                'doc_ucp': int_temp2['unit_cost_price'],
                                'doc_total_ucp': round(int_temp2['unit_cost_price'] * int_qty_sisa,2),
                                'doc_curr_id' : int_temp2['doc_curr_id'],
                                'home_curr_id' : int_temp2['home_curr_id'],
                                'document_date': int_q['sm_date'],
                                'document_no' : sm.picking_id.name,
                                'move_id' : sm.id,
                                'location_id' : sm.location_dest_id.id,
                                'location_name' : sm.location_dest_id.name,
                                'product_qty' : int_qty_sisa,
                                'product_uom' : sm.product_id.uom_id.id,
                                'unit_cost_price' : x_unit_cost_price,
                                'total_cost_price' : round(x_total_unit_cost_price,2),
                                'qty_allocated' : allo_input,
                                'qty_onhand_free' : int_qty_sisa - allo_input,
                                })
        list_combine = incoming_list + physical_list + internal_list
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['move_id']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['document_date']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['location_id']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['location_name']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['product_id']) or []
        list_combine = list_combine and sorted(list_combine, key=lambda val_res: val_res['product_name']) or []

        if list_combine:
            grand_qty = 0
            grand_cost = 0
            prod_id = False
            loc_id = False
            prod_name = False
            loc_name = False
            total_qty = 0
            total_cost = 0
            for all_combine in list_combine:
                if all_combine['product_name'] != prod_name:
                    if total_qty > 0:
                        cr.execute('''SELECT sum(AA.product_qty) as sum_product_qty, aa.location_id FROM
                            (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
                            m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                            m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
                            CASE when pt.uom_id = m.product_uom
                            THEN
                                coalesce(sum(-m.product_qty)::decimal, 0.0)
                            ELSE
                                coalesce(sum(-m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                            FROM
                                stock_move m
                                LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                                LEFT JOIN product_product pp ON (m.product_id=pp.id)
                                LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                                LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                                LEFT JOIN product_uom u ON (m.product_uom=u.id)
                                LEFT JOIN stock_location l ON (m.location_id=l.id)
                            GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
                                m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                            UNION ALL
                            SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
                            m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                            m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
                            CASE when pt.uom_id = m.product_uom
                            THEN
                                coalesce(sum(m.product_qty)::decimal, 0.0)
                            ELSE
                                coalesce(sum(m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                            FROM
                                stock_move m
                                LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                                LEFT JOIN product_product pp ON (m.product_id=pp.id)
                                LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                                LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                                LEFT JOIN product_uom u ON (m.product_uom=u.id)
                                LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                            GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
                                m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                            ) AS AA
                                INNER JOIN stock_location sl on sl.id = AA.location_id
                                LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
                                LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
                                LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
                                LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
                                LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
                                LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
                                LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
                                WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = ''' + str(prod_id)
                                + ''' AND AA.location_id = ''' + str(loc_id)
                                + ''' GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                                HAVING sum(AA.product_qty) > 0''')
                        cr_vals = cr.fetchone()
                        product_qty = cr_vals and cr_vals[0] or 0
                        if product_qty == total_qty:
                            pr = 'Valid'
                        else:
                            pr = 'Non Valid'
                        header +=   str(product_qty) + ';;;Total For Location (' + str(loc_name) + ');' + \
                                    str(total_qty) + ';;' + \
                                    str(total_cost) + ';' + str(pr) + ';' \
                                    '\n'
                    if grand_cost > 0:
                        header +=   ';;;Total For ' + str(prod_name) + ';' + \
                                    str(grand_qty) + ';;' + \
                                    str(grand_cost) + ';' \
                                    '\n\n'

                    
                    prod_name = all_combine['product_name']
                    prod_id = all_combine['product_id']
                    header += prod_name + ' \n'
                    grand_qty = all_combine['product_qty']
                    grand_cost = all_combine['total_cost_price']
                    loc_id = all_combine['location_id']
                    loc_name = all_combine['location_name']
                    total_qty = all_combine['product_qty']
                    total_cost = all_combine['total_cost_price']
                    header += '     ' + all_combine['location_name'] + ' \n'
                    header +=   all_combine['int_doc_no'] + ';' + all_combine['document_no'] +  ';' + \
                                str(all_combine['document_date']) + ';' + str(all_combine['location_name']) +  ';' + \
                                str(all_combine['product_qty']) + ';' + str(all_combine['unit_cost_price']) +  ';' + \
                                str(all_combine['total_cost_price']) + ';' + \
                                '\n'
                else:
                    grand_qty += all_combine['product_qty']
                    grand_cost += all_combine['total_cost_price']
                    if all_combine['location_name'] != loc_name:
                        if total_qty > 0:
                            cr.execute('''SELECT sum(AA.product_qty) as sum_product_qty, aa.location_id FROM
                                (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
                                m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                                m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
                                CASE when pt.uom_id = m.product_uom
                                THEN
                                    coalesce(sum(-m.product_qty)::decimal, 0.0)
                                ELSE
                                    coalesce(sum(-m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                                FROM
                                    stock_move m
                                    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                                    LEFT JOIN product_product pp ON (m.product_id=pp.id)
                                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                                    LEFT JOIN product_uom u ON (m.product_uom=u.id)
                                    LEFT JOIN stock_location l ON (m.location_id=l.id)
                                GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
                                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                                UNION ALL
                                SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
                                m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                                m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
                                CASE when pt.uom_id = m.product_uom
                                THEN
                                    coalesce(sum(m.product_qty)::decimal, 0.0)
                                ELSE
                                    coalesce(sum(m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                                FROM
                                    stock_move m
                                    LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                                    LEFT JOIN product_product pp ON (m.product_id=pp.id)
                                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                                    LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                                    LEFT JOIN product_uom u ON (m.product_uom=u.id)
                                    LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                                GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
                                    m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                                ) AS AA
                                    INNER JOIN stock_location sl on sl.id = AA.location_id
                                    LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
                                    LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
                                    LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
                                    LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
                                    LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
                                    LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
                                    LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
                                    WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = ''' + str(prod_id)
                                    + ''' AND AA.location_id = ''' + str(loc_id)
                                    + ''' GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                                    HAVING sum(AA.product_qty) > 0''')
                            cr_vals = cr.fetchone()
                            product_qty = cr_vals and cr_vals[0] or 0
                            if product_qty == total_qty:
                                pr = 'Valid'
                            else:
                                pr = 'Non Valid'
                            header +=   str(product_qty) + ';;;Total For Location (' + str(loc_name) + ');' + \
                                        str(total_qty) + ';;' + \
                                        str(total_cost) + ';' + str(pr) + ';' \
                                        '\n'
                        loc_id = all_combine['location_id']
                        loc_name = all_combine['location_name']
                        total_qty = all_combine['product_qty']
                        total_cost = all_combine['total_cost_price']
                        header += '     ' + all_combine['location_name'] + ' \n'
                        header +=   all_combine['int_doc_no'] + ';' + all_combine['document_no'] +  ';' + \
                                    str(all_combine['document_date']) + ';' + str(all_combine['location_name']) +  ';' + \
                                    str(all_combine['product_qty']) + ';' + str(all_combine['unit_cost_price']) +  ';' + \
                                    str(all_combine['total_cost_price']) + ';' + \
                                    '\n'
                    else:
                        total_qty += all_combine['product_qty']
                        total_cost += all_combine['total_cost_price']
                        header +=   all_combine['int_doc_no'] + ';' + all_combine['document_no'] +  ';' + \
                                    str(all_combine['document_date']) + ';' + str(all_combine['location_name']) +  ';' + \
                                    str(all_combine['product_qty']) + ';' + str(all_combine['unit_cost_price']) +  ';' + \
                                    str(all_combine['total_cost_price']) + ';' + \
                                    '\n'
            if total_qty > 0:
                cr.execute('''SELECT sum(AA.product_qty) as sum_product_qty, aa.location_id FROM
                    (SELECT min(m.id) as id, m.date as date, m.address_id as partner_id, m.location_id as location_id,
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(-pt.standard_price * m.product_qty)::decimal, 0.0) as value,
                    CASE when pt.uom_id = m.product_uom
                    THEN
                        coalesce(sum(-m.product_qty)::decimal, 0.0)
                    ELSE
                        coalesce(sum(-m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                    FROM
                        stock_move m
                        LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                        LEFT JOIN product_product pp ON (m.product_id=pp.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                        LEFT JOIN product_uom u ON (m.product_uom=u.id)
                        LEFT JOIN stock_location l ON (m.location_id=l.id)
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id,  m.location_dest_id,
                        m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                    UNION ALL
                    SELECT -m.id as id, m.date as date, m.address_id as partner_id, m.location_dest_id as location_id,
                    m.product_id as product_id, pt.categ_id as product_categ_id, l.usage as location_type, m.company_id,
                    m.state as state, m.prodlot_id as prodlot_id, coalesce(sum(pt.standard_price * m.product_qty )::decimal, 0.0) as value,
                    CASE when pt.uom_id = m.product_uom
                    THEN
                        coalesce(sum(m.product_qty)::decimal, 0.0)
                    ELSE
                        coalesce(sum(m.product_qty * pu.factor/u.factor)::decimal, 0.0) END as product_qty
                    FROM
                        stock_move m
                        LEFT JOIN stock_picking p ON (m.picking_id=p.id)
                        LEFT JOIN product_product pp ON (m.product_id=pp.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                        LEFT JOIN product_uom pu ON (pt.uom_id=pu.id)
                        LEFT JOIN product_uom u ON (m.product_uom=u.id)
                        LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                    GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.address_id, m.location_id, m.location_dest_id,
                        m.prodlot_id, m.date, m.state, l.usage, m.company_id,pt.uom_id
                    ) AS AA
                        INNER JOIN stock_location sl on sl.id = AA.location_id
                        LEFT JOIN stock_location sl1 on sl1.id = sl.location_id
                        LEFT JOIN stock_location sl2 on sl2.id = sl1.location_id
                        LEFT JOIN stock_location sl3 on sl3.id = sl2.location_id
                        LEFT JOIN stock_location sl4 on sl4.id = sl3.location_id
                        LEFT JOIN stock_location sl5 on sl5.id = sl4.location_id
                        LEFT JOIN stock_location sl6 on sl6.id = sl5.location_id
                        LEFT JOIN stock_location sl7 on sl7.id = sl6.location_id
                        WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = ''' + str(prod_id)
                        + ''' AND AA.location_id = ''' + str(loc_id)
                        + ''' GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                        HAVING sum(AA.product_qty) > 0''')
                cr_vals = cr.fetchone()
                product_qty = cr_vals and cr_vals[0] or 0
                if product_qty == total_qty:
                    pr = 'Valid'
                else:
                    pr = 'Non Valid'
                header +=   str(product_qty) + ';;;Total For Location (' + str(loc_name) + ');' + \
                            str(total_qty) + ';;' + \
                            str(total_cost) + ';' + str(pr) + ';' \
                            '\n'
            if grand_cost > 0:
                header +=   ';;;Total For ' + str(prod_name) + ';' + \
                            str(grand_qty) + ';;' + \
                            str(grand_cost) + ';' \
                            '\n\n'


        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Inventory Valuation Report Checking.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','inventory_valuation_report_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Inventory Valuation Report Checking',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.inventory.valuation.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_inventory_valuation_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
