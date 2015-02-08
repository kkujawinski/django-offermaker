# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.http import HttpResponse
from django.views.generic import TemplateView, View

import offermaker

from .models import MyForm


offer = {
    'params': {},
    'variants': [[
        {
            'params': {
                'crediting_period': ['24'],
                'product': ['PROD1']
            }
        }, {
            'params': {
                'crediting_period': ['12', '36', '48'],
                'product': ['PROD2']
            }
        }, {
            'params': {
                'product': ['PROD3']
            }
        }
    ], [
        {
            'params': {
                'contribution': [[10, 20]],
                'interest_rate': [[2, 2]],
                'product': ['PROD1']
            }
        }, {
            'params': {
                'contribution': [[30, 40]],
                'interest_rate': [[4, 4]],
                'product': ['PROD1']
            }
        }, {
            'params': {
                'contribution': [[30, 70]],
                'interest_rate': [[5, 5]],
                'product': ['PROD2', 'PROD3']
            }
        }
    ]]
}


class MyOfferFormView(offermaker.OfferMakerFormView):
    form_class = MyForm
    offermaker_offer = offer
    template_name = 'offer_form.html'
    success_url = '/form_success/'


class MyOfferFormSuccessView(View):
    def get(self, request):
        return HttpResponse('SUCCESS')


class MyOfferPreviewView(TemplateView):
    template_name = 'offer_preview.html'

    def get_context_data(self):
        output = super(MyOfferPreviewView, self).get_context_data()
        output['offer'] = offermaker.OfferMakerCore(MyForm, offer)
        return output
