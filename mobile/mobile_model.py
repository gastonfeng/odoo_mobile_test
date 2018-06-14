# coding=utf-8
# -*- coding: utf-8 -*-

import os
import sys
import jinja2
import simplejson
from openerp import http
from openerp.http import request
from openerp.osv import fields, osv
import copy, datetime
from dateutil.relativedelta import relativedelta
ISODATEFORMAT = '%Y-%m-%d'
ISODATETIMEFORMAT = "%Y-%m-%d %H:%M:%S"
SUPERUSER_ID = 1
from openerp.tools import float_compare, float_round

class MobileGridLabel(osv.osv):
    _name = 'mobile.grid.label'

    _columns = {
        'name': fields.char(u'名称'),
        'sequence': fields.integer(u'顺序'),
    }


class MobileAction(osv.osv):
    _name = 'mobile.action'

    _columns = {
        'model_id': fields.many2one('ir.model', u'模型名称'),
        'name': fields.char(u'名称'),
        'domain': fields.char('domain'),
        'limit': fields.integer('limit'),
        'offset': fields.integer('offset'),
        'context': fields.char('context'),
        'mobile_view_id': fields.many2one('mobile.view', string=u'视图')
    }


class MobileView(osv.osv):
    _name = 'mobile.view'
    _columns = {
        'mobile_field_ids': fields.one2many('mobile.field', 'view_id', string=u'视图表', copy=True),
        'no_form': fields.boolean(u'不显示form'),
        'model_id': fields.many2one('ir.model', u'模型名称', copy=True),
        'domain_ids': fields.one2many('mobile.domain', 'view_id', string="domain", copy=True),
        'view_type': fields.selection([('tree', u'列表视图'), ('card', u'看板'),
                                       ('view_form', u'表单'), ('edit_form', '编辑表单')], u'view type', copy=True),
        'button_ids': fields.one2many('mobile.button', 'view_id', string='buttons', copy=True),
        'new_form_view': fields.many2one('mobile.view', u'编辑表单', copy=True),
        'show_form_view': fields.many2one('mobile.view', u'展示表单', copy=True),
        'context': fields.text(u'附件值')
    }
    _defaults = {
        'no_form': True
    }


class One2ManyField(osv.osv):
    _name = 'one.many.field'
    _columns = {
        'mobile_field_ids': fields.one2many('mobile.field', 'view_id', string=u'视图表'),

    }


class MobileDomain(osv.osv):
    _name = 'mobile.domain'
    _order = 'sequence'
    _columns = {
        'view_id': fields.many2one('mobile.view', string='view', copy=True),
        'domain': fields.char(u'domain', copy=True),
        'sequence': fields.integer(u'顺序', copy=True),
        'name': fields.char(u'名称', copy=True)
    }


class MobileButton(osv.osv):
    _name = 'mobile.button'
    _columns = {
        'name': fields.char(u'名称', copy=True),
        'button_method': fields.char(u'方法名', copy=True),
        'show_condition': fields.char(u'显示前提', copy=True),
        'view_id': fields.many2one('mobile.view', string=u'视图', copy=True)
    }
    _defaults = {
        'show_condition': []
    }


class MobileField(osv.osv):
    _name = 'mobile.field'
    _order = 'sequence'
    _columns = {
        'sequence': fields.integer(u'序列'),
        'view_id': fields.many2one('mobile.view', u'视图ID', copy=True),
        'ir_field': fields.many2one('ir.model.fields', u'字段', copy=True),
        'domain': fields.char(u'domain'),
        'field_type': fields.related('ir_field', 'ttype', type='char', string=u'字段类型', readonly=True, copy=True),
        'field_relation': fields.related('ir_field', 'relation', type='char', string=u'字段关联', readonly=True, copy=True),
        'field_selection': fields.related('ir_field', 'selection', type='char', string=u'选择项目', readonly=True,
                                          copy=True),
        'model_id': fields.many2one('ir.model', string=u'类型', copy=True),
        'required': fields.boolean(u'必输', copy=True),
        'readonly': fields.boolean(u'只读', copy=True),
        'invisible': fields.boolean(u'不可见', copy=True),
        'is_show_edit_form': fields.boolean(u'form不可见', copy=True),
        'is_show_form_tree': fields.boolean(u'tree不可见', copy=True),
        'field_id': fields.many2one('mobile.field', 'field_id', copy=True),
        'many_field': fields.one2many('mobile.field', 'field_id', string='one2many', copy=True)
    }


