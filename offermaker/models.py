# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json

from django import forms
from django.forms.util import flatatt
from django.utils import six
from django.utils.html import mark_safe
from django.utils.encoding import force_text
from django.templatetags.static import static
from django.core.exceptions import ValidationError

from jsonfield import JSONField
from jsonfield.fields import JSONFormField

from .core import OfferMakerCore

select_widget = forms.Select()


class OfferMakerWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        def render_widget_for_field(field_name, field):
            if hasattr(field, 'choices'):
                return select_widget.render(
                    '{0}__{1}'.format(name, field_name), '',
                    choices=field.choices
                )
            else:
                return field.widget.render('{0}__{1}'.format(name, field_name), '')

        def js_tag(path):
            return '<script src="{0}" type="text/javascript"></script>'.format(static(path))

        def css_tag(path):
            return '<link rel="stylesheet" href="{0}" type="text/css" />'.format(static(path))

        form_fields = self.attrs['form_object'].fields
        fields = [render_widget_for_field(field_name, field) for field_name, field in form_fields.items()]
        value = value if value else {}
        value = value if isinstance(value, six.string_types) else json.dumps(value)

        field_labels_json = ', '.join([
            '{0}: "{1}"'.format(field_name, force_text(field.label))
            for field_name, field in form_fields.items()
        ])

        output = [forms.HiddenInput().render(name, value),
                  '<ul class="editor-instructions">',
                  '<li>Only already tagged values are saved. Use TAB or ENTER to convert.</li>',
                  '<li>Use ":" as range values link, ex. 1:2.</li>',
                  '<li>No value at the beginning or the end of the range means minus infinity or '
                  'plus infinity, ex. :2, 3:)</li></ul>',
                  '<div{0}>{1}</div>'.format(flatatt({'style': 'display: none;', 'id': '{0}_fields'.format(name)}),
                                              ''.join(fields)),
                  '<div{0}></div>'.format(flatatt({'class': 'offermaker_panel',
                                                             'id': '{0}_panel'.format(name)})),
                  '<script type="text/javascript">',
                  'window.jQuery = window.jQuery || django.jQuery;',
                  '</script>',

                  css_tag("offermaker/editor.css"),
                  css_tag("offermaker/jquery-ui.min.css"),
                  css_tag("offermaker/bootstrap-tokenfield.min.css"),

                  js_tag("offermaker/jquery-ui.min.js"),
                  js_tag("offermaker/bootstrap-tokenfield.min.js"),
                  js_tag("offermaker/editor.js"),

                  '<script type="text/javascript">' +
                  'offermaker.labels = offermaker.labels || {}; ' +
                  'offermaker.labels.{0} = {{ {1} }}; '.format(name, field_labels_json) +
                  'offermaker.editor("{0}"); '.format(name) +
                  '</script>',
                  ]
        return mark_safe('\n'.join(output))


class OfferMakerField(JSONFormField):
    def __init__(self, form_object, *args, **kwargs):
        self.form_object = form_object
        super(OfferMakerField, self).__init__(*args, **kwargs)

    def widget_attrs(self, *args, **kwargs):
        output = super(OfferMakerField, self).widget_attrs(*args, **kwargs)
        output['form_object'] = self.form_object
        return output


class OfferJSONField(JSONField):
    def __init__(self, form_object=None, *args, **kwargs):
        if form_object is not None:
            self.form_object = form_object
        try:
            self.form_object
        except AttributeError:
            raise NotImplemented('Form object is not defined for the field.')
        super(OfferJSONField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': OfferMakerField,
            'form_object': self.form_object,
        }
        defaults.update(kwargs)
        defaults['widget'] = OfferMakerWidget()
        field = super(OfferJSONField, self).formfield(**defaults)
        if field.help_text == "Enter valid JSON":
            field.help_text = None
        return field

    def validate(self, value, model_instance):
        offer = OfferMakerCore(self.form_object, value)
        json_variants = [{'variant': key, 'groups': val} for key, val in offer.get_conflicts().items()]
        if json_variants:
            raise ValidationError(
                "Some variants are not compatible with group of variants.|CONFLICTED-VARIANT|%s" %
                json.dumps(json_variants)
            )
