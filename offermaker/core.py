# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy, copy
from functools import reduce

from django.utils import six
from django.core.exceptions import ValidationError

__author__ = 'kamil'


class NoMatchingVariantsException(Exception):
    pass


class RangeException(Exception):
    pass


class Range(tuple):

    def __new__(cls, *args):
        if isinstance(args[0], (tuple, list)):
            Range._validate_range_restriction(args[0])
            x, y = args[0]
        else:
            Range._validate_range_restriction(args)
            x, y = args
        if x is None:
            x = -float("inf")
        if y is None:
            y = float("inf")
        return tuple.__new__(cls, [x, y])

    @staticmethod
    def _validate_range_restriction(restriction):
        if len(restriction) != 2:
            raise RangeException("Range restriction must be two element tuple, but {0} isn't".format(str(restriction)))
        else:
            restriction_is_none = [restriction[0] is None, restriction[1] is None]
            if all(restriction_is_none):
                # Empty range restriction, ex. sum of half limited restrictions
                pass
            elif not any(restriction_is_none):
                if not all(isinstance(x, six.integer_types + (float,)) for x in restriction):
                    raise RangeException("Both side of range restriction must be numeric, "
                                         "but {0} isn't".format(str(restriction)))
                if restriction[0] > restriction[1]:
                    raise RangeException("Left side must smaller the right in range restriction, "
                                         "but {0} isn't".format(str(restriction)))

    @staticmethod
    def sets_sum(sets):
        if not sets:
            yield sets
            return

        sets = sorted(sets)
        saved = list(sets[0])
        for st, en in sets[1:]:
            if st <= saved[1]:
                saved[1] = max(saved[1], en)
            else:
                yield tuple(saved)
                saved[0] = st
                saved[1] = en
        yield tuple(saved)

    @staticmethod
    def sets_diff(sets_x, sets_y):
        if not sets_y:
            yield sets_x
            return

        sets_x = sorted(sets_x)
        sets_y = sorted(sets_y)
        sets_y_iter = iter(x for x in sets_y if Range.is_range(x))
        y_st, y_en = y_range = next(sets_y_iter)

        for x_range in sets_x:
            x_st, x_en = x_range
            try:
                if x_en <= y_st:
                    yield Range(x_st, x_en)
                else:
                    while y_st == y_en or (y_en <= x_st and not Range.is_range(x_range * y_range)):
                        y_st, y_en = y_range = next(sets_y_iter)

                    while y_st <= x_en:
                        if x_st < y_st:
                            yield (x_st, min(x_en, y_st))
                        if y_en <= x_en:
                            x_st = y_en
                        y_st, y_en = y_range = next(sets_y_iter)
                    else:
                        yield x_range
            except StopIteration:
                if x_en > y_en:
                    yield Range(x_st, x_en)

    @staticmethod
    def is_range(x):
        if not isinstance(x, (list, tuple)):
            return False
        if len(x) != 2:
            return False
        if not all(y is None or isinstance(y, six.integer_types + (float,)) for y in x):
            return False
        return x is not None and x[0] != x[1]

    def __mul__(self, other):
        output = (max(self[0], other[0]), min(self[1], other[1]))
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

    def __str__(self):
        x = '' if self[0] == -float("inf") else self[0]
        y = '' if self[1] == float("inf") else self[1]
        return '{0} - {1}'.format(x, y)


