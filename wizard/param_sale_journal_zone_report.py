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

class account_statement_report(osv.osv_memory):
    _name = "param.sale.journal.zone.report"
    _description = "Param Sale Journal Zone Report"

    _columns = {
        'zone_from'         : fields.char('Zone From', size=128),
        'zone_to'           : fields.char('Zone To', size=128),
        'date_from'         : fields.date("From Date"),
        'date_to'           : fields.date("To Date"),
    }

    _defaults = {
        'date_from'         : lambda *a: time.strftime('%Y-01-01'),
        'date_to'           : lambda *a: time.strftime('%Y-%m-%d'),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas               = {'ids': context.get('active_ids', [])}
        datas['model']      = 'param.sale.journal.zone.report'
        datas['form']       = self.read(cr, uid, ids)[0]
        return {
            'type'          : 'ir.actions.report.xml',
            'report_name'   : 'sale.journal.zone_landscape',
            'datas'         : datas,
            'nodestroy'     : True,
        }

account_statement_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
