__author__ = 'kamil'
from unittest2 import TestCase
from offermaker.core import Range


class OfferMakerCoreRangeTest(TestCase):

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
            frozenset(Range.sets_product([frozenset([Range(1, 2)]), frozenset([Range(3,4)])])),
            frozenset())
       
                     


    def test_ranges_mul(self):
        self.assertEqual(Range(None, 10) * Range(5, None), Range(5, 10))
        self.assertEqual(Range(1, 5) * Range(6, 10), None)
        self.assertEqual(Range(1, 5) * Range(5, 10), Range(5, 5))