class RestrictionSet(dict):

    omc = None

    def __radd__(self, other):
        if isinstance(other, int):
            return RestrictionSet(self)
        return self.__add__(other)

    def __add__(self, other, omc=None):
        output = RestrictionSet(self)
        for field in other:
            if field in output:
                output[field] += other[field]
            elif omc is not None:
                output[field] = omc.full_params.get(field, other[field])
            else:
                output[field] = other[field]
        return output

    def __mul__(self, other):
        output = RestrictionSet()
        for key in self:
            if key in other:
                mul = self[key] * other[key]
                if mul is not None:
                    output[key] = mul
        return output

    def __sub__(self, other):
        output = RestrictionSet()
        for key in self:
            if key in other:
                sub = self[key] - other[key]
                if sub is not None:
                    output[key] = sub
            else:
                output[key] = self[key]
        return output

    @staticmethod
    def intersection_with_rest(rs1, rs2):
        """
        rs1 = {A in x, y, z; B [<3, 5>, <6,7>]}
        rs2 = {B [<2, 6>]; C = k}

        rs1 * rs2 = [
            {A in x, y, z; B [<6,7>]},
            {B [<2, 5>]},
            {B [<5, 6>]; C=k}
        ]
        """
        # if not isinstance(rs1, RestrictionSet) and isinstance(rs1, dict):
        #     rs1 = RestrictionSet(rs1)
        # if not isinstance(rs2, RestrictionSet) and isinstance(rs2, dict):
        #     rs2 = RestrictionSet(rs2)
        output = []
        mul = rs1 * rs2
        left = rs1 - mul
        right = rs2 - mul
        if left:
            output.append(left)
        if mul:
            output.append(mul)
        if right:
            output.append(right)
        return output


    @staticmethod
    def union_with_intersection(rs1, rs2):
        """
        rs1 = {A in x, y, z; B [<3, 5>, <6,7>]}
        rs2 = {B [<2, 6>]; C = k}

        rs1 * rs2 = [
            {A in x, y, z, {B [<2, 5>]}, C=k}
        ]
        """
        # if not isinstance(rs1, RestrictionSet) and isinstance(rs1, dict):
        #     rs1 = RestrictionSet(rs1)
        # if not isinstance(rs2, RestrictionSet) and isinstance(rs2, dict):
        #     rs2 = RestrictionSet(rs2)
        mul_ = rs1 * rs2
        sum_ = rs1 + rs2
        common_keys = set(rs1.keys()).intersection(rs2.keys())
        if not all(k in mul_ for k in common_keys):
            return None
        for k in common_keys:
            del sum_[k]
        sum_.update(mul_)
        return sum_

    def items_to_variants(self):
        is_items_fields = lambda restr: restr.items or (restr.ranges and len(restr.ranges) > 0)
        items_fields = dict((field, restr) for field, restr in self.items() if is_items_fields(restr))
        if not items_fields:
            yield self
            return

        output = RestrictionSet()
        for field, restr in (i for i in self.items() if i[0] not in items_fields):
            output[field] = restr

        def reduce_splitted(x, y):
            for i in x:
                for j in y:
                    i.update(j)  # overriding from previous iteration
                    yield RestrictionSet(i)

        splitted = ([RestrictionSet({f: Restriction(f, i)})
                     for i in r.items or r.ranges] for f, r in items_fields.items())
        varianted = reduce(reduce_splitted, splitted)
        for v in varianted:
            v.update(output)
            yield v

    @staticmethod
    def fields_sorted_key(fields):
        # return lambda item: tuple(item.get(f) for f in fields)
        def _func(item):
            return tuple(item.get(f) for f in fields)
        return _func


