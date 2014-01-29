import json
import re

from django.http import HttpResponse

from offermaker.core import OfferMakerCore, NoMatchingVariantsException


class OfferMakerDispatcher(object):

    def __init__(self, handler_get, handler_post, form=None, offer=None, core_object=None):
        self.handler_post = handler_post
        self.handler_get = handler_get
        if core_object is None:
            self.form = form
            self.offer_core = OfferMakerCore(form, offer)
        else:
            self.form = core_object.form
            self.offer_core = core_object

    @classmethod
    def from_core_object(cls, handler_get, handler_post, core_object):
        return OfferMakerDispatcher(handler_get, handler_post, core_object=core_object)

    def _offermaker_field_descriptions(self, request):
        try:
            process_fn = self.offer_core.process
            matched_variants = process_fn(request.GET,
                                          initiator=request.GET.get('__initiator__'),
                                          break_variant=request.GET.get('__break_current_variant__') == 'true')
            for field, restriction in matched_variants.items():
                field_description = {'field': field}
                if restriction.items:
                    field_description['items'] = sorted(list(restriction.items))
                if restriction.ranges:
                    field_description['ranges'] = sorted(list(restriction.ranges))
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
                json_output = json.dumps(list(fields_descriptions))
                json_output = re.compile(r'\bInfinity\b').sub('null', json_output)
                return HttpResponse(json_output, content_type="application/json")
            else:
                return self.handler_get(self.form())
