from osv import fields, osv
import datetime

class tigernix_export(osv.osv):
    _name = 'tigernix.export'
    
    _columns = {
        'name'          : fields.char('Name',size=64),
        'field_line'    : fields.one2many('tigernix.export.field', 'export_id', 'Filter Field', help="The rule is satisfied if at least one test is True"),
        'filter_line'   : fields.one2many('tigernix.export.filter', 'export_id', 'Filter Field',),
        'model_id'      : fields.many2one('ir.model', 'Object',select=1),
        'field_ids'     : fields.many2many('ir.model.fields', 'export_field_rel', 'field_id', 'export_id', 'Field Selection'),
    }
    
    
tigernix_export()

class tigernix_export_field(osv.osv):
    _name = 'tigernix.export.field'
    _rec_name = 'field_id'
    
    _columns = {
        'export_id' : fields.many2one('tigernix.export', 'Export Root'),
        'field_id'  : fields.many2one('ir.model.fields', 'Field', domain= "[('model_id','=', parent.model_id)]",  select=1),
    }
    
tigernix_export_field()


class tigernix_export_filter(osv.osv):
    _name = 'tigernix.export.filter'
    _rec_name = 'field_id'
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(tigernix_export_filter, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        
        list = []
        if 'parent_id' in context:
            field_obj  = self.pool.get('ir.model.fields')
            field_ids  = field_obj.search(cr,uid,[('model_id','=',context['parent_id'])])
            fields    = field_obj.browse(cr,uid,field_ids)
                    
            for field in fields:
                if field.model_id.model:
                    object = self.pool.get(field.model_id.model)
                    if field.name in object._columns:
                        if 'function' in str(object._columns[field.name]):
                            continue
                        else:
                            list.append(field.id)

        form = """ <field name="field_id" colspan="2" domain="[('model_id','=', parent.model_id),('id','in',%s),('ttype','not in',('one2many','many2many'))]" on_change="onchange_field_id(field_id)" required="1"/>  """ % list
        res['arch'] = res['arch'].replace(str("""<field name="field_id" colspan="2" domain="[('model_id','=', parent.model_id)]" on_change="onchange_field_id(field_id)" required="1"/>"""),form)

        return res
    
    def _overall_operand(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.type == 'boolean':
                if line.operand_bool:
                    res[line.id] = 'Yes'
                else:
                    res[line.id] = 'No'
            elif line.type == 'date':
                res[line.id] = line.operand_date
            elif line.type == 'datetime':
                res[line.id] = line.operand_datetime
            else:
                res[line.id] = line.operand
        return res
    
    _columns = {
        'export_id'          : fields.many2one('tigernix.export', 'Export Root'),
        'field_id'           : fields.many2one('ir.model.fields', 'Field', select=1),
        'operator'           : fields.selection((('=', '='), ('<>', '<>'), ('<=', '<='), ('>=', '>='), ('<', '<'), ('>', '>'), ('child_of', 'child_of'), ('like', 'like'), ('ilike', 'ilike'),('in', 'in')), 'Operator'),
        'type'               : fields.char('Type', size=64),
        'overall_operand'    : fields.function(_overall_operand, method=True, type='char', string='Operand', size=64),
        'operand'            : fields.char('Operand', size=64),
        'operand_bool'       : fields.boolean('Operand'),
        'operand_date'       : fields.date('Operand'),
        'operand_datetime'   : fields.datetime('Operand'),
        
    }
    
    def onchange_field_id(self,cr,uid,ids,field_id):
        result = {}
        if not field_id:
            return {'value' : {'type' : False}}
        field  = self.pool.get('ir.model.fields').browse(cr,uid,field_id)
        type   = field.ttype
        
        result['type']   = type
        return {'value' : result}
        
    
tigernix_export_filter()