class Restriction(object):

    def __init__(self, field, restriction):
        self.field = field
        self.ranges = None
        self.items = None
        self.fixed = None

        if restriction in (None, [], ()):
            raise Exception("Empty restrictions is not allowed, but it's defined for {0}".format(field))

        if isinstance(restriction, tuple):
            self.ranges = frozenset([Range(restriction)])
        elif isinstance(restriction, (list, set, frozenset)):
            list_of_tuples = [isinstance(r, (tuple, list)) for r in restriction]
            if any(list_of_tuples) and not all(list_of_tuples):
                raise Exception("Can't mix range restriction with items restriction, unlike {0}".format(str(restriction)))
            if all(list_of_tuples):
                self.ranges = frozenset(Range(x) for x in restriction)
            else:
                if not Restriction.has_restriction_the_same_types(restriction):
                    raise Exception("All items in restriction must have same type, but {0} isn't".format(str(restriction)))
                if len(restriction) == 1:
                    self.fixed = next(iter(restriction))
                else:
                    self.items = frozenset(restriction)
        else:
            self.fixed = restriction
        if self.ranges and len(self.ranges) == 1:
            x, y = next(iter(self.ranges))
            if x == y:
                self.fixed = x

    @staticmethod
    def has_restriction_the_same_types(restriction):
        types = frozenset((
            'string' if isinstance(r, six.string_types) else type(r)
            for r in restriction
        ))
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
            raise Exception("You can add only restrictions of the same field, you trying "
                            "add {0} to {1}".format(self.field, other.field))
        if (self.ranges and not other.ranges) or (not self.ranges and other.ranges):
            raise Exception("Range restriction can be added only to other range restriction, "
                            "unlike in '{0}'".format(self.field))

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

    def __sub__(self, other):
        if self.field != other.field:
            raise Exception("You can add only restrictions of the same field, you trying "
                            "add {0} to {1}".format(self.field, other.field))
        if (self.ranges and not other.ranges) or (not self.ranges and other.ranges):
            raise Exception("Range restriction can be added only to other range restriction, "
                            "unlike in '{0}'".format(self.field))
        # if one is range restriction, both are
        if self.ranges:
            ranges = frozenset(Range.sets_diff(self.ranges, other.ranges))
            if not ranges:
                return None
            return Restriction(self.field, ranges)

        self_items = self.items or frozenset([self.fixed])
        other_items = other.items or frozenset([other.fixed])
        sub = self_items.difference(other_items)
        if sub:
            return Restriction(self.field, sub)

        return None

    def __mul__(self, other):
        if self.field != other.field:
            raise Exception("You can multiply only restrictions of the same field, you trying "
                            "multiply {0} with {1}".format(self.field, other.field))
        if (self.ranges and not other.ranges) or (not self.ranges and other.ranges):
            raise Exception("Range restriction can be multiplied only to other range restriction, "
                            "unlike in '{0}'".format(self.field))

        if self.ranges:
            ranges = frozenset(Range.sets_product((self.ranges, other.ranges)))
            if not ranges:
                return None
            output = Restriction(self.field, ranges)
            return output

        self_items = frozenset([self.fixed]) if self.fixed else self.items
        other_items = frozenset([other.fixed]) if other.fixed else other.items
        output_other = self_items.intersection(other_items)
        if len(output_other) == 1:
            return Restriction(self.field, next(iter(output_other)))
        elif len(output_other) > 1:
            return Restriction(self.field, output_other)
        else:
            return None

    def __eq__(self, other):
        if other is None:
            return False
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
            output.append('ranges: {0}'.format(repr(self.ranges)))
        if self.items:
            output.append('x in {0}'.format(self.items))
        if self.fixed:
            output.append('x = {0}'.format(repr(self.fixed)))
        return ', '.join(output)

    def format_str(self, object_fields=None):
        if object_fields is None:
            formatter = lambda x: x
        else:
            def formatter(x):
                field = object_fields[self.field]
                if hasattr(field, 'choices'):
                    return dict(field.choices)[x]
                else:
                    return x

        if self.fixed:
            return str(formatter(self.fixed))
        if self.ranges:
            return ', '.join(str(r) for r in sorted(self.ranges))
        if self.items:
            return ', '.join(str(formatter(r)) for r in sorted(self.items))
        return ''

    def __str__(self):
        return self.format_str()

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __cmp__(self, other):
        if other is None:
            return -1
        if self.items or self.fixed:
            x = sorted(self.items or [self.fixed])
            y = sorted(other.items or [other.fixed])
        else:  # range
            x = sorted(self.ranges or [])
            y = sorted(other.ranges or [])

        if y == [None]:
            return -1

        if x < y:
            return -1
        elif x > y:
            return 1
        else:
            return 0


