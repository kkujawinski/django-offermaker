# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import include, patterns, url
from django.contrib import admin

from . import views


admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^preview/$', views.MyOfferPreviewView.as_view()),
    url(r'^form/$', views.MyOfferFormView.as_view()),
    url(r'^form_success/$', views.MyOfferFormSuccessView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
)
