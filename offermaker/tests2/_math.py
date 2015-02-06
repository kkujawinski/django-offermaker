# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from django.test import TestCase

from offermaker.core import Restriction, Range


class OfferMakerCoreMathTest(TestCase):

    def test_restriction_sum_range(self):
        self.assertEqual(
            Restriction('f', (1, 2)) + Restriction('f', (3, 4)) + Restriction('f', (5, 6)),
            Restriction('f', [(1, 2), (3, 4), (5, 6)]),
        )
        self.assertEqual(
            Restriction('f', (1, 3)) + Restriction('f', (3, 4)) + Restriction('f', (4, 6)),
            Restriction('f', [(1, 6)]),
        )

    def test_restriction_diff_range(self):
        self.assertEqual(
            Restriction('f', (1, 2)) - Restriction('f', [(-1, 1), (3, 4)]),
            Restriction('f', (1, 2)),
        )
        self.assertEqual(
            Restriction('f', (1, 3)) - Restriction('f', (2, 4)),
            Restriction('f', (1, 2)),
        )
        self.assertEqual(
            Restriction('f', (1, 10)) - Restriction('f', [(2, 4), (5, 6)]),
            Restriction('f', [(1, 2), (4, 5), (6, 10)]),
        )
        self.assertEqual(
            Restriction('f', (3, 5)) - Restriction('f', (2, 4)),
            Restriction('f', (4, 5)),
        )
        self.assertEqual(
            Restriction('f', [(3, 4), (5, 6), (7, 8)]) - Restriction('f', (1, 10)),
            None,
        )
        self.assertEqual(
            Restriction('f', [(1, 2), (3, 4), (5, 6)]) - Restriction('f', (1, 2)),
            Restriction('f', [(3, 4), (5, 6)]),
        )
        self.assertEqual(
            Restriction('f', (1, 6)) - Restriction('f', (3, 4)),
            Restriction('f', [(1, 3), (4, 6)]),
        )
        self.assertEqual(
            Restriction('f', [(3, 5), (6, 7)]) - Restriction('f', (2, 6)),
            Restriction('f', [(6, 7)]),
        )
        self.assertEqual(
            Restriction('f', [(3, 5), (6, 7)]) - Restriction('f', [(3, 5), (6, 6)]),
            Restriction('f', [(6, 7)]),
        )

    def test_restriction_sum_range_infinite(self):
        self.assertEqual(
            Restriction('f', (None, 2)) + Restriction('f', (2, None)),
            Restriction('f', (None, None)),
        )
        self.assertEqual(
            Restriction('f', (None, 2)) + Restriction('f', (2, 10)),
            Restriction('f', [(None, 10)]),
        )
        self.assertEqual(
            Restriction('f', (None, 2)) + Restriction('f', (4, None)),
            Restriction('f', [(None, 2), (4, None)]),
        )

    def test_restriction_diff_range_infinite(self):
        self.assertEqual(
            Restriction('f', (None, 2)) - Restriction('f', (3, None)),
            Restriction('f', (None, 2)),
        )
        self.assertEqual(
            Restriction('f', (None, 3)) - Restriction('f', (2, None)),
            Restriction('f', (-float('inf'), 2)),
        )
        self.assertEqual(
            Restriction('f', (None, 10)) - Restriction('f', [(2, 4), (5, 6)]),
            Restriction('f', [(None, 2), (4, 5), (6, 10)]),
        )
        self.assertEqual(
            Restriction('f', (1, None)) - Restriction('f', [(2, 4), (5, 6)]),
            Restriction('f', [(1, 2), (4, 5), (6, None)]),
        )
        self.assertEqual(
            Restriction('f', (3, None)) - Restriction('f', (None, 4)),
            Restriction('f', (4, float('inf'))),
        )
        self.assertEqual(
            Restriction('f', [(3, 4), (5, 6), (7, 8)]) - Restriction('f', (None, 10)),
            None,
        )
        self.assertEqual(
            Restriction('f', (None, 2)) - Restriction('f', (2, None)),
            Restriction('f', (-float('inf'), 2)),
        )
        self.assertEqual(
            Restriction('f', (None, 5)) - Restriction('f', (2, 10)),
            Restriction('f', [(None, 2)]),
        )
        self.assertEqual(
            Restriction('f', [(None, 2), (4, None)]) - Restriction('f', (4, None)),
            Restriction('f', (-float("inf"), 2))
        )

    def test_restriction_sum_items(self):
        self.assertEqual(
            Restriction('f', 1) + Restriction('f', 2),
            Restriction('f', [1, 2]),
        )
        self.assertEqual(
            Restriction('f', [1, 2, 3]) + Restriction('f', 3),
            Restriction('f', [1, 2, 3]),
        )
        self.assertEqual(
            Restriction('f', [1]) + Restriction('f', [2, 3]),
            Restriction('f', [1, 2, 3]),
        )
        self.assertEqual(
            Restriction('f', 1) + Restriction('f', 1),
            Restriction('f', 1),
        )

    def test_restriction_diff_items(self):
        self.assertEqual(
            Restriction('f', [1, 2]) - Restriction('f', 2),
            Restriction('f', 1),
        )
        self.assertEqual(
            Restriction('f', [1, 2, 3]) - Restriction('f', 3),
            Restriction('f', [1, 2]),
        )
        self.assertEqual(
            Restriction('f', [1]) - Restriction('f', [2, 3]),
            Restriction('f', [1]),
        )
        self.assertEqual(
            Restriction('f', 1) - Restriction('f', 1),
            None,
        )

    def test_range_sets_sum(self):
        self.assertEqual(
            frozenset(Range.sets_sum(
                frozenset([Range(None, 2), Range(-1, 5), Range(8, 11), Range(12, None), Range(14, 17)]))),
            frozenset([Range(None, 5), Range(8, 11), Range(12, None)])
        )

    def test_range_sets_product(self):
        self.assertEqual(
            frozenset(Range.sets_product([
                frozenset([Range(None, -1), Range(3, 8), Range(10, 15)]),
                frozenset([Range(-2, 0), Range(2, 6), Range(7, None)])])),
            frozenset([Range(-2, -1), Range(3, 6), Range(7, 8), Range(10, 15)])
        )
        self.assertEqual(
            frozenset(Range.sets_product([frozenset([Range(1, 2)]), frozenset([Range(3, 4)])])),
            frozenset())

    def test_ranges_mul(self):
        self.assertEqual(Range(None, 10) * Range(5, None), Range(5, 10))
        self.assertEqual(Range(1, 5) * Range(6, 10), None)
        self.assertEqual(Range(1, 5) * Range(5, 10), Range(5, 5))


