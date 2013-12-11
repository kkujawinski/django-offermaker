# coding=utf-8
__author__ = 'kamil'

class OfferMakerCore(object):

    def __init__(self, offer):
        self.offer = offer
        self.values = {}

    def set_values(self, values, initiator=None):
        self.values = values
        self._process()

    def _process(self):

        def _variants_groups(variant):
            """
            Getting set of params, which are touched in groups
            """
            params = set(variant['params'].keys()) if 'params' in variant else set()
            subvariants = None
            if 'variants' in variant and variant['variants']:
                subvariants = {}
                grouped_variants = [variant['variants']] if isinstance(variant['variants'][0], dict) else variant['variants']
                for i, group in enumerate(grouped_variants):
                    group_params = set()
                    for subvariant in group:
                        subvariant_params, subvariant_subvariants = _variants_groups(subvariant)
                        if subvariant_subvariants:
                            for k, v in subvariant_subvariants.items():
                                subvariants[str(i) + '-' + k] = v
                                group_params.update(v)
                        group_params.update(set(subvariant_params))
                    subvariants[str(i)] = group_params
            return params, subvariants

        group_params = {
            '0': ['param1', 'param2'],
            '0-0': ['param1', 'param2', 'param3'],
            '0-1': ['param1', 'param2']
        }
        _, variants_groups = _variants_groups(self.offer)
        import pdb; pdb.set_trace()


        pass


#1. Dla wszystkich grup wyznaczamy listę parametrów, które w nich obowiązują
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
