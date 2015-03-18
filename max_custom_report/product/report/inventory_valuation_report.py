# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
# Copyright (c) 2006-2010 OpenERP S.A
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from datetime import datetime, timedelta
from osv import osv, fields
from tools.translate import _
from report import report_sxw
import locale
locale.setlocale(locale.LC_ALL, '')

class inventory_valuation_report(report_sxw.rml_parse):
    _name = 'inventory.valuation.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.product_from = data['form']['product_from'] and data['form']['product_from'][0] or False
        self.product_to = data['form']['product_to'] and data['form']['product_to'][0] or False
        self.location_from = data['form']['location_from'] and data['form']['location_from'][0] or False
        self.location_to = data['form']['location_to'] and data['form']['location_to'][0] or False
        self.valid = data['form']['valid'] or False
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(inventory_valuation_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(inventory_valuation_report, self).__init__(cr, uid, name, context=context)
        self.total_cost = 0.00
        self.total_qty = 0.00
#      
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'total_cost' : self._total_cost,
            'total_qty' : self._total_qty,
            'product_from': self._get_product_from,
            'product_to': self._get_product_to,
            'location_from': self._get_location_from,
            'location_to': self._get_location_to,
            })
      

    def _get_product_from(self):
           return self.product_from and self.pool.get('product.product').browse(self.cr, self.uid, self.product_from).name or False
    
    def _get_product_to(self):
        return self.product_to and self.pool.get('product.product').browse(self.cr, self.uid, self.product_to).name or False
    
    def _get_location_from(self):
        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_from).name or False
    
    def _get_location_to(self):
        return self.location_to and self.pool.get('stock.location').browse(self.cr, self.uid, self.location_to).nameor or False
#        
    def _get_lines(self):
        count = 0
        results = []
        val_product = []
        val_location = []
        valid_x = self.valid
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        product_from = self.product_from
        product_to = self.product_to
        location_from = self.location_from
        location_to = self.location_to
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(code_from, code_to))

        product_product_obj = self.pool.get('product.product')
        cost_price_fifo_obj = self.pool.get('cost.price.fifo')
        stock_location_obj = self.pool.get('stock.location')
        if product_from and product_product_obj.browse(self.cr, self.uid, product_from) and product_product_obj.browse(self.cr, self.uid, product_from).name:
            val_product.append(('name', '>=', product_product_obj.browse(self.cr, self.uid, product_from).name))
        if product_to and product_product_obj.browse(self.cr, self.uid, product_to) and product_product_obj.browse(self.cr, self.uid, product_to).name:
            val_product.append(('name', '<=', product_product_obj.browse(self.cr, self.uid, product_to).name))
        if location_from and stock_location_obj.browse(self.cr, self.uid, location_from) and stock_location_obj.browse(self.cr, self.uid, location_from).name:
            val_location.append(('name', '>=', stock_location_obj.browse(self.cr, self.uid, location_from).name))
        if location_to and stock_location_obj.browse(self.cr, self.uid, location_to) and stock_location_obj.browse(self.cr, self.uid, location_to).name:
            val_location.append(('name', '<=', stock_location_obj.browse(self.cr, self.uid, location_to).name))

#        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
#            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
#        if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
#            val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_from).name))
#        if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
#            val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_to).name))
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(vals, code_to))

#        part_ids = res_partner_obj.search(self.cr, self.uid, val_part)
        product_ids = product_product_obj.search(self.cr, self.uid, val_product,order='name')
        location_ids = stock_location_obj.search(self.cr, self.uid, val_location)
#        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)
        for product_id in product_ids:
            pp = product_product_obj.browse(self.cr, self.uid, product_id)
            cpf_prod = cost_price_fifo_obj.stock_move_get(self.cr, self.uid, product_id)
#            raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(cost_price_fifo_result, pp.name))
            if cpf_prod:
                res = {}
                res['product_name'] = pp.name or ''
                vals_ids = []
                total_cost = 0
                total_qty = 0
                for loc in stock_location_obj.browse(self.cr, self.uid, location_ids):
                    cpf_loc = cost_price_fifo_obj.stock_move_get(self.cr, self.uid, product_id, location_id=loc.id)
                    #print cpf_loc
                    if cpf_loc:
                        vals_ids2 = []
                        total_loc_cost = 0
                        total_loc_qty = 0
                        for res_f1 in cpf_loc:
                            document_date =  res_f1['document_date'] or  False
                            if document_date \
                                and document_date >= date_from and document_date <= date_to \
                                and res_f1['location_id'] in location_ids:
                                location = stock_location_obj.browse(self.cr, self.uid, res_f1['location_id'])
        #                        res = {
        #                            'desc' : '',
        #                            'location' : location and location.name or '',
        #                            'qty_on_hand' : res_f1['product_qty'] or 0.00,
        #                            'unit_cost' : res_f1['unit_cost_price'] or 0.00,
        #                            'total_cost' : res_f1['total_cost_price'] or 0.00,
        #                        }
                                vals_ids2.append({
                                    'int_no' : res_f1['int_doc_no'] or '',
                                    'doc_no' : res_f1['document_no'] or '',
                                    'date' : res_f1['document_date'] or False,
                                    'location' : location and location.name or '',
                                    'qty_on_hand' : res_f1['product_qty'] or 0.00,
                                    'unit_cost' : res_f1['unit_cost_price'] or 0.00,
                                    'total_cost' : res_f1['total_cost_price'] or 0.00,
                                    })
                                total_loc_cost += (res_f1['total_cost_price'] or 0.00)
                                total_loc_qty += (res_f1['product_qty'] or 0.00)
                                total_qty += (res_f1['product_qty'] or 0.00)
                                total_cost += (res_f1['total_cost_price'] or 0.00)
                                self.total_cost += (res_f1['total_cost_price'] or 0.00)
                                self.total_qty += (res_f1['product_qty'] or 0.00)
                        self.cr.execute('''SELECT sum(AA.product_qty) as sum_product_qty, aa.location_id FROM
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
                                WHERE sl.usage = 'internal' AND AA.state in ('done') AND AA.product_id = ''' + str(pp.id)
                                + ''' AND AA.location_id = ''' + str(loc.id)
                                + ''' GROUP BY ARRAY_TO_STRING(ARRAY[sl7.name, sl6.name, sl5.name, sl4.name, sl3.name,sl2.name, sl1.name, sl.name], '/') , aa.location_id
                                HAVING sum(AA.product_qty) > 0''')
                        cr_vals = self.cr.fetchone()
