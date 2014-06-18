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
        val_sl = ['usage', '=', 'internal']
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
            result['pp_selection'] = '"' + pp_default_from_str + '" - "' + pp_default_to_str + '"'
            if data_found:
                pp_ids = product_product_obj.search(cr, uid, val_pb, order='name ASC')
        
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
                qry = self.cr.dictfetchone()
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


param_inventory_stock_aging_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
