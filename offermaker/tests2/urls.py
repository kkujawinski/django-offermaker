# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^preview/$', views.MyOfferPreviewView.as_view()),
    url(r'^form/$', views.MyOfferFormView.as_view()),
    url(r'^form_success/$', views.MyOfferFormSuccessView.as_view()),
)
