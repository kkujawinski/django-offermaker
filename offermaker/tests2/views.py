# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.http import HttpResponse
from django.views.generic import TemplateView, View

import offermaker

from .models import MyForm


offer = {
    'variants': [
        [{
            'params': {'product': 'PROD1', 'crediting_period': ['24']},
        }, {
            'params': {'product': 'PROD2'},
            'variants': [
                {'params': {'crediting_period': ['12']}},
                {'params': {'crediting_period': ['36']}},
                {'params': {'crediting_period': ['48']}}]
        }, {
            'params': {'product': 'PROD3'},
        }],
        [{
            'params': {'product': 'PROD1'},
            'variants': [
                {'params': {'contribution': (10, 20), 'interest_rate': (2, 2)}},
                {'params': {'contribution': (30, 40), 'interest_rate': (4, 4)}}]
        }, {
            'params': {'product': ['PROD2', 'PROD3']},
            'variants': [{
                'params': {'contribution': (30, 70), 'interest_rate': (5, 5)}
            }]
        }]
    ]
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
