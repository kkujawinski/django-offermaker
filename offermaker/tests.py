# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import os

from .tests2._input import OfferMakerCoreInputTest
from .tests2._math import OfferMakerCoreMathTest
from .tests2._offermaker import OfferMakerTest
from .tests2._restrictionset import OfferMakerCoreRestrictionSet
from .tests2._views import OfferMakerViewsTest

if str(os.environ.get('SKIP_FUNCTIONAL', False)).lower() not in ('1', 'true', 'yes'):
    from .tests2._functional import FunctionalTests