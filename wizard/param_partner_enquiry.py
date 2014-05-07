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
from tools.translate import _
import time

class report(osv.osv_memory):
    _name = "param.partner.enquiry.report"
    _description = "Param Partner Enquiry Report"
    
    def _get_period(self, cr, uid, context=None):
        period_obj  = self.pool.get('account.period')
        date_now    = time.strftime('%Y-%m-%d')
        period_ids  = period_obj.search(cr, uid, [('date_stop','>=',date_now)], order="date_stop ASC")
        period_id   = False
        if period_ids:
            period_id = period_ids[0]
        return period_id

    _columns = {
        'partner_id'    : fields.many2one('res.partner', 'Customer', domain=[('customer','=',True)]),
        'period_id'     : fields.many2one('account.period', 'Period', domain=[('state', '=','draft')]),
    }
    _defaults = {
        'period_id'     : _get_period,
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas           = {'ids': context.get('active_ids', [])}
        datas['model']  = 'param.partner.enquiry.report'
        datas['form']   = self.read(cr, uid, ids)[0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'partner.enquiry',
            'datas': datas,
        }

report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
