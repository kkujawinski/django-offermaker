# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple

from django import template
from django.templatetags.static import static
from django.utils import six

register = template.Library()
xrange = six.moves.xrange


@register.simple_tag
def offermaker_javascript(skip=''):
    """
    HTML tag to insert offermaker javascript file
    """
    skip = (skip or '').split(',')

    output = []
    if 'sprintf' not in skip:
        url = static('offermaker/sprintf.min.js')
        if url:
            output.append('<script src="{0}"></script>'.format(url))

    url = static('offermaker/offermaker.js')
    if url:
        output.append('<script src="{0}"></script>'.format(url))

    return ''.join(output)


@register.simple_tag
def offermaker_css():
    """
    HTML tag to insert offermaker css file
    """
    url = static('offermaker/offermaker.css')
    if url:
        return '<link rel="stylesheet" href="{0}">'.format(url)
    return ''

@register.simple_tag
def offermaker_preview(core_object, orientation='HORIZONTAL', fields=None, **attrs):
    TableCell = namedtuple('TableCell', ['value', 'colspan', 'rowspan'])
    SingleCell = TableCell('<value>', 1, 1)
    HeaderCell = namedtuple('HeaderCell', ['name', 'value'])
    _HeaderCell = HeaderCell('<name>', None)
    HtmlTag = namedtuple('HtmlTag', ['tag', 'attrs'])

    def _format_attrs(attrs):
        if not attrs:
            return ''
        return ' ' + ' '.join('{0}="{1}"'.format(k, str(v)) for k, v in attrs.items())

    _format_tag_item = lambda tag: '<{0}{1}>'.format(tag.tag, _format_attrs(tag.attrs)) if isinstance(tag, HtmlTag) else tag

    object_fields = core_object.form_object.fields
    if fields:
        fields = [f.strip() for f in fields.split(',')]
    else:
        fields = list(core_object.form_object.fields.keys())

    summary = core_object.offer_summary(fields=fields)
    if orientation == 'HORIZONTAL':
        table = []
        for field in fields:
            column = [_HeaderCell._replace(name=object_fields[field].label)]
            for row in summary:
                field_value = row[field]
                prev_cell_ref = len(column) - 1
                prev_cell = column[prev_cell_ref]
                if isinstance(prev_cell, int):
                    prev_cell_ref = prev_cell
                    prev_cell = column[prev_cell_ref]
                if prev_cell.value == field_value:
                    column[prev_cell_ref] = prev_cell._replace(rowspan=prev_cell.rowspan + 1)
                    column.append(prev_cell_ref)
                else:
                    column.append(SingleCell._replace(value=field_value))
            table.append(column)

        output_tags = [HtmlTag('table', attrs)]
        tr_attrs = [{}] * len(fields)
        for i in xrange(max(len(i) for i in table)):
            row_fields = []
            for j, column in enumerate(table):
                try:
                    cell = column[i]
                    if isinstance(cell, HeaderCell):
                        row_fields.append(HtmlTag('th', ''))
                        row_fields.append(cell.name)
                        row_fields.append(HtmlTag('/th', ''))
                    elif isinstance(cell, TableCell):
                        attrs = {'colspan': cell.colspan, 'rowspan': cell.rowspan}
                        tr_attrs[j] = attrs
                        row_fields.append(HtmlTag('td', attrs))
                        row_fields.append(cell.value.format_str(object_fields))
                        row_fields.append(HtmlTag('/td', ''))
                except IndexError:
                    pass

            if row_fields:
                output_tags.append(HtmlTag('tr', ''))
                output_tags.extend(row_fields)
                output_tags.append(HtmlTag('/tr', ''))
                last_row_attrs = tr_attrs
            else:
                for attrs in last_row_attrs:
                    attrs['rowspan'] -= 1

        output_tags.append(HtmlTag('/table', ''))

        return ''.join(_format_tag_item(tag) for tag in output_tags)

    return 'TABLE'