# -*- encoding: utf-8 -*-
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
from osv import osv, fields
from tools.translate import _
import decimal_precision as dp
import re

class res_consigning(osv.osv):
    _name = "res.consigning"
    _description = "Po Requirement"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'note': fields.text('Notes'),
    }

res_consigning()

class res_note_user(osv.osv):
    _name = "res.note.user"
    _description = "Shipping Instruction"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'note': fields.text('Notes'),
    }

res_note_user()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
