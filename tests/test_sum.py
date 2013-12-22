__author__ = 'kamil'
from unittest2 import TestCase
from kkuj.offermaker.core import Restriction


class OfferMakerCoreSumTest(TestCase):

    def test_restriction_sum_range(self):
        self.assertEqual(
            Restriction('f', (1, 2)) + Restriction('f', (3, 4)) + Restriction('f', (5, 6)),
            Restriction('f', [(1, 2), (3, 4), (5, 6)]),
        )
        self.assertEqual(
            Restriction('f', (1, 3)) + Restriction('f', (3, 4)) + Restriction('f', (4, 6)),
            Restriction('f', [(1, 6)]),
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
