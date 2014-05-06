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

class param_balance_sheet_report(osv.osv_memory):
    _name = 'param.balance.sheet.report'
    _description = 'Param Balance Sheet Report'
    _columns = {
        'period_from':fields.many2one('account.period', 'Period From', required=False),
        'period_to':fields.many2one('account.period', 'Period To', required=False),
    }

    def create_vat(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'param.balance.sheet.report'
        datas['form'] = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'balance.sheet.report',
            'datas': datas,
        }

param_balance_sheet_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
