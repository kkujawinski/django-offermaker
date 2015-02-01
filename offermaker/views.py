# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import re

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.forms.forms import NON_FIELD_ERRORS
from django.views.generic.edit import FormView

from offermaker.core import OfferMakerCore, NoMatchingVariantsException


class OfferMakerFormView(FormView):
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST' and request.META.get('HTTP_X_OFFER_FORM_XHR') == '1':
            return self.offermaker_post_xhr(request)
        return super(OfferMakerFormView, self).dispatch(request, *args, **kwargs)

    def offermaker_post_xhr(self, request):
        fields_descriptions = self._offermaker_post_xhr_fields(request)
        json_output = json.dumps(list(fields_descriptions))
        json_output = re.compile(r'\bInfinity\b').sub('null', json_output)
        return HttpResponse(json_output, content_type="application/json")

    def get_form(self, *args, **kwargs):
        form = super(OfferMakerFormView, self).get_form(*args, **kwargs)
        if not getattr(self, 'skip_form_validation', False) and self.request.POST:
            old_full_clean = form.full_clean

            def new_full_clean(*args, **kwargs):
                old_full_clean(*args, **kwargs)
                try:
                    self.get_offermaker_core().process(self.request.POST)
                except NoMatchingVariantsException:
                    form._errors[NON_FIELD_ERRORS] = form.error_class(['Variants not matching with given values'])

            form.full_clean = new_full_clean
        return form

    def get_context_data(self, **kwargs):
        context = super(OfferMakerFormView, self).get_context_data(**kwargs)
        context['offermaker_object'] = self.get_offermaker_core()
        return context

    def get_offermaker_core(self):
        try:
            self.offermaker_offer
        except AttributeError:
            raise ImproperlyConfigured('OfferMakerFormView needs to have offermaker_offer attribute.')
        return OfferMakerCore(
            self.get_form_class(),
            self.offermaker_offer
        )

    def _offermaker_post_xhr_fields(self, request):
        try:
            process_fn = self.get_offermaker_core().process
            matched_variants = process_fn(
                request.POST,
                initiator=request.POST.get('__initiator__'),
                break_variant=request.POST.get('__break_current_variant__') == 'true'
            )
            for field, restriction in matched_variants.items():
                skip_restriction = False
                field_description = {'field': field}
                if restriction.items:
                    field_description['items'] = sorted(list(restriction.items))
                if restriction.ranges:
                    if len(restriction.ranges) == 1:
                        range = next(iter(restriction.ranges))
                        if range[0] == -float("inf") and range[1] == float("inf"):
                            skip_restriction = True
                    field_description['ranges'] = sorted(list(restriction.ranges))
                if restriction.fixed:
                    field_description['fixed'] = restriction.fixed
                if not skip_restriction:
                    yield field_description
        except NoMatchingVariantsException:
            yield {'field': '__all__', 'errors': 'NoMatchingVariants'}
