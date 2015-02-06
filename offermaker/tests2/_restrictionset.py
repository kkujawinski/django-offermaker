# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from functools import partial

from django.test import TestCase

from offermaker.core import Restriction, RestrictionSet


class OfferMakerCoreRestrictionSet(TestCase):

    def test_intersection_with_rest(self):
        self.assertEqual(
            RestrictionSet.intersection_with_rest(
                RestrictionSet({'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                                'interest_rate': Restriction('interest_rate', [(3, 5), (6, 7)])}),
                RestrictionSet({'interest_rate': Restriction('interest_rate', [(2, 6)]),
                                'product': Restriction('product', ['PROD1'])})),
            [
                RestrictionSet({'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                                'interest_rate': Restriction('interest_rate', [(6, 7)])}),
                RestrictionSet({'interest_rate': Restriction('interest_rate', [(3, 5), (6, 6)])}),
                RestrictionSet({'interest_rate': Restriction('interest_rate', [(2, 3), (5, 6)]),
                                'product': Restriction('product', ['PROD1'])})
            ]
        )

    def test_union_with_intersection(self):
        self.assertEqual(
            RestrictionSet.union_with_intersection(
                RestrictionSet({'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                                'interest_rate': Restriction('interest_rate', [(3, 5), (6, 7)])}),
                RestrictionSet({'interest_rate': Restriction('interest_rate', [(2, 6)]),
                                'product': Restriction('product', ['PROD1'])})),
            RestrictionSet({'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                            'interest_rate': Restriction('interest_rate', [(3, 5), (6, 6)]),
                            'product': Restriction('product', ['PROD1'])})
        )
        self.assertEqual(
            RestrictionSet.union_with_intersection(
                RestrictionSet({'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                                'interest_rate': Restriction('interest_rate', [(2, 3)])}),
                RestrictionSet({'interest_rate': Restriction('interest_rate', [(4, 5)]),
                                'product': Restriction('product', ['PROD1'])})),
            None
        )

    def test_split_to_variants(self):
        my_sorted = partial(sorted, key=RestrictionSet.fields_sorted_key(['crediting_period', 'product']))
        self.assertEqual(
            my_sorted(RestrictionSet({
                'product': Restriction('product', ['PROD1']),
                'crediting_period': Restriction('crediting_period', ['12', '36', '48'])}
            ).items_to_variants()),
            my_sorted([
                RestrictionSet({
                    'product': Restriction('product', ['PROD1']),
                    'crediting_period': Restriction('crediting_period', ['12'])}),
                RestrictionSet({
                    'product': Restriction('product', ['PROD1']),
                    'crediting_period': Restriction('crediting_period', ['36'])}),
                RestrictionSet({
                    'product': Restriction('product', ['PROD1']),
                    'crediting_period': Restriction('crediting_period', ['48'])})
            ]))
        self.assertEqual(
            my_sorted(RestrictionSet({
                'product': Restriction('product', ['PROD1', 'PROD2']),
                'crediting_period': Restriction('crediting_period', ['12', '24'])}
            ).items_to_variants()),
            my_sorted([
                RestrictionSet({
                    'product': Restriction('product', ['PROD1']),
                    'crediting_period': Restriction('crediting_period', ['12'])}),
                RestrictionSet({
                    'product': Restriction('product', ['PROD1']),
                    'crediting_period': Restriction('crediting_period', ['24'])}),
                RestrictionSet({
                    'product': Restriction('product', ['PROD2']),
                    'crediting_period': Restriction('crediting_period', ['12'])}),
                RestrictionSet({
                    'product': Restriction('product', ['PROD2']),
                    'crediting_period': Restriction('crediting_period', ['24'])})
            ]))