class MobileGrid(osv.osv):
    _name = 'mobile.grid'
    _rec_name = 'title'
    _order = 'sequence'
    _columns = {
        'label_id': fields.many2one('mobile.grid.label', u'分类'),
        'sequence': fields.related('label_id', 'sequence', type='integer', string=u'顺序', readonly=True),
        'image': fields.binary(u'图片'),
        'mobile_action_id': fields.many2one('mobile.action', u'动作'),
        'title': fields.char(u'名称')
    }


view_type = {
    'tree': 'Tree',
    'card': 'OdooCard'
}


class MobileController(http.Controller):
    @http.route('/odoo/get/all/grid_data', auth='public', type='http', method=['GET'])
    def get_all_grid_data(self, **args):
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        grid_obj = pool.get('mobile.grid')
        allGridData = {}
        grid_ids = grid_obj.search(cr, uid, [], context=context)
        for grid in grid_obj.browse(cr, uid, grid_ids, context=context):
            allGridData.setdefault(grid.label_id, []).append({
                'title': grid.title,
                'actionId': grid.mobile_action_id.id,
                'image': 'data:image/png;base64,' + grid.image
            })
        gridList = [{'groupTitle': label.name, 'sequence': label.sequence,
                     'gridCols': 4, 'gridRow': row} for label, row in allGridData.iteritems()]
        gridList = sorted(gridList, key=lambda grid: grid.get('sequence'))
        return simplejson.dumps(gridList)

    @http.route('/odoo/get/action/views', auth='public', type='http', method=['GET'])
    def get_action_views(self, **args):
        action_id = int(args.get('actionId', 0))
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        action_row = pool.get('mobile.action').browse(cr, uid, action_id, context=context)
        views_data = [{'title': domain.name,
                       'sequence': domain.sequence,
                       'domain': domain.domain} for domain in action_row.mobile_view_id.domain_ids]
        sorted(views_data, key=lambda view: view.get('sequence'))
        return_val = {
            'title': action_row.name,
            'modelID': action_row.model_id.id,
            'view_id': action_row.mobile_view_id.id,
            'noForm': action_row.mobile_view_id.no_form,
            'model': action_row.model_id.model,
            'limit': action_row.limit or 6,
            'offset': action_row.offset or 6,
            'context': action_row.mobile_view_id.context,
            'viewsData': views_data,
            'view_type': view_type.get(action_row.mobile_view_id.view_type)
        }
        return simplejson.dumps(return_val)

    @http.route('/odoo/get/list/view/data', auth='public', type='http', method=['GET'])
    def get_action_form_pre_view(self, **args):
        action_id = int(args.get('actionId', '0'))
        offset = int(args.get('offset', '0'))
        limit = int(args.get('limit', '0'))
        domain = eval(args.get('domain', '[]'))
        view_id = int(args.get('view_id', '0'))
        if not args.get('model'):
            return simplejson.dumps({})
        model_name = args.get('model')
        if not model_name:
            return simplejson.dumps({})
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        record_ids = pool.get(model_name).search(cr, uid, domain, offset=offset, limit=limit, context=context)
        return_val = []
        for view_row in pool.get('mobile.view').browse(cr, uid, view_id, context=context):
            return_val = self.get_view_type_function(view_row.view_type)(pool, cr, uid, view_row,
                                                                         record_ids, model_name, context=context)
            return simplejson.dumps(return_val)
        return simplejson.dumps(return_val)

    def get_view_type_function(self, type):
        type_dict = {
            'card': self.get_card_view_data,
            'tree': self.get_tree_view_data
        }
        return type_dict.get(type)

    def get_all_field_setting(self, field):
        return {
            'title': field.ir_field.field_description,
            'type': field.field_type,
            'is_show_edit_form': field.is_show_edit_form,
            'is_show_form_tree': field.is_show_form_tree,
            'value': '',
            'required': field.required,
            'readonly': field.readonly,
            'invisible': field.invisible,
            'name': field.ir_field.name,
        }

    def get_tree_view_data(self, pool, cr, uid, view_row, record_ids, model_name, context=None):
        return_val = []
        all_field = []
        for field in view_row.mobile_field_ids:
            all_field.append(self.get_all_field_setting(field))
        for button in view_row.button_ids:
            domain = eval(button.show_condition or '[]') + [('id', 'in', record_ids)]
            mode_ids = pool.get(model_name).search(cr, uid, domain, context=context)
            all_field.append({
                'title': button.name,
                'type': 'button',
                'value': button.button_method,
                'model': model_name,
                'ids': mode_ids,
                'invisible': button.show_condition
            })
        for record in pool.get(model_name).browse(cr, uid, record_ids, context=context):
            new_fields = copy.deepcopy(all_field)
            [field.update(self.card_show_val(record, field, context=context))
             for field in new_fields]
            tree_val = {
                'title': record['display_name'],
                'id': record.id,
                'meta': new_fields
            }
            return_val.append(tree_val)
        return return_val

    def get_card_view_data(self, pool, cr, uid, view_row, record_ids, model_name, context=None):
        return_val = []
        all_field = []
        for field in view_row.mobile_field_ids:
            all_field.append(self.get_all_field_setting(field))
        for button in view_row.button_ids:
            domain = eval(button.show_condition or '[]') + [('id', 'in', record_ids)]
            mode_ids = pool.get(model_name).search(cr, uid, domain, context=context)
            all_field.append({
                'title': button.name,
                'type': 'button',
                'value': button.button_method,
                'model': model_name,
                'ids': mode_ids,
                'invisible': button.show_condition
            })
        for record in pool.get(model_name).browse(cr, uid, record_ids, context=context):
            new_fields = copy.deepcopy(all_field)
            [field.update(self.card_show_val(record, field, context=context))
             for field in new_fields]
            return_val.append({'fieldVals': new_fields, 'id': record.id})
        return return_val

    def card_show_val(self, record, field, context=None):
        return_value = {}
        if field.get('type') not in ('button', 'one2many', 'many2one'):
            return_value.update({'value': self.card_field_type_get_val(field, record, context=context)})
        elif field.get('type') == 'many2one':
            options = self.card_field_type_get_val(field, record, context=context)
            return_value.update({'options': self.card_field_type_get_val(field, record, context=context),
                                 'value': options and options[0] and options[0].get('key')})
        elif field.get('type') == 'button':
            return_value.update(
                {'invisible': False if record['id'] in field.get('ids') else True})
        elif field.get('type') == 'one2many':
            return_value.update({'value': self.get_show_tree_one2many(record, field, context=context),
                                 'table': self.get_record_one2many(record, field,
                                                                   context=dict(context, **{'table': True}))
                                 })
        elif field.get('type') == 'selection':
            value = self.card_field_type_get_val(record, field, context=context)
            return_value.update({'value': value,
                                 'options': [{'key': value[0], 'value': value[1]} for value in
                                             record._fields[field.get('name')].selection]
                                 })

        return return_value

    def get_show_tree_one2many(self, record, field, context=None):
        all_tree_row, table_body = [], []
        many_field = field.get('many_field', [])
        if not (many_field and field.get('name')):
            return ''
        for line in record[field.get('name')]:
            new_fields = copy.deepcopy(many_field)
            [field.update(self.card_show_val(line, field, context=dict(context, **{'table': True})))
             for field in new_fields]
            tree_val = {
                'title': line['display_name'],
                'id': line.id,
                'meta': new_fields
            }
            all_tree_row.append(tree_val)
        return all_tree_row

    def card_field_type_get_val(self, field, record, context=None):
        type = field.get('type')
        value = record[field.get('name')]
        if type in ('char', 'text', 'boolean', 'integer'):
            return value
        elif type == 'many2one':
            if value and value.name_get():
                name = value.name_get()
                return [{'key': name[0][0], 'value': name[0][1]}]
        elif type == 'date':
            date_obj = datetime.datetime.strptime(value, ISODATEFORMAT)
            return (date_obj + relativedelta(hours=8)).strftime(ISODATEFORMAT)
        elif type == 'datetime':
            date_obj = datetime.datetime.strptime(value, ISODATETIMEFORMAT)
            return (date_obj + relativedelta(hours=8)).strftime(ISODATETIMEFORMAT)
        elif type == 'float':
            return float_round(value, precision_digits=2)
        elif type == 'selection':
            return value
        return ''

    def get_record_one2many(self, record, field, context=None):
        table_header, table_body = [], []
        many_field = field.get('many_field', [])
        if not (many_field and field.get('name')):
            return ''
        for son_field in many_field:
            table_header.append(son_field.get('title'))
        for line in record[field.get('name')]:
            new_fields = copy.deepcopy(many_field)
            [field.update(self.card_show_val(line, field, context=context))
             for field in new_fields]
            table_body.append(new_fields)
        return {'tableTh': table_header, 'tableBody': table_body}

    # /odoo/button/method
    @http.route('/odoo/button/method', auth='public', type='http', method=['GET'])
    def mobile_button_method(self, **args):
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        model = args.get('model')
        method = args.get('method')
        ids = int(args.get('ids'))
        model_obj = pool.get(model)
        if model_obj and hasattr(model_obj, method) and ids:
            try:
                getattr(model_obj, method)(cr, uid, ids, context=context)
                return simplejson.dumps({'success': True})
            except Exception as exc:
                if exc and exc.value:
                    return simplejson.dumps({'success': False, 'errMsg': u'%s' % exc.value})

    def get_many_field_value(self, field):
        field_value = self.get_all_field_setting(field)
        if field.field_type == 'many2one':
            field_value.update({'model': field.ir_field.relation, 'domain': field.domain, 'options': []})
        return field_value

    def set_default_val(self, pool, cr, uid, field_value, default_val):
        if default_val.get(field_value.get('name')):
            if field_value.get('type') == 'many2one':
                options = pool.get(field_value.get('model')).name_get(cr, uid, default_val.get(field_value.get('name')), context=None)
                return {'value': default_val.get(field_value.get('name')), 'options': [{'key': option[0], 'value':option[1]} for option in options]}
            else:
                return {'value': default_val.get(field_value.get('name'))}
        return {}
    
    def get_form_view_data(self, pool, cr, uid, view_row, record_ids, model_name, context=None):
        all_field = []
        default_val = pool.get(model_name).default_get(cr, uid, [field.ir_field.name for field
                                                                 in view_row.mobile_field_ids], context=context)
        for field in view_row.mobile_field_ids:
            field_value = self.get_all_field_setting(field)
            if field.field_type == 'many2one':
                field_value.update({'model': field.ir_field.relation, 'domain': field.domain or []})
            if field.field_type == 'selection':
                field_value.update({'options': [{'key': value[0], 'value': value[1]} for value in
                                                pool.get(model_name)._fields[field_value.get('name')].selection]})
            if field.field_type == 'one2many':
                field_value.update({'many_field': [self.get_many_field_value(field) for field in field.many_field],
                                    'value': []})
            field_value.update(self.set_default_val(pool, cr, uid, field_value, default_val))
            all_field.append(field_value)
        for button in view_row.button_ids:
            domain = eval(button.show_condition or '[]') + [('id', 'in', record_ids)]
            mode_ids = pool.get(model_name).search(cr, uid, domain, context=context)
            all_field.append({
                'title': button.name,
                'type': 'button',
                'value': button.button_method,
                'model': model_name,
                'ids': mode_ids,
                'invisible': button.show_condition
            })
        for record in pool.get(model_name).browse(cr, uid, record_ids, context=context):
            new_fields = copy.deepcopy(all_field)
            [field.update(self.card_show_val(record, field, context=context))
             for field in new_fields]
            return {'fieldVals': new_fields, 'id': record.id}

        return {'fieldVals': all_field, 'id': 0}

    # /odoo/form/view/data
    @http.route('/odoo/form/view/data', auth='public', type='http', method=['GET'])
    def get_odoo_view_data(self, **args):
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        model_name = args.get('model')
        view_id = int(args.get('viewId', '0'))
        id = int(args.get('id', '0'))
        view_row = pool.get('mobile.view').browse(cr, uid, view_id, context=context)
        return_val = self.get_form_view_data(pool, cr, uid, view_row.show_form_view, id, model_name, context=context)
        return simplejson.dumps(return_val)

    @http.route('/odoo/model/name_search', auth='public', type='http', method=['GET'])
    def get_odoo_model_name_search(self, **args):
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        model_name = args.get('model')
        limit = int(args.get('limit', '15'))
        value = args.get('value', '')
        domain = eval(args.get('domain', '[]'))
        model_row = pool.get(model_name)
        return_val_list_dict = []
        if model_row:
            return_val = getattr(model_row, 'name_search')(cr, uid, name=value, operator='ilike', args=domain,
                                                           limit=limit, context=context)
            return_val_list_dict = [{'key': val[0], 'value': val[1]} for val in return_val]
        return simplejson.dumps(return_val_list_dict)

    def construct_model_vals(self, id, vals):
        dict_val = {}
        for val in vals:
            if not val.get('value'):
                continue
            if val.get('type') in ('text', 'char', 'date', 'selection') \
                    and val.get('name') != 'id':
                dict_val.update({val.get('name'): val.get('value')})
            elif val.get('type') in ['datetime']:
                date_obj = datetime.datetime.strptime(val.get('value', 0) + ':00', ISODATETIMEFORMAT)
                dict_val.update({val.get('name'): (date_obj - relativedelta(hours=8)).strftime(ISODATETIMEFORMAT)})
            elif val.get('type') in ['integer', 'many2one']:
                dict_val.update({val.get('name'): int(val.get('value', 0))})
            elif val.get('type') in ['float']:
                dict_val.update({val.get('name'): float(val.get('value', 0))})
            elif val.get('type') in ['one2many']:
                line_vals = []
                for line_val in val.get('value'):
                    record_row = {}
                    for field in line_val.get('meta'):
                        record_row.update({field.get('name'): field.get('value')})
                    if not id:
                        line_vals.append((0, 0, record_row))
                    else:
                        line_vals.append((0, 0, record_row))
                dict_val.update({val.get('name'): line_vals})
        return dict_val

    @http.route('/odoo/save/record', auth='public', type='json', method=['POST'])
    def create_new_record(self, **args):
        cr, context, pool = request.cr, request.context, request.registry
        uid = request.session.get('uid') or SUPERUSER_ID
        model = request.jsonrequest.get('model')
        vals = request.jsonrequest.get('value')
        id = request.jsonrequest.get('id')
        vals = self.construct_model_vals(id, vals)
        context_val = eval(request.jsonrequest.get('context', '{}') or '{}')
        try:
            if not id:
                vals.update(context_val.get('default_vals', {}))
                pool.get(model).create(cr, uid, vals, context=context)
            else:
                pool.get(model).write(cr, uid, id, vals, context=context)
            return {'success': True, 'errMsg': u'创建成功！'}
        except Exception as exc:
            if isinstance(exc, basestring):
                return {'success': False, 'errMsg': u'%s' % exc}
            if exc and hasattr(exc, 'value'):
                return {'success': False, 'errMsg': u'%s' % exc.value}
            if exc and hasattr(exc, 'message') and hasattr(exc, 'diag'):
                return {'success': False, 'errMsg': u'%s' % exc.diag.message_primary}
            elif exc and hasattr(exc, 'message'):
                return {'success': False, 'errMsg': u'%s' % exc.message}