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

class param_monthly_pos_report(osv.osv_memory):
    _name = 'param.monthly.pos.report'
    _description = 'Param Monthly POS Report with Selected Brand'
    _columns = {
        'date_selection': fields.selection([('none_sel','None'),('date_sel', 'Date')],'Type Selection', required=True),
        'date_from': fields.date("From Date"),
        'date_to': fields.date("To Date"),
        'brand_selection': fields.selection([('all_vall','All'),('def','Default'),('input', 'Input'),('selection','Selection')],'Inventory Brand Filter Selection', required=True),
        'brand_default_from':fields.many2one('product.brand', 'Inventory Brand From', domain=[], required=False),
        'brand_default_to':fields.many2one('product.brand', 'Inventory Brand To', domain=[], required=False),
        'brand_input_from': fields.char('Inventory Brand From', size=128),
        'brand_input_to': fields.char('Inventory Brand To', size=128),
        'brand_ids' :fields.many2many('product.brand', 'report_monthly_brand_rel', 'report_id', 'brand_id', 'Inventory Brand', domain=[]),
    }

    _defaults = {
       'date_selection':'none_sel',
       'brand_selection':'all_vall',
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.monthly.pos.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'monthly.pos.report_landscape',
            'datas': datas,
        }

param_monthly_pos_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
