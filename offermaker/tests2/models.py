# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import django
from django.db import models
from django import forms

import offermaker


class MyForm(forms.Form):
    product = forms.ChoiceField(
        label='Product',
        choices=(
            ('', '---'), ('PROD1', 'Product X'), ('PROD2', 'Product Y'), ('PROD3', 'Product Z'),
        ),
        required=False)
    crediting_period = forms.ChoiceField(
        label='Crediting period',
        choices=(('', '---'), ('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')))
    interest_rate = forms.FloatField(label='Interest rate', min_value=1, max_value=5)
    contribution = forms.FloatField(label='Contribution', min_value=0)

    if django.VERSION[:2] <= (1, 5):
        def __init__(self, *args, **kwargs):
            super(MyForm, self).__init__(*args, **kwargs)
            self.fields['interest_rate'].widget.attrs['data-om-type'] = 'number'
            self.fields['interest_rate'].widget.attrs['data-om-min'] = 1
            self.fields['interest_rate'].widget.attrs['data-om-max'] = 5
            self.fields['contribution'].widget.attrs['data-om-type'] = 'number'
            self.fields['contribution'].widget.attrs['data-om-min'] = 0


class MyOfferMakerField(offermaker.OfferJSONField):
    form_object = MyForm()


class MyOffer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    offer = MyOfferMakerField()
