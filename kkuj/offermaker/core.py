# coding=utf-8
from collections import defaultdict

__author__ = 'kamil'


class Restriction(object):

    def __init__(self, restriction_config):
        self.min = None
        self.max = None
        self.items = None
        self.fixed = None

        if isinstance(restriction_config, dict):
            self.min = restriction_config.get('min')
            self.max = restriction_config.get('max')
        elif isinstance(restriction_config, list):
            self.items = restriction_config
        else:
            self.fixed = restriction_config

    def fit(self, value):
        if self.min is not None or self.max is not None:
            if self.min is not None and value < self.min:
                return False
            if self.max is not None and value > self.max:
                return False
        elif self.items is not None:
            if value not in self.items:
                return False
        else:
            if value != self.fixed:
                return False
        return True


class OfferMakerCore(object):

    def __init__(self, offer):
        self.offer = None
        self.values = {}
        self.params_to_variants_groups = {}
        self.variants_groups_to_params = {}

        self._configure(offer)

    def set_values(self, values, initiator=None):
        self.values = values
        self._process()

    def _configure(self, offer):
        def _parse_offer(the_variant):
            """
            Normalizing two ways of defininig groups of variants. 1. with separated groups, 2. with one/default group
            """
            if 'variants' in the_variant:
                output = []
                groups = [the_variant['variants']] if isinstance(the_variant['variants'][0], dict) else the_variant['variants']
                for group in groups:
                    output.append([_parse_offer(variant) for variant in group])
                the_variant['variants'] = output
            if 'params' in the_variant:
                params_output = {}
                for name, value in the_variant['params'].items():
                    params_output[name] = Restriction(value)
                the_variant['params'] = params_output
            return offer

        def _variants_groups(variant):
            """
            Getting set of params, which are touched in groups
            """
            params = set(variant['params'].keys()) if 'params' in variant else set()
            subvariants = None
            if 'variants' in variant and variant['variants']:
                subvariants = {}
                for i, group in enumerate(variant['variants']):
                    group_params = set()
                    for subvariant in group:
                        subvariant_params, subvariant_subvariants = _variants_groups(subvariant)
                        if subvariant_subvariants:
                            for k, v in subvariant_subvariants.items():
                                subvariants['%d-%s' % (i, k)] = v
                                group_params.update(v)
                        group_params.update(set(subvariant_params))
                    subvariants[str(i)] = group_params
            return params, subvariants

        def _invert_multi_value_dict(input):
            output = defaultdict(set)
            for group_name, params in input.items():
                for p in params:
                    output[p].add(group_name)
            return output

        self.offer = _parse_offer(offer)
        import pdb; pdb.set_trace()
        main_params, self.variants_groups_to_params = _variants_groups(self.offer)
        self.variants_groups_to_params['MAIN'] = main_params
        self.params_to_variants_groups = _invert_multi_value_dict(self.variants_groups_to_params)


    def _process(self):
        def _does_params_fit(variant, values):
            """
            Check if given params fits to configured restrictions in variant
            """
            restrictions = variant['params']
            for name, restriction in restrictions.items():
                if name in values:
                    if not restrictions.fit(values[name]):
                        return False
            return True

        def _get_fit_groups(the_variant, values):
            """
            Returns all fit groups (if one of group doesn't fit anymore, it means that value was wrong)
            """
            output = []
            for i, group in enumerate(the_variant['variants']):
                if any((_does_params_fit(variant) for variant in group)):
                    output.append(str(i))
                for variant in group:
                    if 'variants' in variant:
                        output.extend(['%d-%s' (i, vg)  for vg in _get_fit_groups(variant['variants'])])
            return output

        def _get_fit_restrictions(the_variant, values):
            fit_groups = []
            for group in the_variant['variants']:
                fit_variants = []
                for variant in group:
                    if _does_params_fit(variant, values):
                        fit_variants.append(variant)
                    if 'variants' in variant:
                        _get_fit_restrictions(variant)
                fit_groups.append(fit_variants or None)

        if not _does_params_fit(self.offer, self.values):
            raise Exception("Not fits")

        fit_groups = set(['MAIN'] + _get_fit_groups(self.offer, self.values))

        if fit_groups != set(self.variants_groups_to_params.keys()):
            raise Exception("Not fits")








#1. Dla wszystkich grup wyznaczamy listę parametrów, które w nich obowiązują (variants_groups)
#2. Dla każdego z parametrów w requeście wyznaczamy listę grup, które
#ograniczają dany parametr (na podstawie listy z 1.)
#3. Dla każdego z parametrów w requeście wyznaczamy listę wariantów, do których
#"pasują" (uwzględniamy tutaj listę z 1.)
#4. Dla każdego z wariantów z 3., wyznaczamy listę grup, do których należy
#5. Wyznaczamy grupy parametrów w zależności od wspólnych grup
#6. Robimy JOINa 3 z 5 po parametrach
#7. Jeżeli w punkcie 6. powstaną puste grupy, to znaczy, że oferta nie pasuje
#
#W przykładzie 1 jest błąd w pkt. 2, 5 i 6 - powinno być:
#
#2.
#
#MAKE (CARS, PERIOD, RV)
#INSURANCE (CARS)
#AGREEMENT-PERIOD (INTEREST, PERIOD, RV)
#
#5.
#
#CARS: MAKE, INSURANCE
#PERIOD: MAKE, AGREEMENT-PERIOD
#RV: MAKE, AGREEMENT-PERIOD
#INTEREST: AGREEMENT-PERIOD
#
#6.
#
#CARS: (146,355,365,375,387) * (93,103,146) = (146)
#PERIOD: (146,355,365,375,387) * (172,188,204,220,256,266,276,298,318) = () -
#puste!!
#RV: (146,355,365,375,387) * (172,188,204,220,256,266,276,298,318) = () -
#puste!!
#INTEREST: (172,188,204,220,256,266,276,298,318) =
#(172,188,204,220,256,266,276,298,318)
