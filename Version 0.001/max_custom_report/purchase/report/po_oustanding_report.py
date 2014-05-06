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

class po_oustanding_report(report_sxw.rml_parse):
    _name = 'po.oustanding.report'

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        res = {}
        self.date_from = data['form']['date_from']
        self.date_to = data['form']['date_to']
        self.partner_code_from = data['form']['partner_code_from'] and data['form']['partner_code_from'][0] or False
        self.partner_code_to = data['form']['partner_code_to'] and data['form']['partner_code_to'][0] or False
        self.po_from = data['form']['po_from'] and data['form']['po_from'][0] or False
        self.po_to = data['form']['po_to'] and data['form']['po_to'][0] or False

#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(data['form']['partner_code_from'][0], data['form']['partner_code_from'][0]))
        return super(po_oustanding_report, self).set_context(objects, data, new_ids, report_type=report_type)

    def __init__(self, cr, uid, name, context=None):
        super(po_oustanding_report, self).__init__(cr, uid, name, context=context)
        
        self.oustanding = 0.00
        
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines': self._get_lines,
            'get_code_from': self._get_code_from,
            'get_code_to': self._get_code_to,
            'get_po_from': self._get_po_from,
            'get_po_to': self._get_po_to,
            'total_oustanding' : self._total_oustanding,
            })
    
    def _get_code_from(self):
        return self.partner_code_from and self.pool.get('res.partner').browse(self.cr, self.uid,self.partner_code_from).ref or False
    
    def _get_code_to(self):
        return self.partner_code_to and self.pool.get('res.partner').browse(self.cr, self.uid, self.partner_code_to).ref or False
    
    def _get_po_from(self):
        return self.po_from and self.pool.get('purchase.order').browse(self.cr, self.uid, self.po_from).name or False
    
    def _get_po_to(self):
        return self.po_to and self.pool.get('purchase.order').browse(self.cr, self.uid, self.po_to).name or False
###        

    def _get_lines(self):
        results = []
        val_part = []
        val_po = []
        date_from = self.date_from
        date_to =  self.date_to + ' ' + '23:59:59'
        code_from = self.partner_code_from
        code_to = self.partner_code_to
        po_from = self.po_from
        po_to = self.po_to
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(code_from, code_to))

        purchase_order_line_obj = self.pool.get('purchase.order.line')
        purchase_order_obj = self.pool.get('purchase.order')
        res_partner_obj = self.pool.get('res.partner')
        
        if code_from and res_partner_obj.browse(self.cr, self.uid, code_from) and res_partner_obj.browse(self.cr, self.uid, code_from).ref:
            val_part.append(('ref', '>=', res_partner_obj.browse(self.cr, self.uid, code_from).ref))
        if code_to and res_partner_obj.browse(self.cr, self.uid, code_to) and res_partner_obj.browse(self.cr, self.uid, code_to).ref:
            val_part.append(('ref', '<=', res_partner_obj.browse(self.cr, self.uid, code_to).ref))
        if po_from and purchase_order_obj.browse(self.cr, self.uid, po_from) and purchase_order_obj.browse(self.cr, self.uid, po_from).name:
            val_po.append(('name', '>=', purchase_order_obj.browse(self.cr, self.uid, po_from).name))
        if po_to and purchase_order_obj.browse(self.cr, self.uid, po_to) and purchase_order_obj.browse(self.cr, self.uid, po_to).name:
            val_po.append(('name', '<=', purchase_order_obj.browse(self.cr, self.uid, po_to).name))
#        raise osv.except_osv(_('Invalid action !'), _(' \'%s\' \'%s\'!') %(vals, code_to))

        part_ids = res_partner_obj.search(self.cr, self.uid, val_part)
        po_ids = purchase_order_obj.search(self.cr, self.uid, val_po)
        line_ids = purchase_order_line_obj.search(self.cr, self.uid, [])
        purcs = purchase_order_line_obj.browse(self.cr, self.uid, line_ids)

        for pur in purcs:
            date_po =  pur.order_id and pur.order_id.date_order or False
            state = pur.order_id and pur.order_id.state or ''
            partner_id = pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.id or False
            po_id = pur.order_id and pur.order_id.id or False
            if date_po and state == 'approved' \
                and date_po >= date_from and date_po <= date_to \
                and pur.oustanding_qty > 0 and partner_id in part_ids \
                and po_id in po_ids:
                partner_name = ''

                if pur.order_id:
                    partner_name = pur.order_id.partner_id and pur.order_id.partner_id.name or ''
                if partner_name: partner_name = partner_name.replace('&','&amp;')
                    
                res = {
                    's_name' : pur.order_id and partner_name or '',
                    's_ref' : pur.order_id and pur.order_id.partner_id and pur.order_id.partner_id.ref or '',
                    'order_name' : pur.order_id and pur.order_id.name or '',
                    'part_name' : pur.product_id and pur.product_id.name or '',
                    'etd' : pur.estimated_time_departure or False,
                    'order_qty' : pur.product_qty or '',
                    'unit_price': pur.price_unit,
                    'oustanding': pur.oustanding_qty or '',
                }
                self.oustanding += (pur.oustanding_qty or '')
                
                results.append(res)
                res = {}
        return results 
    
    def _total_oustanding(self):
        return self.oustanding
    
report_sxw.report_sxw('report.po.oustanding.report_landscape', 'purchase.order',
    'addons/max_custom_report/purchase/report/po_oustanding_report.rml', parser=po_oustanding_report, header="internal landscape")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
