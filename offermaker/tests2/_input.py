# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from django.test import TestCase

from offermaker.core import Restriction


class OfferMakerCoreInputTest(TestCase):

    def assertRaisesRegexp(self, *args, **kwargs):
        if sys.version_info < (3, 0):
            return super(OfferMakerCoreInputTest, self).assertRaisesRegexp(*args, **kwargs)
        else:
            return self.assertRaisesRegex(*args, **kwargs)

    def test_restriction_input_range_items_mix(self):
        self.assertRaisesRegexp(
            Exception, "Can't mix range restriction with items restriction.",
            Restriction, 'field1', [(3, 4), 'a']
        )

    def test_restriction_input_range_two_element_tuple(self):
        self.assertRaisesRegexp(
            Exception, "Range restriction must be two element tuple",
            Restriction, 'field1', (3, 4, 5)
        )
        self.assertRaisesRegexp(
            Exception, "Range restriction must be two element tuple",
            Restriction, 'field1', [(1, 2), (3, 4, 5)]
        )

    def test_restriction_input_range_same_type(self):
        self.assertRaisesRegexp(
            Exception, "Both side of range restriction must be numeric",
            Restriction, 'field1', ('0', 2)
        )
        self.assertRaisesRegexp(
            Exception, "Both side of range restriction must be numeric",
            Restriction, 'field1', [(1, 2), (0, '2')]
        )

    def test_restriction_input_range_left_side_smaller_than_right(self):
        self.assertRaisesRegexp(
            Exception, "Left side must smaller the right in range restriction",
            Restriction, 'field1', (3, 2)
        )
        self.assertRaisesRegexp(
            Exception, "Left side must smaller the right in range restriction",
            Restriction, 'field1', [(1, 2), (3, 2)]
        )

    def test_restriction_input_items_same_type(self):
        self.assertRaisesRegexp(
            Exception, "All items in restriction must have same type",
            Restriction, 'field1', ['1', '2', 4]
        )
