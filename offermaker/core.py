# coding=utf-8
from copy import deepcopy, copy

__author__ = 'kamil'


class NoMatchingVariantsException(Exception):
    pass

class RangeException(Exception):
    pass

class Range(tuple):

    def __new__(cls, *args):
        if isinstance(args[0], (tuple, list)):
            Range._validate_range_restriction(args[0])
            return tuple.__new__(cls, args[0])
        else:
            Range._validate_range_restriction(args)
            return tuple.__new__(cls, args)


    @staticmethod
    def _validate_range_restriction(restriction):
        if len(restriction) != 2:
            raise RangeException(u"Range restriction must be two element tuple, but %s isn't" % str(restriction))
        else:
            restriction_is_none = [restriction[0] is None, restriction[1] is None]
            if all(restriction_is_none):
                # Empty range restriction, ex. sum of half limited restrictions
                pass
            elif not any(restriction_is_none):
                if not Restriction.has_restriction_the_same_types(restriction):
                    raise RangeException(u"Both side of range restriction must have same type, "
                                         u"but %s isn't" % str(restriction))
                if restriction[0] > restriction[1]:
                    raise RangeException(u"Left side must smaller the right in range restriction, "
                                         u"but %s isn't" % str(restriction))

    @staticmethod
    def first_item_cmp(a, b):
        # None on the first position means minus infinity
        if a is None and b is not None:
            return -1
        elif b is None and a is not None:
            return 1
        return cmp(a, b)

    @staticmethod
    def second_item_cmp(a, b):
        # None on the second position means minus infinity
        if a is None and b is not None:
            return 1
        elif b is None and a is not None:
            return -1
        return cmp(a, b)

    @staticmethod
    def range_cmp(a, b):
        first_cmp = Range.first_item_cmp(a[0], b[0])
        if first_cmp == 0:
            return Range.second_item_cmp(a[1], b[1])
        else:
            return first_cmp

    @staticmethod
    def sets_sum(sets):
        if not sets:
            yield sets
            return

        sets = sorted(sets, cmp=Range.range_cmp)
        saved = list(sets[0])
        for st, en in sets[1:]:
            if Range.second_item_cmp(st, saved[1]) <= 0:
                saved[1] = saved[1] if Range.second_item_cmp(saved[1], en) == 1 else en
            else:
                yield tuple(saved)
                saved[0] = st
                saved[1] = en
        yield tuple(saved)

    def __mul__(self, other):
        first_cmp = Range.first_item_cmp(self[0], other[0])
        second_cmp = Range.second_item_cmp(self[1], other[1])
        output = (self[0] if first_cmp > 0 else other[0], # max(self[0], other[0])
                  self[1] if second_cmp < 0 else other[1]) # min(self[1], other[1])
        try:
            Range._validate_range_restriction(output)
            return output
        except RangeException:
            return None

    @staticmethod
    def sets_product(sets):
        def sets_product_reduce(x, y):
            for i in x:
                for j in y:
                    item = i * j
                    if item is not None:
                        yield item
        return reduce(sets_product_reduce, sets)


class RestrictionSet(dict):

    def __radd__(self, other):
        if isinstance(other, int):
            return RestrictionSet(self)
        return self.__add__(other)

    def __add__(self, other):
        output = RestrictionSet(self)
        for field in other:
            if field in output:
                output[field] += other[field]
            else:
                output[field] = other[field]
        return output


