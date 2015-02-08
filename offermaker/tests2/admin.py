# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib import admin
import django

from . import models


class OfferAdmin(admin.ModelAdmin):
    fields = ('name', 'offer')

    if django.VERSION[:2] <= (1, 5):
        class Media:
            js = ('//code.jquery.com/jquery-1.11.0.min.js',)

admin.site.register(models.MyOffer, OfferAdmin)