#                        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(cr_vals[0], pp.name))
                        product_qty = cr_vals and cr_vals[0] or 0
                        valid = "Valid"
                        if product_qty != total_loc_qty:
                            valid = "Non Valid"
                        if valid_x == 'valid':
                            if valid == 'Valid':
                                vals_ids.append({
                                'loc_name' : loc.name,
                                'loc_qty_real': product_qty,
                                'loc_cost' : total_loc_cost,
                                'loc_qty' : total_loc_qty,
                                'lines' : vals_ids2,
                                'valid' : str(valid),
                                })
                        elif valid_x == 'non_valid':
                            if valid == "Non Valid":
                                count += 1
                                vals_ids.append({
                                'loc_name' : loc.name,
                                'loc_qty_real': product_qty,
                                'loc_cost' : total_loc_cost,
                                'loc_qty' : total_loc_qty,
                                'lines' : vals_ids2,
                                'valid' : str(valid),
                                })
                        else:
                            vals_ids.append({
                            'loc_name' : loc.name,
                            'loc_qty_real': product_qty,
                            'loc_cost' : total_loc_cost,
                            'loc_qty' : total_loc_qty,
                            'lines' : vals_ids2,
                            'valid' : str(valid),
                            })
                    
#                    document_date =  res_f1['document_date'] or  False
#                    if document_date \
#                        and document_date >= date_from and document_date <= date_to \
#                        and res_f1['location_id'] in location_ids:
#                        location = stock_location_obj.browse(self.cr, self.uid, res_f1['location_id'])
##                        res = {
##                            'desc' : '',
##                            'location' : location and location.name or '',
##                            'qty_on_hand' : res_f1['product_qty'] or 0.00,
##                            'unit_cost' : res_f1['unit_cost_price'] or 0.00,
##                            'total_cost' : res_f1['total_cost_price'] or 0.00,
##                        }
#                        vals_ids.append({
#                            'desc' : '',
#                            'location' : location and location.name or '',
#                            'qty_on_hand' : res_f1['product_qty'] or 0.00,
#                            'unit_cost' : res_f1['unit_cost_price'] or 0.00,
#                            'total_cost' : res_f1['total_cost_price'] or 0.00,
#                            })
#                        self.total_cost += (res_f1['total_cost_price'] or 0.00)
#                        total_cost += (res_f1['total_cost_price'] or 0.00)
#                        
#                        self.total_qty += (res_f1['product_qty'] or 0.00)
#                        total_qty += (res_f1['product_qty'] or 0.00)
                res['total_cost'] = total_cost
                res['total_qty'] = total_qty
                res['pro_lines'] = vals_ids
                results.append(res)
        #raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(count, 'xxx'))
        return results 

    def _total_cost(self):
        return self.total_cost
    
    def _total_qty(self):
        return self.total_qty
#        for pur in purcs:
#            date_po =  pur.order_id and pur.order_id.date_order or False
#            state = pur.order_id and pur.order_id.state or ''
#            partner_id = pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.id or False
#            po_id = pur.order_id and pur.order_id.id or False
#            if date_po and state == 'approved' \
#                and date_po >= date_from and date_po <= date_to \
#                and pur.oustanding_qty > 0 and partner_id in part_ids \
#                and po_id in po_ids:
#                partner_name = ''
#
#                if pur.order_id:
#                    partner_name = pur.order_id.partner_id and pur.order_id.partner_id.name or ''
#                if partner_name: partner_name = partner_name.replace('&','&amp;')
#                    
#                res = {
#                    's_name' : pur.order_id and partner_name or '',
#                    's_ref' : pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.ref or '',
#                    'order_name' : pur.order_id and pur.order_id.name or '',
#                    'part_name' : pur.product_id and pur.product_id.name or '',
#                    'etd' : pur.estimated_time_departure or False,
#                    'order_qty' : pur.product_qty or '',
#                    'unit_price': pur.price_unit,
#                    'oustanding': pur.oustanding_qty or '',
#                }
#                results.append(res)
#                res = {}
        
report_sxw.report_sxw('report.inventory.valuation.report_landscape', 'product.product',
    'addons/max_custom_report/product/report/inventory_valuation_report.rml', parser=inventory_valuation_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
