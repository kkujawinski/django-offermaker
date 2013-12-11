import json

from django import forms
from django.http import HttpResponse
from django.utils import safestring
from django.templatetags.static import static
from kkuj.offermaker.core import OfferMakerCore


class OfferMakerForm(forms.Form):

    def _html_output(self, *args, **kwargs):
        offer_maker_js_static = static('kkuj_offer_maker.js')
        script_tag = u'<script type="text/javascript" src="' + offer_maker_js_static + '"></script>'
        
        return super(OfferMakerForm, self)._html_output(*args, **kwargs) + \
            safestring.SafeText(script_tag)


class OfferMakerDispatcher(object):

    def __init__(self, form, handler_get, handler_post, offer=None):
        self.form = form
        self.handler_post = handler_post
        self.handler_get = handler_get
        self.offer_core = OfferMakerCore(offer)

    def handle_request(self, request):
        if request.method == 'POST':
            form = self.form(request.POST)
            return self.handler_post(form)
        else:
            if request.META.get('HTTP_X_OFFER_FORM_XHR') == '1':
                self.offer_core.set_values(request.GET)
                # AJAX handler
                # items (options/checkboxes/radio values)
                # min (text inputs)
                # max (text inputs)
                # value: $val (no attr - no change)
                # readonly: True/False (no attr - no change)
                output = [
                    {
                        'field': 'crediting_period',
                        'value': '2',
                    }
                ]
                return HttpResponse(json.dumps(output), content_type="application/json")
            else:
                return self.handler_get(self.form())

    