class OfferMakerCore(object):

    def __init__(self, form, offer):
        if isinstance(form, type):
            self.form = form
            self.form_object = form()
        else:
            self.form = form.__class__
            self.form_object = form
        self.offer = None
        self.full_restrictions = {}  # RANGE or ITEM field
        self.groups_to_params = {}
        self.full_matching_variants = {}
        self.full_params = {}
        self._configure(deepcopy(offer))

    def decide(self, values):
        return self.process(
            values,
            single_value_change=False
        )

    def process(self, values, initiator=None, break_variant=False, single_value_change=True):
        form_values = self.clean_form_values(values)
        original_form_values = copy(form_values)

        if break_variant:
            form_values = dict((k, v) for k, v in form_values.items() if k == initiator)

        matching_variants = OfferMakerCore._get_matching_variants(self.offer, form_values)
        if not matching_variants:
            raise NoMatchingVariantsException()

        output = self._sum_grouped_restrictions(matching_variants)

        if break_variant:
            for field, value in ((f, v) for f, v in original_form_values.items() if f != initiator):
                if value != '' and output[field].match(value):
                    form_values[field] = original_form_values[field]
                    matching_variants = OfferMakerCore._get_matching_variants(self.offer, form_values)
                    output = self._sum_grouped_restrictions(matching_variants)

        if single_value_change:
            full_outputs = self._get_single_value_change(form_values, output)
            output = self._sum_restrictions([output] + list(full_outputs.values()))
            output = self._fill_variant_with_full_restrictions(output)
        return output

    def clean_form_values(self, form_values):
        new_form_values = {}
        for field_name in (f for f, v in form_values.items() if v and f in self.form_object.fields):
            if field_name[-2:] == '[]':
                input_field_name = field_name[:-2]
                value = form_values.getlist(field_name)
            else:
                input_field_name = field_name
                value = form_values.get(field_name)
            try:
                new_form_values[input_field_name] = self.form_object.fields[input_field_name].clean(value)
            except ValidationError:
                raise NoMatchingVariantsException()
        return new_form_values

    def offer_summary(self, fields=None):
        def restrict_fields(v):
            for f in list(v.keys()):
                if f not in fields:
                    del v[f]

        def reduce_merge_groups(g1, g2):
            for v1, v2 in ((v1, v2) for v1 in g1 for v2 in g2):
                x = RestrictionSet.union_with_intersection(v1, v2)
                if x is not None:
                    yield x

        groups = OfferMakerCore._get_flatten_groups(self.offer)
        [restrict_fields(v) for g in groups for v in g]
        self._fill_group_variants_with_full_restrictions(groups)
        merged_groups = reduce(reduce_merge_groups, groups)
        varianted_groups = list(OfferMakerCore._items_to_variants(merged_groups))
        self._fill_variants_with_full_restrictions(varianted_groups)
        return sorted(varianted_groups, key=RestrictionSet.fields_sorted_key(fields))

    def get_conflicts(self):
        groups_full_restrictions = OfferMakerCore._get_flatten_groups(self.offer)
        self._fill_group_variants_with_full_restrictions(groups_full_restrictions)
        groups_full_restrictions = groups_full_restrictions[1:]
        output = {}
        for gi, group_x in enumerate(groups_full_restrictions, 1):
            for vi, variant_x in enumerate(group_x, 1):
                conflicted_groups = []
                for gj, group_y in enumerate(groups_full_restrictions, 1):
                    if gj == gi:
                        continue
                    if not group_y:
                        continue
                    expected_params = frozenset(variant_x.keys()).intersection(frozenset(group_y[0].keys()))
                    for variant_y in group_y:
                        if expected_params == frozenset((variant_x * variant_y).keys()):
                            any_matched = True
                            break
                    else:
                        any_matched = False
                    if not any_matched:
                        conflicted_groups.append(str(gj))
                if conflicted_groups:
                    output['{0}-{1}'.format(gi, vi)] = conflicted_groups
        return output

    def _configure(self, offer):
        self.offer = OfferMakerCore._parse_offer(offer)
        self.full_matching_variants = OfferMakerCore._get_matching_variants(self.offer, {})
        groups = OfferMakerCore._get_flatten_groups(self.full_matching_variants)

        self.full_params = sum([sum(x) or RestrictionSet() for x in groups])
        groups_to_params = (frozenset([r for v in g for r in v.keys()]) for g in groups)
        self.groups_to_params = dict([(str(i), g) for i, g in enumerate(groups_to_params)])

        def _full_restriction(name, field):
            if hasattr(field, 'choices'):
                return Restriction(name, [y for y, _ in field.choices if y != ''])
            else:
                return Restriction(name, (getattr(field, 'min_value', None), getattr(field, 'max_value', None)))

        self.full_restrictions = dict([(k, _full_restriction(k, f)) for k, f in self.form_object.fields.items()])

    @staticmethod
    def _parse_offer(the_variant, top=True, is_dict_parse=False):
        """
        Normalizing two ways of defining groups of variants. 1. with separated groups, 2. with one/default group,
        Parse and validate restrictions
        """
        if 'variants' in the_variant and the_variant['variants']:
            output = []
            if isinstance(the_variant['variants'][0], dict):
                groups = [the_variant['variants']]
            else:
                groups = the_variant['variants']

            if not top and len(groups) > 1:
                raise Exception("Variant groups are allowed only on top level")

            for group in groups:
                output.append([OfferMakerCore._parse_offer(variant, top=False, is_dict_parse=is_dict_parse)
                               for variant in group])

            the_variant['variants'] = output

        params_output = RestrictionSet()
        if is_dict_parse:
            for name, value in the_variant.get('params', {}).items():
                params_output[name] = [value] if isinstance(value, tuple) else value
        else:
            for name, value in the_variant.get('params', {}).items():
                params_output[name] = Restriction(name, value)
        the_variant['params'] = params_output
        return the_variant

    @staticmethod
    def parse_offer_dict(the_variant):
        return OfferMakerCore._parse_offer(the_variant, is_dict_parse=True)

    @staticmethod
    def _has_variant_params_match(params, values):
        """
        Check if given params match to configured restrictions in variant
        """
        for name, restriction in params.items():
            if name in values:
                if not restriction.match(values[name]):
                    return False
        return True

    @staticmethod
    def _get_flatten_groups(the_variant):
        output = [[RestrictionSet(the_variant['params'])]]
        if 'variants' in the_variant:
            for group in the_variant['variants']:
                output_group = []
                for variant in group:
                    for subvariant in OfferMakerCore._get_flatten_variant(variant):
                        output_group.append(RestrictionSet(subvariant))
                output.append(output_group)
        return output

    @staticmethod
    def _get_flatten_variant(the_variant):
        the_params = the_variant['params']
        yielded = False
        if 'variants' in the_variant:
            for group in the_variant['variants']:
                for variant in group:
                    for params in OfferMakerCore._get_flatten_variant(variant):
                        the_params_copy = copy(the_params)
                        the_params_copy.update(params)
                        yield the_params_copy
                        yielded = True
        if not yielded:
            yield copy(the_params)

    @staticmethod
    def _get_matching_variants(the_variant, values):
        if not OfferMakerCore._has_variant_params_match(the_variant['params'], values):
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
                new_variant = OfferMakerCore._get_matching_variants(variant, values)
                if not new_variant:
                    continue
                new_group.append(new_variant)
            if not any(new_group):
                return
            new_variants.append(new_group)

        output['variants'] = new_variants
        return output

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

            param_matching_variants = OfferMakerCore._get_matching_variants(self.offer, temp_form_values)
            if not param_matching_variants:
                continue

            temp_full_output = self._sum_grouped_restrictions(param_matching_variants)
            full_outputs[param] = dict((k, v) for k, v in temp_full_output.items() if k == param)
        return full_outputs

    @staticmethod
    def _get_summarized_groups(grouped_subparams):
        return [sum(x) or {} for x in grouped_subparams]

    @staticmethod
    def _get_variants_groups(the_variant):
        """
        Getting set of params, which are touched in groups
        """
        params = frozenset(the_variant['params'].keys())
        subvariants = None
        if 'variants' in the_variant and the_variant['variants']:
            subvariants = {}
            for i, group in enumerate(the_variant['variants']):
                group_params = set()
                for subvariant in group:
                    subvariant_params, subvariant_subvariants = OfferMakerCore._get_variants_groups(subvariant)
                    if subvariant_subvariants:
                        for k, v in subvariant_subvariants.items():
                            subvariants['{0}-{1}'.format(i, k)] = v
                            group_params.update(v)
                    group_params.update(set(subvariant_params))
                subvariants[str(i)] = group_params
        return params, subvariants

    @staticmethod
    def _items_to_variants(variants):
        for variant in variants:
            for new_variant in variant.items_to_variants():
                yield new_variant

    @staticmethod
    def _sum_restrictions(restrictions_groups):
        output = {}
        for restrictions in restrictions_groups:
            for name, restriction in restrictions.items():
                if name in output:
                    output[name] += restriction
                else:
                    output[name] = restriction
        return output

    def _get_grouped_restrictions(self, variants):
        groups = OfferMakerCore._get_flatten_groups(variants)
        summarized_groups = OfferMakerCore._get_summarized_groups(groups)

        for sg in (x for x in summarized_groups if x):
            for i, g in enumerate(groups):
                new_g = OfferMakerCore._restrict_group_by_summarized(copy(g), sg)
                if new_g != g:
                    new_g = OfferMakerCore._restrict_group_by_summarized(copy(g), sg)
                    groups[i] = new_g
                    summarized_groups.append(sum(groups[i]) or RestrictionSet())

        self._fill_group_variants_with_full_restrictions(groups)
        return groups

    def _fill_group_variants_with_full_restrictions(self, groups):
        for i, group in enumerate(groups):
            group_params = self.groups_to_params[str(i)]
            self._fill_variants_with_full_restrictions(group, group_params)

    def _fill_variants_with_full_restrictions(self, group, group_params=None):
        if group_params is None:
            group_params = frozenset(self.full_restrictions.keys())
        for variant in group:
            self._fill_variant_with_full_restrictions(variant, group_params)

    def _fill_variant_with_full_restrictions(self, variant, group_params=None):
        if group_params is None:
            group_params = frozenset(self.full_restrictions.keys())
        for param in group_params.difference(frozenset(variant.keys())):
            variant[param] = self.full_restrictions[param]
        return variant

    def _sum_grouped_restrictions(self, variants):
        groups = self._get_grouped_restrictions(variants)
        return sum([sum(x) or RestrictionSet() for x in groups])

    @staticmethod
    def _restrict_group_by_summarized(group, summarized_group):
        out = [OfferMakerCore._variant_restrict_by_summarized(v, summarized_group) for v in group]
        return [x for x in out if x is not None]

    @staticmethod
    def _variant_restrict_by_summarized(variant, summarized_group):
        for key, restriction in summarized_group.items():
            if key in variant:
                product = variant[key] * restriction
                if product is None:
                    return None
                variant[key] = product
        return variant