class Restriction(object):

    def __init__(self, field, restriction):
        self.field = field
        self.ranges = None
        self.items = None
        self.fixed = None

        if restriction in (None, [], ()):
            raise Exception(u"Empty restrictions is not allowed, but it's defined for %s" % field)

        if isinstance(restriction, tuple):
            self.ranges = frozenset([Range(restriction)])
        elif isinstance(restriction, (list, set, frozenset)):
            list_of_tuples = [isinstance(r, tuple) for r in restriction]
            if any(list_of_tuples) and not all(list_of_tuples):
                raise Exception(u"Can't mix range restriction with items restriction, unlike %s" % str(restriction))
            if all(list_of_tuples):
                self.ranges = frozenset(Range(x) for x in restriction)
            else:
                if not Restriction.has_restriction_the_same_types(restriction):
                    raise Exception(u"All items in restriction must have same type, but %s isn't" % str(restriction))
                self.items = frozenset(restriction)
        else:
            self.fixed = restriction

    @staticmethod
    def has_restriction_the_same_types(restriction):
        types = set([type(r) for r in restriction])
        return len(types) <= 1

    def match(self, value):
        if self.ranges is not None:
            for start, end in self.ranges:
                if start is not None and value < start:
                    return False
                if end is not None and value > end:
                    return False
        elif self.items is not None:
            if value not in self.items:
                return False
        else:
            if value != self.fixed:
                return False
        return True

    def __add__(self, other):
        if self.field != other.field:
            raise Exception(u"You can add only restrictions of the same field, you trying "
                            u"add %s to %s" % (self.field, other.field))
        if (self.ranges and not other.ranges) or (not self.ranges and other.ranges):
            raise Exception(u"Range restriction can be added only to other range restriction, "
                            u"unlike in '%s'" % self.field)

        # if one is range restriction, both are
        if self.ranges:
            ranges = self.ranges.union(other.ranges)
            ranges = frozenset(Range.sets_sum(ranges))
            output = Restriction(self.field, ranges)
            return output

        # if both fixed restrictions are even, we return the same restriction
        if self.fixed is not None and self.fixed == other.fixed:
            return Restriction(self.field, self.fixed)

        self_items = self.items or frozenset([self.fixed])
        other_items = other.items or frozenset([other.fixed])

        return Restriction(self.field, self_items.union(other_items))

    def __mul__(self, other):
        if self.field != other.field:
            raise Exception(u"You can multiply only restrictions of the same field, you trying "
                            u"multiply %s with %s" % (self.field, other.field))
        if (self.ranges and not other.ranges) or (not self.ranges and other.ranges):
            raise Exception(u"Range restriction can be multiplied only to other range restriction, "
                            u"unlike in '%s'" % self.field)

        if self.ranges:
            ranges = self.ranges.union(other.ranges)
            ranges = frozenset(Range.sets_product(ranges))
            output = Restriction(self.field, ranges)
            return output

        self_items = frozenset([self.fixed]) if self.fixed else self.items
        other_items = frozenset([other.fixed]) if other.fixed else other.items
        output_other = self_items.intersection(other_items)
        if len(output_other) == 1:
            return Restriction(self.field, iter(output_other).next())
        else:
            return Restriction(self.field, output_other)

    def __eq__(self, other):
        if self.items is not None and other.items is not None:
            return self.items == other.items
        elif self.fixed is not None and other.fixed is not None:
            return self.fixed == other.fixed
        elif self.ranges is not None and other.ranges is not None:
            return self.ranges == other.ranges
        return False

    def __repr__(self):
        output = []
        if self.ranges:
            output.append('ranges: %s' % repr(self.ranges))
        if self.items:
            output.append('x in %s' % self.items)
        if self.fixed:
            output.append('x = %s' % repr(self.fixed))
        return ', '.join(output)


