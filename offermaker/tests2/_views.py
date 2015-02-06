# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import xml.etree.ElementTree as ET

from django.test import Client
from django.test import TestCase


class OfferMakerViewsTest(TestCase):
    urls = 'offermaker.tests2.urls'

    @classmethod
    def setUpClass(cls):
        cls.client = Client()

    def test_preview_view(self):
        resp = self.client.get('/preview/')
        self.assertEqual(resp.status_code, 200)

    def test_form_view(self):
        resp = self.client.get('/form/')
        self.assertEqual(resp.status_code, 200)

    def test_form_validation(self):
        resp = self.client.post('/form/', {
            'product': 'PROD1',
            'crediting_period': '12',  # this is against defined variants
            'interest_rate': '2',
            'contribution': '15',
            'some_field': '12'
        })
        resp_content = ET.fromstring(resp.content)

        # Python 2.6.6 contains an older version of ElementTree that
        # does not have support for searching for attributes [@attribute] syntax
        li_error_element = [
            el for el in resp_content.findall('.//ul')
            if 'errorlist' in el.attrib['class']
        ][0].findall('./li')[0]
        self.assertEqual(li_error_element.text, 'Variants not matching with given values')

        resp = self.client.post('/form/', {
            'product': 'PROD1',
            'crediting_period': '24',
            'interest_rate': '2',
            'contribution': '15',
            'some_field': '12'
        }, follow=True)
        self.assertEqual(resp.content.decode(), 'SUCCESS')
