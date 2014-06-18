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
            result['date_to'] = data['form']['date_to'] and data['form']['date_to'] + ' ' + '23:59:59'

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
        pp_qry = (pp_ids and ((len(pp_ids) == 1 and "AND pt.id = " + str(pp_ids[0]) + " ") or "AND pt.id IN " + str(tuple(pp_ids)) + " ")) or "AND pt.id IN (0) "
        
        sl_ids = form['location_ids'] or False
        sl_qry = (sl_ids and ((len(sl_ids) == 1 and "AND sl.id = " + str(sl_ids[0]) + " ") or "AND sl.id IN " + str(tuple(sl_ids)) + " ")) or "AND sl.id IN (0) "
        
        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')

        all_content_line = ''
        header = 'sep=;' + " \n"
        header += 'Inventory Valuation Report' + " \n"
        header += ('pp_selection' in form and 'Supplier Part No Filter Selection : ' + form['pp_selection'] + " \n") or ''
        header += ('date_showing' in form and 'Date : ' + str(form['date_showing']) + " \n") or ''
        header += ('sl_selection' in form and 'Location Filter Selection : ' + form['sl_selection'] + " \n") or ''
        header += 'Source Internal No;Document No;Date;Location;Qty On Hand(PCS);Unit Cost;Total Cost' + " \n"

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
