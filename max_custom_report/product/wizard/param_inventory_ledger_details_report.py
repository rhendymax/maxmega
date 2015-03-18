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
from datetime import datetime, timedelta
from tools import float_round, float_is_zero, float_compare

class param_inventory_ledger_details_report(osv.osv_memory):
    _name = 'param.inventory.ledger.details.report'
    _description = 'Param Inventory Ledger Details Report'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        #Product Selection
        'product_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Supplier Part No Filter Selection', required=True),
        'product_default_from':fields.many2one('product.product', 'Supplier Part No From', domain=[], required=False),
        'product_default_to':fields.many2one('product.product', 'Supplier Part No To', domain=[], required=False),
        'product_input_from': fields.char('Supplier Part No From', size=128),
        'product_input_to': fields.char('Supplier Part No To', size=128),
        'product_ids' :fields.many2many('product.product', 'report_ledger_detail_product_rel', 'report_id', 'product_id', 'Product', domain=[]),
        #Location Selection
        'sl_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Location Filter Selection', required=True),
        'sl_default_from':fields.many2one('stock.location', 'Location From', domain=[('usage','=','internal')], required=False),
        'sl_default_to':fields.many2one('stock.location', 'Location To', domain=[('usage','=','internal')], required=False),
        'sl_input_from': fields.char('Location From', size=128),
        'sl_input_to': fields.char('Location To', size=128),
        'sl_ids' :fields.many2many('stock.location', 'report_ledger_detail_sl_rel', 'report_id', 'sl_id', 'location', domain=[('usage','=','internal')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
    }

    _defaults = {
        'date_selection':'none_sel',
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
            'report_name': 'inventory.ledger.details.report_landscape',
            'datas': datas,
        }

    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_selection', 'date_from', 'date_to', \
                                                'product_selection', 'product_default_from', 'product_default_to', \
                                                'product_input_from', 'product_input_to', 'product_ids', \
                                                'sl_selection', 'sl_default_from', 'sl_default_to', \
                                                'sl_input_from', 'sl_input_to', 'sl_ids' \
                                                ], context=context)[0]
        for field in ['date_selection', 'date_from', 'date_to', \
                      'product_selection', 'product_default_from', 'product_default_to', \
                      'product_input_from', 'product_input_to', 'product_ids', \
                      'sl_selection', 'sl_default_from', 'sl_default_to', \
                      'sl_input_from', 'sl_input_to', 'sl_ids' \
                    ]:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)

        return self._get_tplines(cr, uid, ids, used_context, context=context)

    def _build_contexts(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        product_obj = self.pool.get('product.product')
        location_obj = self.pool.get('stock.location')
#         res_partner_obj = self.pool.get('res.partner')
#         account_journal_obj = self.pool.get('account.journal')
#         period_obj = self.pool.get('account.period')
#         account_fiscalyear_obj = self.pool.get('account.fiscalyear')
        result['date_selection'] = data['form']['date_selection']
        if data['form']['date_selection'] == 'none_sel':
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to']

        qry_prod = ''
        val_prod = []
        qry_loc = "usage = 'internal'"
        val_loc = [('usage','=','internal')]
#         qry_jour = ''
#         val_jour = []
        
        product_ids = False
        location_ids = False
#         journal_ids = False

        prod_default_from = data['form']['product_default_from'] or False
        prod_default_to = data['form']['product_default_to'] or False
        prod_input_from = data['form']['product_input_from'] or False
        prod_input_to = data['form']['product_input_to'] or False
        pp_default_from_str = pp_default_to_str = ''
        pp_input_from_str = pp_input_to_str= ''
        if data['form']['product_selection'] == 'all_vall':
            product_ids = product_obj.search(cr, uid, val_prod, order='name ASC')
        elif data['form']['product_selection'] == 'def':
            data_found = False
            if prod_default_from and product_obj.browse(cr, uid, prod_default_from) and \
                product_obj.browse(cr, uid, prod_default_from).name:
                pp_default_from_str = product_obj.browse(cr, uid, prod_default_from).name
                data_found = True
                val_prod.append(('name', '>=', product_obj.browse(cr, uid, prod_default_from).name))
            if prod_default_to and product_obj.browse(cr, uid, prod_default_to) and product_obj.browse(cr, uid, prod_default_to).name:
                pp_default_to_str = product_obj.browse(cr, uid, prod_default_to).name
                data_found = True
                val_prod.append(('name', '<=', product_obj.browse(cr, uid, prod_default_to).name))
            if data_found:
                product_ids = product_obj.search(cr, uid, val_prod, order='name ASC')
            result['pp_selection'] = '"' + pp_default_from_str + '" - "' + pp_default_to_str + '"'
        elif data['form']['product_selection'] == 'input':
            data_found = False
            if prod_input_from:
                pp_input_from_str = prod_input_from
                cr.execute("select name " \
                    "from product_template "\
                    "where " \
                    "name ilike '" + str(prod_input_from) + "%' " \
                    "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_prod.append(('name', '>=', qry['name']))
            if prod_input_to:
                pp_input_to_str = prod_input_to
                cr.execute("select name " \
                    "from product_template "\
                    "where " \
                    "name ilike '" + str(prod_input_to) + "%' " \
                    "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_prod.append(('name', '<=', qry['name']))

            result['pp_selection'] = '"' + pp_input_from_str + '" - "' + pp_input_to_str + '"'

            if data_found:
                product_ids = product_obj.search(cr, uid, val_prod, order='name ASC')
        elif data['form']['product_selection'] == 'selection':
            pp_ids = ''
            if data['form']['product_ids']:
                for pp in  product_obj.browse(cr, uid, data['form']['product_ids']):
                    pp_ids += '"' + str(pp.name) + '",'
                product_ids = data['form']['product_ids']
            result['pp_selection'] = '[' + pp_ids +']'

        result['product_ids'] = product_ids

        sl_default_from = data['form']['sl_default_from'] or False
        sl_default_to = data['form']['sl_default_to'] or False
        sl_input_from = data['form']['sl_input_from'] or False
        sl_input_to = data['form']['sl_input_to'] or False
        sl_default_from_str = sl_default_to_str = ''
        sl_input_from_str = sl_input_to_str= ''
        if data['form']['sl_selection'] == 'all_vall':
            location_ids = location_obj.search(cr, uid, val_loc, order='name ASC')
        elif data['form']['sl_selection'] == 'def':
            data_found = False
            if sl_default_from and location_obj.browse(cr, uid, sl_default_from) and \
                location_obj.browse(cr, uid, sl_default_from).name:
                sl_default_from_str = location_obj.browse(cr, uid, sl_default_from).name
                data_found = True
                val_loc.append(('name', '>=', location_obj.browse(cr, uid, sl_default_from).name))
            if sl_default_to and location_obj.browse(cr, uid, sl_default_to) and \
                location_obj.browse(cr, uid, sl_default_to).name:
                sl_default_to_str = location_obj.browse(cr, uid, sl_default_to).name
                data_found = True
                val_loc.append(('name', '<=', location_obj.browse(cr, uid, sl_default_to).name))
            result['sl_selection'] = '"' + sl_default_from_str + '" - "' + sl_default_to_str + '"'
            if data_found:
                location_ids = location_obj.search(cr, uid, val_loc, order='name ASC')
        elif data['form']['sl_selection'] == 'input':
            data_found = False
            if sl_input_from:
                sl_input_from_str = sl_input_from
                cr.execute("select name " \
                    "from stock_location " \
                    "where " + qry_loc + " and " \
                    "name ilike '" + str(sl_input_from) + "%' " \
                    "order by name limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_loc.append(('name', '>=', qry['name']))
            if sl_input_to:
                sl_input_to_str = sl_input_to
                cr.execute("select name " \
                    "from stock_location "\
                    "where " + qry_loc + " and " \
                    "name ilike '" + str(sl_input_from) + "%' " \
                    "order by name desc limit 1")
                qry = cr.dictfetchone()
                if qry:
                    data_found = True
                    val_loc.append(('name', '<=', qry['name']))

            result['sl_selection'] = '"' + sl_input_from_str + '" - "' + sl_input_to_str + '"'

            if data_found:
                location_ids = location_obj.search(cr, uid, val_loc, order='name ASC')
        elif data['form']['sl_selection'] == 'selection':
            sl_ids = ''
            if data['form']['sl_ids']:
                for sl in  location_obj.browse(cr, uid, data['form']['sl_ids']):
                    sl_ids += '"' + str(sl.name) + '",'
                location_ids = data['form']['sl_ids']
            result['sl_selection'] = '[' + sl_ids +']'

        result['location_ids'] = location_ids
        return result

    def _get_tplines(self, cr, uid, ids, data, context):
        form = data
        if not ids:
            ids = data['ids']
        if not ids:
            return []
        
        date_selection = form['date_selection']
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
#         print date_from
#         date_from_minus = datetime.strptime(date_from, '%Y-%m-%d') - timedelta(days=1)
        date_from_minus = date_from and datetime.strftime(datetime.strptime(date_from, '%Y-%m-%d') - timedelta(days=1),'%Y-%m-%d') or False
#         print date_from_minus
        count = 0
        results = []
        val_product = []
        val_location = []
        
#         date_selection = form['dt_selection'] or False
#         date_from = form['date_from'] or False
#         date_to = form['date_to'] or False

#         date_from_qry = date_from and "And sp.do_date >= '" + str(date_from) + "' " or " "
#         date_to_qry = date_to and "And sp.do_date <= '" + str(date_to) + "' " or " "
#         
        pp_ids = form['product_ids'] or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND sm.product_id = " + str(pp_ids[0]) + " ") or "AND sm.product_id IN " + str(tuple(pp_ids)) + " ")) or "AND sm.product_id IN (0) "
        
        sl_ids = form['location_ids'] or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sld.id = " + str(sl_ids[0]) + " ") or "AND sld.id IN " + str(tuple(sl_ids)) + " ")) or "AND sld.id IN (0) "
        
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        stock_move_obj = self.pool.get('stock.move')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        fifo_control_obj = self.pool.get('fifo.control')
        obj_currency_rate = self.pool.get('res.currency.rate')
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Valuation Report' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('date_showing' in form and 'Date : ' + str(form['date_showing']) + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += 'Date;Mod;Type;Voucher No;Cust/Supp Key;Source Location;Destination Location;Qty;Cost;Qty On Hand;Total Cost' + " \n"
        #check oustanding qty and balance
        #in
        product_combine_ids = {}
        if date_selection == 'date_sel':
            incoming_list = physical_list = internal_list = []
            #in
            cr.execute(
                "select sm.product_id, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) as oustanding_qty, " \
                "round(((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) * sm.price_unit * (" \
                "select rate from res_currency_rate where currency_id = rc.currency_id and name <= sp.do_date order by name desc limit 1) / " \
                "(select rate from res_currency_rate where currency_id = pr_p.currency_id and name <= sp.do_date order by name desc limit 1) " \
                "),2) as total_cost " \
                "from stock_move sm " \
                "left join stock_location sld on sld.id = sm.location_dest_id " \
                "left join stock_location sl on sl.id = sm.location_id " \
                "left join stock_picking sp on sm.picking_id = sp.id " \
                "left join res_company rc on sp.company_id = rc.id " \
                "left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
                "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) > 0 " \
                "and sp.type != 'internal' and sm.picking_id is not null " \
                "And sp.do_date  <= '" +str(date_from_minus) + "' "\
                + pp_qry + sl_qry + \
                "order by sm.product_id ")

            incoming_list = cr.dictfetchall()

            #Physical

            cr.execute(
                "select sm.product_id, (sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) as oustanding_qty, " \
                "round((sm.product_qty - coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) * sm.price_unit,2) as total_cost " \
                "from stock_move sm " \
                "left join stock_location sld on sld.id = sm.location_dest_id " \
                "left join stock_location sl on sl.id = sm.location_id " \
                "left join stock_inventory si on si.id = (select inventory_id from stock_inventory_move_rel where move_id = sm.id) " \
                "where sm.state = 'done' and sld.usage = 'internal' and (sm.product_qty- coalesce((select sum(fc.quantity) from fifo_control fc " \
                "left join stock_move sm_out on fc.out_move_id = sm_out.id " \
                "left join stock_picking sp_out on sp_out.id = sm_out.picking_id " \
                "left join stock_inventory si_out on si_out.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm_out.id) " \
                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                "and fc.in_move_id = sm.id),0)) > 0 " \
                "and sm.picking_id is null " \
                "And si.date ::timestamp::date <= '" +str(date_from_minus) + "' "\
                + pp_qry + sl_qry + \
                "order by sm.product_id ")
            physical_list = cr.dictfetchall()

            list_combine = incoming_list + physical_list
            
            for ls in list_combine:
                if ls['product_id'] in product_combine_ids:
                    ls_vals = product_combine_ids[ls['product_id']]
                    ls_vals['oustanding_qty'] += ls['oustanding_qty']
                    ls_vals['total_cost'] += ls['total_cost']
                    product_combine_ids[ls['product_id']] = ls_vals
                else:
                    product_combine_ids[ls['product_id']] = {'oustanding_qty' : ls['oustanding_qty'],
                                                             'total_cost' : ls['total_cost']
                                                             }

            #Internal
            cr.execute(
                "select sm.product_id as product_id, sm.id as id "
                "from stock_move sm " \
                "left join stock_location sld on sld.id = sm.location_dest_id " \
                "left join stock_location sl on sl.id = sm.location_id " \
                "left join stock_picking sp on sm.picking_id = sp.id " \
                "left join res_company rc on sp.company_id = rc.id " \
                "left join product_pricelist pr_p on pr_p.id = sp.pricelist_id " \
                "where sm.state = 'done' and sld.usage = 'internal' " \
                "and sp.type = 'internal' and sm.picking_id is not null " \
                "And sp.date ::timestamp::date  <= '" +str(date_from_minus) + "' "\
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
                                "where coalesce(si_out.date ::timestamp::date, coalesce(sp_out.do_date, sp_out.date ::timestamp::date)) <= '" +str(date_from_minus) + "' " \
                                "and fc.in_move_id = " + str(int_q['id']) + " and fc.int_in_move_id = " + str(int_temp2['move_id']))
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



                                if product_id in product_combine_ids:
                                    ls_vals = product_combine_ids[product_id]
                                    ls_vals['oustanding_qty'] += int_qty_sisa
                                    ls_vals['total_cost'] += x_total_unit_cost_price
                                    product_combine_ids[product_id] = ls_vals
                                else:
                                    product_combine_ids[product_id] = {'oustanding_qty' : int_qty_sisa,
                                                                             'total_cost' : x_total_unit_cost_price
                                                                             }

        if pp_ids:
            for product in product_product_obj.browse(cr, uid, pp_ids):
                res_temp = []
                balance_all = 0
                cost_all = 0
                if product_combine_ids:
                    if product.id in product_combine_ids:
                        ls_4_prod = product_combine_ids[product.id]
                        balance_all = ls_4_prod['oustanding_qty']
                        cost_all = ls_4_prod['total_cost'] 
#                 stock_move_ids = stock_move_obj.search(cr, uid, [('product_id','=',product.id),('state','=','done')])
                stock_move_qry = False
                if date_selection == 'date_sel':
                    cr.execute(
                        "select sm.id as sm_id from stock_move sm " \
                        "left join stock_picking sp on sp.id = sm.picking_id " \
                        "left join stock_inventory si on si.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm.id) " \
                        "where coalesce(si.date ::timestamp::date, coalesce(sp.do_date, sp.date ::timestamp::date)) >= '" +str(date_from) + "' " \
                        "and coalesce(si.date ::timestamp::date, coalesce(sp.do_date, sp.date ::timestamp::date)) <= '" +str(date_to) + "' " \
                        "and sm.product_id = " + str(product.id) + " and sm.state='done' order by coalesce(si.date ::timestamp::date, coalesce(sp.do_date, sp.date ::timestamp::date)), sm.id")
                    stock_move_qry = cr.dictfetchall()
                else:
                    cr.execute(
                        "select sm.id as sm_id from stock_move sm " \
                        "left join stock_picking sp on sp.id = sm.picking_id " \
                        "left join stock_inventory si on si.id = (select inventory_id from stock_inventory_move_rel simr where simr.move_id = sm.id) " \
                        "where sm.product_id = " + str(product.id) + " and sm.state='done' order by coalesce(si.date ::timestamp::date, coalesce(sp.do_date, sp.date ::timestamp::date)), sm.id")
                    stock_move_qry = cr.dictfetchall()

                if balance_all == 0 and not (stock_move_qry):
                    continue

                header += product.name +';;;;;;;;Opening Balance (Qty / Cost);' + str(balance_all) + ';' + str(cost_all) + ' \n'
                if stock_move_qry:
                    for sm_q in stock_move_qry:
                        partner_ref = ''
                        unit_cost_price = 0.00
                        total_unit_cost_price = 0.00
                        sm = stock_move_obj.browse(cr, uid, sm_q['sm_id'], context=None)
                        if sm.picking_id:
                            document_date = sm.picking_id.do_date or sm.picking_id.date_done or False
                            voucher_no = sm.picking_id.name
                        else:
                            for si in sm.stock_inventory_ids:
                                voucher_no = si.name
                                document_date =  si.date_done or False
                        qty = uom_obj._compute_qty(cr, uid, sm.product_uom.id, sm.product_qty, sm.product_id.uom_id.id)
                        if sm.picking_id:
                            key = sm.picking_id and sm.picking_id.partner_id and sm.picking_id.partner_id.ref or False
                            if sm.picking_id.type != "internal":
                                mod = "PO"
                                type = "GR"
                                rate_id = False
                                p_curr_id = sm.picking_id.pricelist_id.currency_id.id
                                ptype_src = self.pool.get('res.company').browse(cr, uid, sm.picking_id.company_id.id, context=None).currency_id.id
                                if p_curr_id != ptype_src:
                                    tgl = sm.picking_id.do_date or (sm.picking_id.date_done and datetime.strptime(sm.picking_id.date_done, '%Y-%m-%d %H:%M:%S').date()) or False
                                    rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', p_curr_id),
                                                                                  ('name','<=', tgl)
                                                                                  ])
                                    if rate_ids:
                                        rate_id = rate_ids[0]
                                    else:
                                        raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                    home_rate_ids = obj_currency_rate.search(cr, uid, [('currency_id','=', ptype_src),
                                                                                  ('name','<=', tgl)
                                                                                  ])
                                    if home_rate_ids:
                                        home_rate_id = home_rate_ids[0]
                                    else:
                                        raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
    
                                if rate_id:
                                    unit_cost_price = sm.price_unit * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                                    total_unit_cost_price = (qty * sm.price_unit) * obj_currency_rate.browse(cr, uid, home_rate_id, context=None).rate/ (obj_currency_rate.browse(cr, uid, rate_id, context=None).rate)
                                else:
                                    unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, sm.price_unit, round=False)
                                    total_unit_cost_price = currency_obj.compute(cr, uid, p_curr_id, ptype_src, (qty * sm.price_unit), round=False)
                                unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, unit_cost_price, sm.product_uom.id)
                                unit_cost_price = product_product_obj.round_p(cr, uid, unit_cost_price, 'Purchase Price',)
                                total_unit_cost_price = uom_obj._compute_price(cr, uid, sm.product_id.uom_id.id, total_unit_cost_price, sm.product_uom.id)
                                total_unit_cost_price = product_product_obj.round_p(cr, uid, total_unit_cost_price, 'Purchase Price',)
                                if sm.picking_id.type == 'out':
                                    mod = "SO"
                                    type = "DO"
                            else:
                                mod = "IC"
                                type = "TF"
                        else:
                            key = ''
                            mod = "IC"
                            unit_cost_price = sm.price_unit
                            total_unit_cost_price = unit_cost_price * qty
                            if sm.location_dest_usage == 'internal':
                                type = "PI-IN"
                            else:
                                type = "PI-OUT"
                        res_temp.append({
                            'inv_key' : product.name or '',
                            'voucher_no' : voucher_no,
                            'date' : document_date,
                            'mod' : mod or '',
                            'type' : type or '',
                            'key' : key or '',
                            'qty' : qty or 0.00,
                            'total_unit_cost_price' : total_unit_cost_price or 0.00,
                            'cost': unit_cost_price or 0.00,
                            'sm_id' : sm.id,
                            'source_location': sm.location_id.name or '',
                            'dest_location': sm.location_dest_id.name or '',
                             }
                            )
                if res_temp:
                    res_temp = res_temp and sorted(res_temp, key=lambda val_res: val_res['date']) or []
                    for all in res_temp:
                        cost_output = 0
                        qty_output = all['qty']
                        if all['mod'] == 'SO' or (all['mod'] == 'IC' and all['type'] == 'PI-OUT'):
                            balance_all -= all['qty']
                            fifo_control_ids = fifo_control_obj.browse(cr, uid, fifo_control_obj.search(cr, uid, [('out_move_id','=',all['sm_id'])]), context=None)
                            total_unit_cost_price_1 = 0.00
                            if fifo_control_ids:
                                for val in fifo_control_ids:
                                    qty_xx = uom_obj._compute_qty(cr, uid, val.in_move_id.product_uom.id, val.quantity, val.in_move_id.product_id.uom_id.id)
                                    if val.in_move_id.picking_id:

                                        sm_id = val.int_in_move_id or val.in_move_id
                                        if sm_id.picking_id:
                                            rate_id_xx = False
                                            p_curr_id_xx = sm_id.picking_id.pricelist_id.currency_id.id
                                            ptype_src_xx = self.pool.get('res.company').browse(cr, uid, sm_id.picking_id.company_id.id, context=None).currency_id.id
                                            if p_curr_id_xx != ptype_src_xx:
                                                tgl_xx = sm_id.picking_id.do_date
                                                tgl_xx = datetime.strptime(tgl_xx, '%Y-%m-%d').date()
                                                rate_ids_xx = obj_currency_rate.search(cr, uid, [('currency_id','=', p_curr_id_xx),
                                                                                              ('name','<=', tgl_xx)
                                                                                              ])
                                                if rate_ids_xx:
                                                    rate_id_xx = rate_ids_xx[0]
                                                    rate = obj_currency_rate.browse(cr, uid, rate_id_xx, context=None).rate
                                                else:
                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in currency'))
                                                home_rate_ids_xx = obj_currency_rate.search(cr, uid, [('currency_id','=', ptype_src_xx),
                                                                                              ('name','<=', tgl_xx)
                                                                                              ])
                                                if home_rate_ids_xx:
                                                    home_rate_id_xx = home_rate_ids_xx[0]
                                                    home_rate = obj_currency_rate.browse(cr, uid, home_rate_id_xx, context=None).rate
                                                else:
                                                    raise osv.except_osv(_('Message Error!'), _('no rate found in home currency'))
                
                                            if rate_id_xx:
                                                unit_cost_price_xx = sm_id.price_unit * home_rate / rate
                                                total_unit_cost_price_xx = (qty_xx * sm_id.price_unit) * home_rate/ rate
                                            else:
                                                unit_cost_price_xx = currency_obj.compute(cr, uid, p_curr_id_xx, ptype_src_xx, sm_id.price_unit, round=False)
                                                total_unit_cost_price_xx = currency_obj.compute(cr, uid, p_curr_id_xx, ptype_src_xx, (qty_xx * sm_id.price_unit), round=False)
                                            unit_cost_price_xx = uom_obj._compute_price(cr, uid, sm_id.product_id.uom_id.id, unit_cost_price_xx, sm_id.product_uom.id)
                                            unit_cost_price_xx = product_product_obj.round_p(cr, uid, unit_cost_price_xx, 'Purchase Price',)
                                            total_unit_cost_price_xx = uom_obj._compute_price(cr, uid, sm_id.product_id.uom_id.id, total_unit_cost_price_xx, sm_id.product_uom.id)
                                            total_unit_cost_price_xx = product_product_obj.round_p(cr, uid, total_unit_cost_price_xx, 'Purchase Price',)
                                            total_unit_cost_price_1 += total_unit_cost_price_xx
                                        else:
                                            total_unit_cost_price_1 += (sm_id.price_unit * qty_xx)
                                    else:
                                        total_unit_cost_price_1 += (val.in_move_id.price_unit * qty_xx)
                            cost_output = -1 * total_unit_cost_price_1
                            qty_output = -1 * all['qty']
                            cost_all = cost_all - total_unit_cost_price_1
                        elif all['mod'] == 'PO' or (all['mod'] == 'IC' and all['type'] == 'PI-IN'):
                            balance_all += all['qty']
                            cost_all += all['total_unit_cost_price']
                            cost_output = all['total_unit_cost_price']
                        
                        if float_is_zero(cost_all, precision_digits=5):
                            cost_all = 0.00000
                        header += str(all['date']) + ';' + str(all['mod']) + ';' + str(all['type']) + ';' + str(all['voucher_no']) + ';' + \
                        str(all['key']) + ';' + str(all['source_location']) + ';' + \
                        str(all['dest_location']) + ';' + str(qty_output) + ';' + \
                        str(cost_output) + ';' + str(balance_all) + ';' + str(cost_all) + ' \n'
                header += ';;;;;;;;Total for '+ product.name + ': ;' + str(balance_all) + ';' + str(cost_all) + ' \n\n'
#                 print product.name + '--' + str(balance_all) + '--' +str(cost_all)

        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Inventory Ledger Details Report.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','inventory_ledger_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Inventory Ledger Details Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.inventory.ledger.details.report',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }
        
param_inventory_ledger_details_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
