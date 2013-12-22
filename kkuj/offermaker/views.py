import json

from django import forms
from django.http import HttpResponse

from kkuj.offermaker.core import OfferMakerCore, NoMatchingVariantsException


class OfferMakerForm(forms.Form):
    pass


class OfferMakerDispatcher(object):

    def __init__(self, form, handler_get, handler_post, offer=None):
        self.form = form
        self.handler_post = handler_post
        self.handler_get = handler_get
        self.offer_core = OfferMakerCore(form, offer)

    def _offermaker_field_descriptions(self, request):
        try:
            matched_variants = self.offer_core.get_form_response(request.GET)
            for field, restriction in matched_variants.items():
                field_description = {'field': field}
                if restriction.items:
                    field_description['items'] = list(restriction.items)
                if restriction.ranges:
                    field_description['ranges'] = list(restriction.ranges)
                if restriction.fixed:
                    field_description['fixed'] = restriction.fixed
                yield field_description
        except NoMatchingVariantsException:
            yield {'field': '__all__', 'errors': 'NoMatchingVariants'}

    def handle_request(self, request):
        if request.method == 'POST':
            form = self.form(request.POST)
            return self.handler_post(form)
        else:
            if request.META.get('HTTP_X_OFFER_FORM_XHR') == '1':
                # AJAX handler
                # items (options/checkboxes/radio values)
                # min (text inputs)
                # max (text inputs)
                # value: $val (no attr - no change)
                # readonly: True/False (no attr - no change)
                fields_descriptions = self._offermaker_field_descriptions(request)
                return HttpResponse(json.dumps(list(fields_descriptions)), content_type="application/json")
            else:
                return self.handler_get(self.form())
