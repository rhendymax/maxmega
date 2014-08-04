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

import time
from report import report_sxw
#from tools.translate import _

class voucher(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(voucher, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'company': self.pool.get('res.company').browse(cr, uid, (self.pool.get('res.users').browse(cr, uid, uid).company_id.id)),
            'to_upper': self.to_upper,
            'get_partner_address': self.get_partner_address,
            'split_word': self.split_word,
            'get_line_amount': self._get_line_amount,
        })

    def to_upper(self, s):
        return s.upper()

    def _get_line_amount(self, voucher_type, line_type, amount):
        cr          = self.cr
        uid         = self.uid
##
#        print voucher_type
#        print line_type
#        print amount
#        sign = 1
#        raise osv.except_osv(_('Invalid action !'), _('Test'))
        if voucher_type == 'payment' and line_type == 'cr':
            amount = amount * -1
        elif voucher_type == 'receipt' and line_type == 'dr':
            amount = amount * -1
#        print amount
        return amount

    def get_partner_address(self, partner, add=False):
        result = ''
#        raise osv.except_osv(_('Invalid action !'), _('Test'))
        if partner.address:
            address = partner.address[0]
            result = address.street and address.street + ' ' or '' + \
                     address.street2 and address.street2 + ' ' or '' + \
                     address.city and address.city + ' ' or '' + \
                     address.zip and address.zip or ''
            if add == 'country':
                result = address.country_id and address.country_id.name or ''
        return result
    
    def split_word(self, s):
        res = s
        max = 17
        if len(s) > max:
            count = 0
            res = ''
            for i in s:
                count += 1
                res += i
                if count == max:
                    res += ' '
                    count = 0
        return res

report_sxw.report_sxw('report.account.voucher', 'account.voucher', 'addons/max_report/report/voucher.rml', parser=voucher, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