class OfferMakerCore(object):

    def __init__(self, form, offer):
        self.form = form
        self.offer = None
        self.values = {}
        self.params_to_variants_groups = {}
        self.variants_groups_to_params = {}
        self.full_matching_variants = {}
        self._configure(deepcopy(offer))

    def get_form_response(self, values, initiator=None):
        return self._process_form_values(values)

    def _configure(self, offer):
        self.offer = OfferMakerCore.parse_offer(offer)
        main_params, self.variants_groups_to_params = OfferMakerCore.get_variants_groups(self.offer)
        self.variants_groups_to_params['MAIN'] = main_params
        self.full_matching_variants = OfferMakerCore.get_matching_variants(self.offer, {})

    def _get_single_value_change(self, form_values, output):
        """
        Returns list of possible values if each input param would be changed
        """
        form_values = copy(form_values)
        fixed_values = dict((k, v.fixed) for k, v in output.items() if v.fixed is not None)
        form_values.update(fixed_values)

        full_outputs = {}
        for param in form_values:
            temp_form_values = copy(form_values)
            del temp_form_values[param]

            param_matching_groups = set(['MAIN'] + OfferMakerCore.get_matching_groups(self.offer, temp_form_values))
            if param_matching_groups != set(self.variants_groups_to_params.keys()):
                continue

            param_matching_variants = OfferMakerCore.get_matching_variants(self.offer, temp_form_values)
            if not param_matching_variants:
                continue

            temp_full_output = OfferMakerCore.sum_grouped_restrictions(param_matching_variants)
            full_outputs[param] = dict((k, v) for k, v in temp_full_output.items() if k in form_values)
        return full_outputs

    def _process_form_values(self, form_values):
        form_values = OfferMakerCore.clean_form_values(self.form(), form_values)
        if not OfferMakerCore.do_variant_params_match(self.offer['params'], form_values):
            raise NoMatchingVariantsException()
        matching_groups = set(['MAIN'] + OfferMakerCore.get_matching_groups(self.offer, form_values))
        if matching_groups != set(self.variants_groups_to_params.keys()):
            raise NoMatchingVariantsException()

        matching_variants = OfferMakerCore.get_matching_variants(self.offer, form_values)
        if not matching_variants:
            raise NoMatchingVariantsException()

        output = OfferMakerCore.sum_grouped_restrictions(matching_variants)
        full_outputs = self._get_single_value_change(form_values, output)
        return self.sum_restrictions([output] + full_outputs.values())

    @staticmethod
    def parse_offer(the_variant, top=True):
        """
        Normalizing two ways of defining groups of variants. 1. with separated groups, 2. with one/default group,
        Parse and validate restrictions
        """
        if 'variants' in the_variant:
            output = []
            if isinstance(the_variant['variants'][0], dict):
                groups = [the_variant['variants']]
            else:
                groups = the_variant['variants']

            if not top and len(groups) > 1:
                raise Exception("Variant groups are allowed only on top level")

            for group in groups:
                output.append([OfferMakerCore.parse_offer(variant, False) for variant in group])

            the_variant['variants'] = output

        params_output = RestrictionSet()
        for name, value in the_variant.get('params', {}).items():
            params_output[name] = Restriction(name, value)
        the_variant['params'] = params_output
        return the_variant

    @staticmethod
    def get_variants_groups(the_variant):
        """
        Getting set of params, which are touched in groups
        """
        params = set(the_variant['params'].keys())
        subvariants = None
        if 'variants' in the_variant and the_variant['variants']:
            subvariants = {}
            for i, group in enumerate(the_variant['variants']):
                group_params = set()
                for subvariant in group:
                    subvariant_params, subvariant_subvariants = OfferMakerCore.get_variants_groups(subvariant)
                    if subvariant_subvariants:
                        for k, v in subvariant_subvariants.items():
                            subvariants['%d-%s' % (i, k)] = v
                            group_params.update(v)
                    group_params.update(set(subvariant_params))
                subvariants[str(i)] = group_params
        return params, subvariants

    @staticmethod
    def clean_form_values(form_object, form_values):
        new_form_values = {}
        for field_name in (f for f, v in form_values.items() if v and f in form_object.fields):
            if field_name[-2:] == '[]':
                input_field_name = field_name[:-2]
                value = form_values.getlist(field_name)
            else:
                input_field_name = field_name
                value = form_values.get(field_name)
            new_form_values[input_field_name] = form_object.fields[input_field_name].clean(value)
        return new_form_values

    @staticmethod
    def do_variant_params_match(params, values):
        """
        Check if given params match to configured restrictions in variant
        """
        for name, restriction in params.items():
            if name in values:
                if not restriction.match(values[name]):
                    return False
        return True

    @staticmethod
    def get_matching_groups(the_variant, values):
        """
        Returns all match groups (if one of group doesn't match anymore, it means that value was wrong)
        """
        output = []
        for i, group in enumerate(the_variant['variants']):
            if any((OfferMakerCore.do_variant_params_match(variant['params'], values) for variant in group)):
                output.append(str(i))
            for variant in group:
                if 'variants' in variant:
                    output.extend(['%d-%s' % (i, vg) for vg in OfferMakerCore.get_matching_groups(variant, values)])
        return output

    @staticmethod
    def get_matching_variants(the_variant, values):
        if not OfferMakerCore.do_variant_params_match(the_variant['params'], values):
            return None

        output = {
            'params': the_variant['params'],
        }
        if 'variants' not in the_variant:
            return output

        new_variants = []
        for group in the_variant['variants']:
            new_group = []
            for variant in group:
                new_variant = OfferMakerCore.get_matching_variants(variant, values)
                if not new_variant:
                    continue
                new_group.append(new_variant)
            if not any(new_group):
                return
            new_variants.append(new_group)

        output['variants'] = new_variants
        return output

    @staticmethod
    def sum_grouped_restrictions(variants):
        grouped_subparams = OfferMakerCore.get_grouped_subparams(variants)
        output = {}
        for restriction_group in OfferMakerCore.get_restrictions_groups(grouped_subparams):
            for name, restriction in restriction_group.items():
                if name in output:
                    output[name] *= restriction
                else:
                    output[name] = restriction
        return output

    @staticmethod
    def sum_restrictions(restrictions_groups):
        output = {}
        for restrictions in restrictions_groups:
            for name, restriction in restrictions.items():
                if name in output:
                    output[name] += restriction
                else:
                    output[name] = restriction
        return output

    @staticmethod
    def get_restrictions_groups(grouped_subparams):
        for x in grouped_subparams:
            yield sum(x)

    @staticmethod
    def get_grouped_subparams(the_variant):
        if the_variant is None:
            import pdb; pdb.set_trace()
        yield (the_variant['params'],)
        if 'variants' in the_variant:
            for group in the_variant['variants']:
                yield (params for variant in group for params in OfferMakerCore.get_all_subparams(variant))

    @staticmethod
    def get_all_subparams(the_variant):
        yield the_variant['params']
        if 'variants' in the_variant:
            for group in the_variant['variants']:
                for variant in group:
                    for params in OfferMakerCore.get_all_subparams(variant):
                        yield params


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


