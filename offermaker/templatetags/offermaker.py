from collections import namedtuple

from django import template
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def offermaker_javascript(skip=''):
    """
    HTML tag to insert offermaker javascript file
    """
    skip = (skip or '').split(',')

    output = []
    if 'sprintf' not in skip:
        url = static('sprintf.min.js')
        if url:
            output.append(u'<script src="%s"></script>' % url)

    url = static('offermaker.js')
    if url:
        output.append(u'<script src="%s"></script>' % url)

    return u''.join(output)


@register.simple_tag
def offermaker_css():
    """
    HTML tag to insert offermaker css file
    """
    url = static('offermaker.css')
    if url:
        return u'<link rel="stylesheet" href="%s">' % url
    return u''

@register.simple_tag
def offermaker_preview(core_object, orientation='HORIZONTAL', fields=None, table_class=''):
    TableCell = namedtuple('TableCell', ['value', 'colspan', 'rowspan'])
    SingleCell = TableCell('<value>', 1, 1)
    HeaderCell = namedtuple('HeaderCell', ['name', 'value'])
    _HeaderCell = HeaderCell('<name>', None)

    object_fields = core_object.form_object.fields
    if fields:
        fields = [f.strip() for f in fields.split(',')]
    else:
        fields = core_object.form_object.fields.keys()

    summary = core_object.offer_summary(fields=fields)
    if orientation == 'HORIZONTAL':
        table_output = []
        for field in fields:
            column_output = [_HeaderCell._replace(name=field)]
            for row in summary:
                field_value = row[field]
                prev_cell_ref = len(column_output) - 1
                prev_cell = column_output[prev_cell_ref]
                if isinstance(prev_cell, int):
                    prev_cell_ref = prev_cell
                    prev_cell = column_output[prev_cell_ref]
                if prev_cell.value == field_value:
                    column_output[prev_cell_ref] = prev_cell._replace(rowspan=prev_cell.rowspan + 1)
                    column_output.append(prev_cell_ref)
                else:
                    column_output.append(SingleCell._replace(value=field_value))
            table_output.append(column_output)

        output = ['<table border="1" class="%s">' % table_class]
        for i in xrange(max(len(i) for i in table_output)):
            output.append('<tr>')
            for column in table_output:
                try:
                    cell = column[i]
                    if isinstance(cell, HeaderCell):
                        output.append('<th>%(name)s</th>' % cell._asdict())
                    elif isinstance(cell, TableCell):
                        cell_params = cell._asdict()
                        cell_params['value'] = cell_params['value'].format_str(object_fields)
                        output.append('<td colspan="%(colspan)d" rowspan="%(rowspan)d">%(value)s</td>'
                                      % cell_params)
                except IndexError:
                    pass
            output.append('</tr>')
        output.append('</table>')
        return ''.join(output)
    return u'TABLE'