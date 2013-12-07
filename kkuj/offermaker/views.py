from django import forms
from django.utils import safestring
from django.templatetags.static import static

class OfferMakerForm(forms.Form):
    
    def _html_output(self, *args, **kwargs):
        offermaker_js_static = static('kkuj_offer_maker.js')
        script_tag = u'<script type="text/javascript" src="' + offermaker_js_static + '"></script>'
        
        return super(OfferMakerForm, self)._html_output(*args, **kwargs) + \
               safestring.SafeText(script_tag)


class OfferMakerDispatcher(object):
    
    def __init__(self, form, handler_GET, handler_POST):
        self.form = form
        self.handler_POST = handler_POST
        self.handler_GET = handler_GET
    
    def handle_request(self, request):
        if request.method == 'POST':
            form = self.form(request.POST)
            return self.handler_POST(form)
        else:
            if request.META.get('HTTP_X_OFFER_FORM_XHR') == '1':
                pass
                # TODO obsluga AJAXa
            else:
                return self.handler_GET(self.form())
    
    
