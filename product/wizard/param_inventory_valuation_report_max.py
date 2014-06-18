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

class param_inventory_valuation_report_max(osv.osv_memory):
    _name = 'param.inventory.valuation.report.max'
    _description = 'Param Inventory Valuation Report'
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
        'product_ids' :fields.many2many('product.product', 'report_inv_valmax_product_rel', 'report_id', 'product_id', 'Product', domain=[]),
        #Location Selection
        'sl_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Location Filter Selection', required=True),
        'sl_default_from':fields.many2one('stock.location', 'Location From', domain=[('usage', '=', 'internal')], required=False),
        'sl_default_to':fields.many2one('stock.location', 'Location To', domain=[('usage', '=', 'internal')], required=False),
        'sl_input_from': fields.char('Location From', size=128),
        'sl_input_to': fields.char('Location To', size=128),
        'sl_ids' :fields.many2many('stock.location', 'report_inv_valmax_sl_rel', 'report_id', 'sl_id', 'Location', domain=[('usage', '=', 'internal')]),
        'data': fields.binary('Exported CSV', readonly=True),
        'filename': fields.char('File Name',size=64),
        
#        'date_from': fields.date("From Date", required=True),
#        'date_to': fields.date("To Date", required=True),
#        'product_from':fields.many2one('product.product', 'Supplier Part No From', required=False),
#        'product_to':fields.many2one('product.product', 'Supplier Part No To', required=False),
#        'location_from':fields.many2one('stock.location', 'Location From', required=False),
#        'location_to':fields.many2one('stock.location', 'Location To', required=False),
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
        datas['model'] = 'param.inventory.valuation.report.max'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'inventory.valuation.report.max_landscape',
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
                                                'sl_default_from','sl_default_to','sl_input_from','sl_input_to','sl_ids'], context=context)[0]
                                                
        for field in ['date_selection', 'date_from', 'date_to','product_selection','product_default_from','product_default_to', \
                      'product_input_from','product_input_to','product_ids','sl_selection','sl_default_from','sl_default_to', \
                      'sl_input_from','sl_input_to','sl_ids']:
            
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

        if data['form']['date_selection'] == 'none_sel':
            result['dt_selection'] = 'none_sel'
            result['date_from'] = False
            result['date_to'] = False
        else:
            result['dt_selection'] = 'date'
            result['date_selection'] = 'Date'
            result['date_showing'] = '"' + data['form']['date_from'] + '" - "' + data['form']['date_to'] + '"'
            result['date_from'] = data['form']['date_from']
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

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
        date_selection = form['dt_selection'] or False
        date_from = form['date_from'] or False
        date_to = form['date_to'] or False
        
        pp_ids = form['pp_ids'] or False
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND pt.id = " + str(pp_ids[0]) + " ") or "AND pt.id IN " + str(tuple(pp_ids)) + " ")) or "AND pt.id IN (0) "
        
        sl_ids = form['sl_ids'] or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sl.id = " + str(sl_ids[0]) + " ") or "AND sl.id IN " + str(tuple(sl_ids)) + " ")) or "AND sl.id IN (0) "
        
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        
        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Valuation Report' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('date_selection' in form and 'Date : ' + str(form['date_showing']) + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += 'Source Internal No;Document No;Date;Location;Qty On Hand(PCS);Unit Cost;Total Cost' + " \n"
        
        for location_id in sl_ids:
            sl = stock_location_obj.browse(cr, uid, location_id)
            sl_checking = stock_location_obj.search(cr, uid, [('location_id','=',sl.id)])
            if sl_checking:
                continue
            res = {}

            vals_ids = []
            total_cost = 0
            total_qty = 0
            for product_id in product_product_obj.browse(cr, uid, pp_ids):
                cpf_loc = cost_price_fifo_obj.stock_move_get(cr, uid, product_id.id, location_id=location_id)
                if cpf_loc:
                    vals_ids2 = []
                    total_prod_cost = 0.00
                    total_prod_qty = 0.00
                    for res_f1 in cpf_loc:
                        if date_selection == 'date':
                            document_date =  res_f1['document_date'] or  False
                            if document_date \
                                and document_date >= date_from and document_date <= date_to:
                                vals_ids2.append({
                                    'int_no' : res_f1['int_doc_no'] or '',
                                    'doc_no' : res_f1['document_no'] or '',
                                    'date' : res_f1['document_date'] or False,
                                    'location' : sl.name or '',
                                    'qty_on_hand' : res_f1['product_qty'] or 0.00,
                                    'unit_cost' : res_f1['unit_cost_price'] or 0.00,
                                    'total_cost' : res_f1['total_cost_price'] or 0.00,
                                    })
                                total_prod_cost += (res_f1['total_cost_price'] or 0.00)
                                total_prod_qty += (res_f1['product_qty'] or 0.00)
                                total_cost += (res_f1['total_cost_price'] or 0.00)
                                total_qty += (res_f1['product_qty'] or 0.00)
                        else:
                            vals_ids2.append({
                                    'int_no' : res_f1['int_doc_no'] or '',
                                    'doc_no' : res_f1['document_no'] or '',
                                    'date' : res_f1['document_date'] or False,
                                    'location' : sl.name or '',
                                    'qty_on_hand' : res_f1['product_qty'] or 0.00,
                                    'unit_cost' : res_f1['unit_cost_price'] or 0.00,
                                    'total_cost' : res_f1['total_cost_price'] or 0.00,
                                    })
                            total_prod_cost += res_f1['total_cost_price'] or 0.00
                            total_prod_qty += res_f1['product_qty'] or 0.00
                            total_cost += (res_f1['total_cost_price'] or 0.00)
                            total_qty += (res_f1['product_qty'] or 0.00)
    #                            total_cost += (res_f1['total_cost_price'] or 0.00)
    #                            total_qty += (res_f1['product_qty'] or 0.00)
                    vals_ids.append({
                    'prod_name' : product_id.name,
                    'lines' : vals_ids2,
                    'loc_cost' : total_prod_cost,
                    'loc_qty' : total_prod_qty,
                    })
            if not vals_ids:
                continue
            res['total_cost'] = total_cost
            res['total_qty'] = total_qty
            res['pro_lines'] = vals_ids
            res['loc_name'] = sl.name or ''
            results.append(res)
            
        _total_cost = _total_qty = 0
        for rs in results:
            header += str(rs['loc_name']) + ' \n'
            for rs1 in rs['pro_lines']:
                header += str(rs1['prod_name']) + ' \n'
                for rs2 in rs1['lines']:
                    _total_cost += rs2['total_cost'] or 0.00
                    _total_qty += rs2['qty_on_hand'] or 0.00
                    header += str(rs2['int_no']) + ';' + str(rs2['doc_no']) + ';' + str(rs2['date']) + ';' + str(rs2['location']) + ';' \
                    + str(float_round(rs2['qty_on_hand'],0)) + ';' + str(float_round(rs2['unit_cost'],5)) + ';' + str(float_round(rs2['total_cost'],2)) + ' \n'
                    
                header += 'Total Of ' + str(rs1['prod_name']) + ';;;;' + str(rs1['loc_qty']) + ';' + ';' + str(rs1['loc_cost']) + ' \n'
            header += 'Total Of : ' + str(rs['loc_name']) + ';;;;' + str(float_round(rs['total_qty'],0)) + ';' + ';' + str(float_round(rs['total_cost'],2)) + ' \n \n'
        header += 'Report Total' + ';;;;' + str(float_round(_total_qty,0)) + ';;' + str(float_round(_total_cost,2)) + ' \n'
        
        all_content_line += header
        all_content_line += ' \n'
        all_content_line += 'End of Report'
        csv_content = ''

        filename = 'Inventory Valuation Report Checking.csv'
        out = base64.encodestring(all_content_line)
        self.write(cr, uid, ids,{'data':out, 'filename':filename})
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','inventory_valuation_report_max_result_csv_view')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
                'name':'Inventory Valuation Report',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'param.inventory.valuation.report.max',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'res_id':ids[0],
                }

param_inventory_valuation_report_max()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
