from collections import defaultdict

__author__ = 'kamil'
from unittest2 import TestCase

from offermaker.core import OfferMakerCore, Restriction, NoMatchingVariantsException


class DjangoFormMockup(object):

    class DjangoFieldMockup(object):

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def clean(self, value):
            return value

    def __init__(self, fields):
        self.fields = {}
        for field in fields:
            params = {}
            if field == 'crediting_period':
                params.update({'choices': [(k, k) for k in ('12', '24', '36', '48')]})
            elif field == 'product':
                params.update({'choices': [(k, k) for k in ('PROD1', 'PROD2', 'PROD3')]})
            elif field == 'contribution':
                params.update({'min_value': 0})
            elif field == 'interest_rate':
                params.update({'min_value': 1, 'max_value': 5})
            self.fields[field] = DjangoFormMockup.DjangoFieldMockup(**params)


class OfferMakerTest(TestCase):

    example_offer_1 = {
        'variants': [
            [{
                'params': {'product': 'PROD1', 'crediting_period': ['24']},
            }, {
                'params': {'product': 'PROD2'},
                'variants': [
                    {'params': {'crediting_period': ['12']}},
                    {'params': {'crediting_period': ['36']}},
                    {'params': {'crediting_period': ['48']}}]
            }, {
                'params': {'product': 'PROD3'},
            }],
            [{
                'params': {'product': 'PROD1'},
                'variants': [
                    {'params': {'contribution': (10, 20), 'interest_rate': (2, 2)}},
                    {'params': {'contribution': (30, 40), 'interest_rate': (4, 4)}}]
            }, {
                'params': {'product': ['PROD2', 'PROD3']},
                'variants': [{
                    'params': {'contribution': (30, 70), 'interest_rate': (5, 5)}
                }]
            }]
        ]
    }

    example_offer_2 = {
        'variants': [
            [{
                'params': {'product': 'PROD3'},
            }, {
                'params': {'product': 'PROD1', 'crediting_period': ['24']},
            }, {
                'params': {'product': 'PROD2'},
                'variants': [
                    {'params': {'crediting_period': ['48']}}]
            }],
            [{
                'params': {'product': 'PROD1'},
                'variants': [
                    {'params': {'contribution': (10, 20)}},
                    {'params': {'interest_rate': (4, 4)}}]
            }, {
                'params': {'product': ['PROD2', 'PROD3']},
                'variants': [{
                    'params': {'contribution': (30, 70), 'interest_rate': (5, 5)}
                }]
            }]
        ]
    }

    class DemoOfferMakerForm(DjangoFormMockup):
        def __init__(self):
            super_init = super(OfferMakerTest.DemoOfferMakerForm, self).__init__
            super_init(['product', 'crediting_period', 'interest_rate', 'contribution'])

    core_1 = None
    core_2 = None

    @classmethod
    def setUp(cls):
        cls.core_1 = OfferMakerCore(cls.DemoOfferMakerForm, cls.example_offer_1)
        cls.core_2 = OfferMakerCore(cls.DemoOfferMakerForm, cls.example_offer_2)

    def test_empty_request(self):
        self.assertEqual(self.core_1.process({}),
                         {'contribution': Restriction('contribution', [(10, 20), (30, 70)]),
                          'crediting_period': Restriction('crediting_period', ['24', '12', '36', '48']),
                          'interest_rate': Restriction('interest_rate', [(2, 2), (4, 4), (5, 5)]),
                          'product': Restriction('product', ['PROD1', 'PROD2', 'PROD3'])})

    def test_filling_with_default_restrictions(self):
        self.assertEqual(self.core_2.process({}),
                         {'contribution': Restriction('contribution', [(0, None)]),
                          'crediting_period': Restriction('crediting_period', ['24', '12', '36', '48']),
                          'interest_rate': Restriction('interest_rate', [(1, 5)]),
                          'product': Restriction('product', ['PROD1', 'PROD2', 'PROD3'])})

    def test_chain_variants_dependency(self):
        self.assertEqual(self.core_1.process({'contribution': 10}),
                         {'contribution': Restriction('contribution', (10, 20)),
                          'crediting_period': Restriction('crediting_period', '24'),
                          'interest_rate': Restriction('interest_rate', (2, 2)),
                          'product': Restriction('product', 'PROD1')})

    def test_breaking_variant(self):
        input_ = {
            'contribution': 10,
            'crediting_period': '24',
            'product': 'PROD2',
            'interest_rate': 2
        }
        self.assertRaises(NoMatchingVariantsException, self.core_1.process, input_)
        self.assertEqual(self.core_1.process(input_, break_variant=True, initiator='product'),
                         {'contribution': Restriction('contribution', (30, 70)),
                          'crediting_period': Restriction('crediting_period', ['12', '36', '48']),
                          'interest_rate': Restriction('interest_rate', (5, 5)),
                          'product': Restriction('product', ['PROD2', 'PROD3'])})