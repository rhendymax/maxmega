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

class param_profit_and_lost_report(osv.osv_memory):
    _name = 'param.profit.and.lost.report'
    _description = 'Param Profit and Lost Report'
    _columns = {
        'period_from':fields.many2one('account.period', 'Period From', required=False),
        'period_to':fields.many2one('account.period', 'Period To', required=False),
#        'date_from': fields.date("From Date", required=True),
#        'date_to': fields.date("To Date", required=True),
#        'partner_code_from':fields.many2one('res.partner', 'Customer Code From', required=False),
#        'partner_code_to':fields.many2one('res.partner', 'Customer Code To', required=False),
#        'inv_from':fields.many2one('account.invoice', 'Invoice From', required=False),
#        'inv_to':fields.many2one('account.invoice', 'Invoice To', required=False),
        # 'product_id': fields.many2one('product.product', 'Item Code', domain=[('sale_ok','=',True)], change_default=True),
    }

#    _defaults = {
#        'date_from': lambda *a: time.strftime('%Y-01-01'),
#        'date_to': lambda *a: time.strftime('%Y-%m-%d')
#    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.profit.and.lost.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'max.profit.and.lost.report',
            'datas': datas,
        }

param_profit_and_lost_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
