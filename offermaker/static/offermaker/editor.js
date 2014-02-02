(function() {
    var $ = jQuery;
    window.offermaker = window.offermaker || {};
    if (window.offermaker.editor !== undefined) return;

    var get_offer_fields_conf = function($fields_div, field) {
        var reverse_map = function(values) {
            var output = {};
            for (var i = 0; i < values.length; i++) {
                output[values[i]['label']] = values[i]['id'];
            }
            return output;
        };
        var array_keys_dict = function(values) {
            var output = {};
            for (var i = 0; i < values.length; i++) {
                output[values[i].value] = values[i];
            }
            return output;
        };
        var get_offer_field_conf = function($field) {
            if ($field[0].tagName == 'SELECT') {
                var items = $.makeArray($('option', $field).map(function() {
                                    var $option = $(this);
                                    return {'value': $option.attr('value'), 'label': $option.html()};
                                }).filter(function() {
                                    return this.value !== '';
                                }));
                return {'type': 'ITEM', 'items': items, 'keys': array_keys_dict(items)};
            } else if ($field.attr('type').toLowerCase() == 'number') {
                var min = $field.attr('min');
                var max = $field.attr('max');
                return {'type': 'RANGE',
                        'min': min === undefined ? undefined : Number(min),
                        'max': max === undefined ? undefined : Number(max)};
            } else {
                return {'type': 'ANYITEM'};
            }
        };
        var offer_field_prefix = field + '__';
        output = {};
        $(':input', $fields_div[0]).each(
            function() {
                var key = $(this).attr('name').replace(offer_field_prefix, '');
                var value = get_offer_field_conf($(this));
                output[key] = value;
            });
        return output;
    };
    var tokens_list_equal = function(tokens1, tokens2) {
        if (tokens1.length != tokens2.length) {
            return false;
        }
        for (var i = 0; i < tokens1.length; i++) {
            if (tokens1[i].value != tokens2[i].value || tokens1[i].label != tokens2[i].label) {
                return false;
            }
        }
        return true;
    }
    var offer_field_factory = function(offer_fields_conf) {
        return function(offer_field_name, the_field_name, the_field_values) {
            the_field_values = the_field_values || '';
            var $input = $('<input type="text" name="' + the_field_name + '" ' +
                           ' value="' + the_field_values + '" id="field__' + the_field_name + '"/>');
            var $input_panel = $('<div class="offermaker_editor_field"><label for="field__' + the_field_name + '">' + offer_field_name +
                                 '</label></div>');
            $input_panel.append($input);
            var the_field_conf = offer_fields_conf[offer_field_name];
            var handlers = {
                'ITEM': function() {
                    $input.tokenfield({
                        autocomplete: {
                            delay: 100,
                            source: function(request, response) {
                                var filtered = the_field_conf.items.filter(function(item) {
                                    return item.label.indexOf(request.term) != -1;
                                })
                                response(filtered);
                            }
                        },
                        showAutocompleteOnFocus: true
                    });
                    $input.change(function(event) {
                        var SEP = ', ';
                        var not_filtered = $input.val().split(SEP);
                        var filtered = not_filtered.filter(function(item) {
                            return the_field_conf.keys[item];
                        }).map(function(item) {
                            return the_field_conf.keys[item];
                        });
                        if (!tokens_list_equal($input.tokenfield('getTokens'), filtered)) {
                            $input.tokenfield('setTokens', filtered);
                        }
                    });
                    // TODO usuwanie elementów spoza listy
                },
                'ANYITEM': function() {
                    $input.tokenfield();
                },
                'RANGE': function() {
                    var MIN = the_field_conf.min;
                    var MAX = the_field_conf.max;
                    $input.tokenfield();
                    var first_item_cmp = function(a, b) {
                        if (a === b) { return 0; }
                        else if (a === undefined) { return -1; }
                        else if (b === undefined) { return 1; }
                        else { return a > b ? 1 : a < b ? -1 : 0; }
                    };
                    var second_item_cmp = function(a, b) {
                        if (a === b) { return 0; }
                        else if (a === undefined) { return 1; }
                        else if (b === undefined) { return -1; }
                        else { return a > b ? 1 : a < b ? -1 : 0 }
                    };
                    var get_normalized_tokens = function(tokens) {
                        var get_numeric = function(value) {
                            value = value.trim();
                            return value === '' ? NaN : Number(value);
                        }
                        var numeric_tokens = [];
                        for (var i = 0; i < tokens.length; i++) {
                            var token = tokens[i];
                            token = token.replace(/\(?([^\)]*)\)?/g, '$1'); // removing external brackets
                            var splitted = token.split(':');
                            if (splitted.length == 1) {
                                value = get_numeric(splitted[0]);
                                if (!isNaN(value)) {
                                    if (first_item_cmp(value, MIN) >= 0 && second_item_cmp(value, MAX) <= 0) {
                                        numeric_tokens.push({min: value, max: value});
                                    }
                                }
                            } else if (splitted.length == 2) {
                                value1 = get_numeric(splitted[0]);
                                value2 = get_numeric(splitted[1]);
                                if (!isNaN(value1) && !isNaN(value2)) {
                                    var min = Math.min(value1, value2);
                                    var max = Math.max(value1, value2);
                                    min = first_item_cmp(min, MIN) < 0 ? MIN : min;
                                    max = second_item_cmp(max, MAX) > 0 ? MAX : max;
                                    if (min <= max && first_item_cmp(min, MIN) >= 0 && second_item_cmp(max, MAX) <= 0) {
                                        numeric_tokens.push({min: min, max: max});
                                    }
                                } else if (value1 !== NaN && splitted[1] === '') {
                                    if (second_item_cmp(value1, MAX) <= 0) {
                                        numeric_tokens.push({min: value1, max: MAX});
                                    }
                                } else if (value2 !== NaN && splitted[0] === '') {
                                    if (first_item_cmp(value2, MIN) >= 0) {
                                        numeric_tokens.push({min: MIN, max: value2});
                                    }
                                }
                            }
                        }
                        return numeric_tokens;
                    };
                    var format_tokens = function(tokens) {
                        return tokens.map(function(token) {
                            var min = String(token.min === undefined ? '' : token.min);
                            var max = String(token.max === undefined ? '' : token.max);
                            var value = min + ':' + max;
                            if (min == max) {
                                return {value: value, label: '(' + min + ')'};
                            } else if (min == '') {
                                return {value: value, label: '(-∞; :' + max + ')'};
                            } else if (max == '') {
                                return {value: value, label: '(' + min + ':∞)'};
                            } else {
                                return {value: value, label: '(' + min + ':' + max + ')'};
                            }
                        });
                    };
                    var sum_ranges = function(ranges) {
                        if (ranges.length == 0) {
                            return ranges;
                        }
                        ranges.sort(function(a, b){
                            var first_cmp = first_item_cmp(a.min, b.min);
                            if (first_cmp == 0){
                                return second_item_cmp(a.max, b.max);
                            } else {
                                return first_cmp;
                            }
                        });
                        var output = [];
                        var saved = ranges[0];
                        for (var i = 1; i < ranges.length; i++) {
                            var st = ranges[i].min;
                            var en = ranges[i].max;
                            if (second_item_cmp(st, saved.max) <= 0) {
                                saved.max = second_item_cmp(saved.max, en) > 0 ? saved.max : en;
                            } else {
                                output.push({min: saved.min, max: saved.max});
                                saved.min = st;
                                saved.max = en;
                            }
                        }
                        if (saved.min !== MIN || saved.max !== MAX) {
                            output.push({min: saved.min, max: saved.max});
                        }
                        return output;
                    }
                    var get_range_tokens = function(tokens) {
                        var normalized_tokens = get_normalized_tokens(tokens);
                        var sorted_tokens = sum_ranges(normalized_tokens);
                        return format_tokens(sorted_tokens);
                    };
                    $input.change(function(event) {
                        //$input.attr('data-tokens-changed', '')
                        var SEP = ', ';
                        var old_val = $input.val();
                        var input_tokens = old_val.split(SEP);
                        var tokens = get_range_tokens(input_tokens);
                        if (!tokens_list_equal($input.tokenfield('getTokens'), tokens)) {
                            $input.tokenfield('setTokens', tokens);
                        }
                    });
                },
            }
            var handler = handlers[the_field_conf.type] || function() {};
            handler();
            return $input_panel;
        }
    };

    var offer_variant_factory = function(offer_field, field_factory) {
        return function(name, params) {
            var $panel = $('<div id="variant_' + offer_field +'_' + name + '" class="offermaker_editor_panel">');
            for (var i = 0; i < params.length; i++) {
                var param = params[i];
                $panel.append(field_factory(param, '__' + param, params[param]));
            }
            return $panel;
        };
    };

    var get_params_in_variants = function(offer) {
        var output = {};
        for (var i = 0; i < offer.variants.length; i++) {
            var group = offer.variants[i];
            for (var j = 0; j < group.length; j++) {
                params = group[j]['params'];
                for (var param in params) {
                    if (params.hasOwnProperty(param)) {
                        output[param] = true;
                    }
                }
            }
        }
        return output;
    };

    var get_global_params = function(offer_fields_types, params_in_variants) {
        output = [];
        for (var param in offer_fields_types) {
            if (offer_fields_types.hasOwnProperty(param)) {
                //if (params_in_variants[param] === undefined) {
                    output.push(param);
                //}
            }
        }
        return output;
    };

    var get_field_values = function(variant) {
        return variant['params'] || {}
    };

    window.offermaker.editor = function(field) {
            var $input = $('input[name='+field+']');
            var $editor_panel = $('#' + field + '_panel');
            var offer = $.parseJSON($input.val());

            var offer_fields_conf = get_offer_fields_conf($('#' + field + '_fields'), field);
            var field_factory = offer_field_factory(offer_fields_conf);
            var variant_factory = offer_variant_factory(field, field_factory);
            var params_in_variants = get_params_in_variants(offer);
            var global_params = get_global_params(offer_fields_conf, params_in_variants);
            $editor_panel.append(variant_factory('default', global_params));

            var $btn = $('<input type="button" onclick="" value="GO!"/>');
            $btn.click(function() {
                $input.val('XXX');
                return false;
            });
            $editor_panel.append($btn);

            // TODO: utworzenie pól
            // TODO: podpięcie zdarzeń i aktualizowanie value w polu
    };
})();