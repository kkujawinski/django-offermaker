import json
from django.db import models
from django import forms
from django.forms.util import flatatt
from django.utils.html import mark_safe
from django.templatetags.static import static
import offermaker

select_widget = forms.Select()


class OfferMakerWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        def render_widget_for_field(field_name, field):
            if hasattr(field, 'choices'):
                return select_widget.render('%s__%s' % (name, field_name), '',
                                     choices=field.choices)
            else:
                return field.widget.render('%s__%s' %(name, field_name), '')

        def js_tag(path):
            return u'<script src="%s" type="text/javascript"></script>' % static(path)

        def css_tag(path):
            return u'<link rel="stylesheet" href="%s" type="text/css" />' % static(path)

        form_fields = self.attrs['form_object'].fields
        fields = [render_widget_for_field(field_name, field) for field_name, field in form_fields.items()]
        output = [forms.HiddenInput().render(name, json.dumps(value)),
                  u'<div{0}>{1}</div>'.format(flatatt({'style': 'display: none;', 'id': '%s_fields' % name}),
                                              ''.join(fields)),
                  u'<div{0}></div>'.format(flatatt({'class': 'offer_panel', 'id': '%s_panel' % name})),
                  u'<script type="text/javascript"> window.jQuery = django.jQuery; </script>',

                  css_tag("offermaker/editor.css"),
                  css_tag("offermaker/jquery-ui.min.css"),
                  css_tag("offermaker/bootstrap-tokenfield.min.css"),

                  js_tag("offermaker/jquery-ui.min.js"),
                  js_tag("offermaker/bootstrap-tokenfield.min.js"),
                  js_tag("offermaker/editor.js"),
                  u'<script type="text/javascript">offermaker.editor("%s");</script>' % name,
                  ]
        return mark_safe('\n'.join(output))


class OfferMakerField(forms.Field):
    widget = OfferMakerWidget()

    def __init__(self, form_object, *args, **kwargs):
        self.form_object = form_object
        super(OfferMakerField, self).__init__(*args, **kwargs)

    def widget_attrs(self, *args, **kwargs):
        output = super(OfferMakerField, self).widget_attrs(*args, **kwargs)
        output['form_object'] = self.form_object
        return output


class OfferJSONField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, form_object):
        self.form_object = form_object
        super(OfferJSONField, self).__init__()

    def get_internal_type(self):
        return "TextField"

    def get_prep_value(self, value):
        return json.dumps(offermaker.OfferMakerCore.parse_offer_dict(value))

    def to_python(self, value):
        if not isinstance(value, (unicode, basestring)):
            return value
        return json.loads(value)

    def value_to_string(self, obj):
        return json.dumps(self._get_val_from_obj(obj))

    def formfield(self, **kwargs):
        defaults = {'form_class': OfferMakerField,
                    'form_object': self.form_object}
        defaults.update(kwargs)
        return super(OfferJSONField, self).formfield(**defaults)