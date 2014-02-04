(function() {
    var $ = jQuery;
    window.offermaker = window.offermaker || {};
    if (window.offermaker.editor !== undefined) return;

    // TOOLS

    var array_has = function(haystack, needle) {
        for (var i = 0; i < haystack.length; i++){
            if (haystack[i] == needle) return i;
        }
        return false;
    };

    // OFFER MANAGEMENT

    var get_params_for_group = function(group) {
        var output = {};
        var output_list = []
        for (var j = 0; j < group.length; j++) {
            params = group[j]['params'];
            for (var param in params) {
                if (params.hasOwnProperty(param)) {
                    if (output[param] === undefined) {
                        output_list.push(param);
                        output[param] = true;
                    }
                }
            }
        }
        return output_list;
    };

    var get_params_in_variants = function(offer) {
        var params_in_variants = {};
        for (var i = 0; i < offer.variants.length; i++) {
            var group = offer.variants[i];
            for (var j = 0; j < group.length; j++) {
                params = group[j]['params'];
                for (var param in params) {
                    if (params.hasOwnProperty(param)) {
                        params_in_variants[param] = true;
                    }
                }
            }
        }
        return params_in_variants;
    };

    var get_global_params = function(fields_conf, params_in_variants) {
        var output = [];
        for (var param in fields_conf) {
            if (fields_conf.hasOwnProperty(param)) {
                if (params_in_variants[param] === undefined) {
                    output.push(param);
                }
            }
        }
        return output;
    };

    // TOKENS MANAGEMENT

    var are_tokens_list_equal = function(tokens1, tokens2) {
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

    // RANGE MANAGEMENT

    var normalize_range_tokens = function(tokens, full_range) {
        var get_numeric = function(value) {
            value = value.trim();
            return value === '' ? NaN : Number(value);
        }
        var MIN = full_range.min;
        var MAX = full_range.max;
        var numeric_tokens = [];
        for (var i = 0; i < tokens.length; i++) {
            var token = tokens[i].replace(/\(?([^\)]*)\)?/g, '$1').split(':'); // removing external brackets
            if (token.length == 1) {
                value = get_numeric(token[0]);
                if (!isNaN(value)) {
                    if (value >= MIN && value <= MAX) { numeric_tokens.push({min: value, max: value}); }
                }
            } else if (token.length == 2) {
                value1 = get_numeric(token[0]);
                value2 = get_numeric(token[1]);
                if (!isNaN(value1) && !isNaN(value2)) {
                    var min = Math.max(Math.min(value1, value2), MIN);
                    var max = Math.min(Math.max(value1, value2), MAX);
                    if (min <= max && min >= MIN && max <= MAX) { numeric_tokens.push({min: min, max: max}); }
                } else if (value1 !== NaN && token[1] === '') {
                    if (value1 <= MAX) { numeric_tokens.push({min: value1, max: MAX}); }
                } else if (value2 !== NaN && token[0] === '') {
                    if (value2 >= MIN) { numeric_tokens.push({min: MIN, max: value2}); }
                }
            }
        }
        return numeric_tokens;
    };

    var sum_range_tokens = function(ranges, full_range) {
        if (ranges.length == 0) { return ranges; }
        var cmp = function(a, b) { return a > b ? 1 : a < b ? -1 : 0 };
        ranges.sort(function(a, b) {
            var first_cmp = cmp(a.min, b.min);
            if (first_cmp == 0){ return cmp(a.max, b.max);
            } else { return first_cmp; }
        });
        var output = [];
        var saved = ranges[0];
        for (var i = 1; i < ranges.length; i++) {
            var st = ranges[i].min;
            var en = ranges[i].max;
            if (st <= saved.max) {
                saved.max = saved.max > en ? saved.max : en;
            } else {
                output.push({min: saved.min, max: saved.max});
                saved.min = st;
                saved.max = en;
            }
        }
        if (full_range || saved.min !== MIN || saved.max !== MAX) {
            output.push({min: saved.min, max: saved.max});
        }
        return output;
    };

    var format_range_tokens = function(tokens) {
        return tokens.map(function(token) {
            var min = String(token.min);
            var max = String(token.max);
            var value = min + ':' + max;
            if (min == max) {
                return {value: value, label: '(' + min + ')'};
            } else if (min == '-Infinity') {
                return {value: value, label: '(-∞; :' + max + ')'};
            } else if (max == 'Infinity') {
                return {value: value, label: '(' + min + ':∞)'};
            } else {
                return {value: value, label: '(' + min + ':' + max + ')'};
            }
        });
    };

    // HTML MANAGEMENT

    var get_fields_conf = function($fields_div, field) {
        var array_keys_dict = function(values) {
            var output = {};
            for (var i = 0; i < values.length; i++) {
                output[values[i].value] = values[i];
            }
            return output;
        };
        var get_field_conf = function($field) {
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
                var output = {'type': 'RANGE',
                        'min': min === undefined ? -Infinity : Number(min),
                        'max': max === undefined ? Infinity : Number(max)};
                var range_str = [
                    'from <b>' + (min === undefined ? '-∞': min) + '</b>',
                    'to <b>' + (max === undefined ? '∞': max) + '</b>' ];
                if (range_str.length > 0) {
                    output.infotip = '<p class="offermaker_editor_field_info">Values ' + range_str.join(' ') + '</p>';
                }
                return output;
            } else {
                return {'type': 'ANYITEM'};
            }
        };
        var field_prefix = field + '__';
        var output = {};
        $(':input', $fields_div[0]).each(
            function() {
                var key = $(this).attr('name').replace(field_prefix, '');
                output[key] = get_field_conf($(this));
            });
        return output;
    };

    var get_field_factory = function(fields_conf) {
        return function(field_id, field_name, field_values, cell) {
            var field_conf = fields_conf[field_id];
            if (Object.prototype.toString.call(field_values) !== '[object Array]') {
                field_values = field_values === undefined ? [] : [field_values];
            }

            var $input = $('<input type="text" name="' + field_name + '" id="field__' + field_name + '"/>');
            if (cell) {
                var $input_panel = $('<td class="offermaker_editor_field field_' + field_id + '"></td>');
                var $input_container = $('<div class="offermaker_editor_field_container"></div>');
                $input_panel.append($input_container);
                $input_container.append($input);
            } else {
                var $input_panel = $('<div class="offermaker_editor_field field_' + field_id + '"><label for="field__' + field_name + '">' + field_id +
                         '</label></div>');
                $input_panel.append($input);
            }

            var HANDLERS = {
                'ITEM': function() {
                    $input.tokenfield({
                        autocomplete: {
                            delay: 100,
                            source: function(request, response) {
                                var filtered = field_conf.items.filter(function(item) {
                                    return item.label.indexOf(request.term) != -1;
                                });
                                response(filtered);
                            }
                        },
                        showAutocompleteOnFocus: true
                    });
                    $input.change(function(event) {
                        var SEP = ', ';
                        var not_filtered = $input.val().split(SEP);
                        var filtered = not_filtered.filter(function(item) {
                            return field_conf.keys[item];
                        }).map(function(item) {
                            return field_conf.keys[item];
                        });
                        if (!are_tokens_list_equal($input.tokenfield('getTokens'), filtered)) {
                            $input.tokenfield('setTokens', filtered);
                        }
                    });
                    $input.tokenfield('setTokens', field_values.map(function(item) { return field_conf.keys[item]; }));
                },
                'ANYITEM': function() {
                    $input.tokenfield();
                },
                'RANGE': function() {
                    var MIN = field_conf.min;
                    var MAX = field_conf.max;
                    if (!cell && field_conf.infotip) {
                        $input_panel.append(field_conf.infotip);
                    }
                    $input.tokenfield();

                    $input.change(function(event) {
                        var SEP = ', ';
                        var old_val = $input.val();
                        var input_tokens = old_val.split(SEP);
                        var full_range = {min: MIN, max: MAX}
                        var tokens = format_range_tokens(
                                        sum_range_tokens(
                                            normalize_range_tokens(input_tokens, full_range),
                                            full_range));
                        if (!are_tokens_list_equal($input.tokenfield('getTokens'), tokens)) {
                            $input.tokenfield('setTokens', tokens);
                            if (tokens.length == 0) {
                                $('#' + $input.attr('id') + '-tokenfield').val('');
                            }
                        }
                    });
                    $input.tokenfield('setTokens', format_range_tokens(
                                                       field_values.map(
                                                           function(item) { return { min: item[0], max: item[1] }}
                                                           )));
                }
            }
            var handler = HANDLERS[field_conf.type] || function() {};
            handler();
            return $input_panel;
        }
    };

    var get_variant_factory = function(field_name, field_factory) {
        return function(name, params, variant, row) {
            if (row) {
                var $row = $('<tr class="variant_' + field_name +'_' + name + '" class="offermaker_editor_panel">');
                for (var i = 0; i < params.length; i++) {
                    var param = params[i];
                    var value = variant.params !== undefined ? variant.params[param] : undefined;
                    $row.append(field_factory(param, name + '__' + param, value, true));
                }
                return $row;
            } else {
                var $panel = $('<div class="variant_' + field_name +'_' + name + '" class="offermaker_editor_panel">');
                for (var i = 0; i < params.length; i++) {
                    var param = params[i];
                    var value = variant.params !== undefined ? variant.params[param] : undefined;
                    $panel.append(field_factory(param, name + '__' + param, value));
                }
                return $panel;
            }
        };
    };

    var get_th_field = function(param, fields_conf) {
        return $('<th class="field_' + param + '">' + param + (fields_conf[param].infotip || '') + '</th>')
    };

    var get_table_factory = function(fields_conf, variant_factory, selector_panel_factory) {
        return function(group, variants) {
            if (variants.length == 0) { return; }
            var params = get_params_for_group(variants);

            var $panel = $('<div class="group_' + group + '_panel" class="offermaker_group_panel">');
            $panel.append(selector_panel_factory(group, params));
            var $table = $('<table class="offermaker_editor_table"/>');
            $panel.append($table);

            var $header_row = $('<tr>');
            for (var i = 0; i < params.length; i++) {
                $header_row.append(get_th_field(params[i], fields_conf));
            }
            $table.append($header_row);

            for (var i = 0; i < variants.length; i++) {
                var $row = variant_factory(group + '__' + i, params, variants[i], true);
                $table.append($row);
            }
            return $panel;
        };
    };

    var get_selector_panel_factory = function(fields_conf, group_column_operation_factory) {
        return function(group, selected_params) {
            var $panel = $('<div class="editor_selector_panel"/>');
            for (var param in fields_conf) {
                if (fields_conf.hasOwnProperty(param)) {
                    var field_conf = fields_conf[param];
                    var field_id = 'selector__' + group + '__' + param;
                    var checked = array_has(selected_params, param) === false ? '' : ' checked ';
                    var $input = $('<input type="checkbox" ' + checked + ' name="' + field_id + '" id="id__' +
                                    field_id + '"/>');
                    var $selector_field = $('<label for="id_' + field_id + '"/>');
                    $selector_field.append($input);
                    $selector_field.append(String(param));
                    (function(param) {
                        $(':input', $selector_field).change(function() {
                            var $this = $(this);
                            if ($this.is(':checked')) {
                                group_column_operation_factory('add', group, param);
                            } else {
                                group_column_operation_factory('remove', group, param);
                            }

                        });
                    })(param);
                    $panel.append($selector_field);
                }
            }
            return $panel;
        };
    };

    var get_group_column_operation_factory = function(fields_conf, field_factory, $editor_panel) {
        return function(operation, group, field) {
            var $table = $editor_panel.find('.group_' + group + '_panel table');
            var $global_params_panel = $('.variant_offer_default', $editor_panel);
            if (operation === 'add') {
                $table.find('tr').each(function(index) {
                    var $row = $(this);
                    if (index == 0) {
                        $row.append(get_th_field(field, fields_conf));
                    } else {
                        var $cell = field_factory(field, group + '__' + String(index - 1) + '__' + field, undefined, true);
                        $row.append($cell);
                    }
                });
                $global_params_panel.find('.field_' + field).remove();
            } else if (operation === 'remove') {
                $table.find('td.field_' + field + ', th.field_' + field).remove();
                var field_regex = /selector__[\d+]__(.+)/;
                var selected_fields = {};
                $editor_panel.find('.editor_selector_panel :input').each(function() {
                    var $this = $(this);
                    if ($this.is(':checked')) {
                        var field = $this.prop('name').replace(field_regex, '$1');
                        selected_fields[field] = true;
                    }
                });
                $.each(get_global_params(fields_conf, selected_fields), function() {
                    var field = String(this);
                    if ($global_params_panel.find('.field_' + field).length == 0) {
                        $global_params_panel.append(field_factory(field, 'default__' + field));
                    }
                });
            }
        };
    };

    window.offermaker.editor = function(field) {
        var $input = $('input[name='+field+']');
        var $editor_panel = $('#' + field + '_panel');

        var offer = $.parseJSON($input.val());
        var fields_conf = get_fields_conf($('#' + field + '_fields'), field);
        var global_params = get_global_params(fields_conf, get_params_in_variants(offer));

        var field_factory = get_field_factory(fields_conf);
        var group_column_operation_factory = get_group_column_operation_factory(fields_conf, field_factory, $editor_panel);
        var variant_factory = get_variant_factory(field, field_factory);
        var selector_panel_factory = get_selector_panel_factory(fields_conf, group_column_operation_factory);
        var table_factory = get_table_factory(fields_conf, variant_factory, selector_panel_factory);

        $editor_panel.append(variant_factory('default', global_params, offer));
        for (var i = 0; i < offer.variants.length; i++) {
            var $table_panel = table_factory(String(i), offer.variants[i]);
            if ($table_panel !== undefined) {
                $editor_panel.append($table_panel);
            }
        }

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