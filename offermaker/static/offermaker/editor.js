(function () {
    "use strict";

    var $ = jQuery,
        TOKENS_SEP = ', ',

        array_has,
        get_params_for_group,
        get_params_in_variants,
        get_global_params,
        are_tokens_list_equal,
        normalize_range_tokens,
        sum_range_tokens,
        format_range_tokens,
        get_fields_conf,
        get_offer_encoder,
        get_field_factory,
        get_variant_factory,
        get_th_field,
        get_table_factory,
        get_selector_panel_factory,
        get_selected_fields,
        revert_not_selected_fields,
        remove_selected_field,
        get_group_column_operation_factory,
        tables_factory,
        mark_incompatible_variants;


    window.offermaker = window.offermaker || {};
    if (window.offermaker.editor !== undefined) { return; }

    // TOOLS

    array_has = function (haystack, needle) {
        var i;
        for (i = 0; i < haystack.length; i += 1) {
            if (haystack[i] === needle) { return i; }
        }
        return false;
    };

    // OFFER MANAGEMENT

    get_params_for_group = function (group) {
        var j,
            output = {},
            output_list = [],
            param,
            params;
        for (j = 0; j < group.length; j += 1) {
            params = group[j].params;
            for (param in params) {
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

    get_params_in_variants = function (offer) {
        var i,
            j,
            group,
            param,
            params_in_variants = {},
            params;
        for (i = 0; i < offer.variants.length; i += 1) {
            group = offer.variants[i];
            for (j = 0; j < group.length; j += 1) {
                params = group[j].params;
                for (param in params) {
                    if (params.hasOwnProperty(param)) {
                        params_in_variants[param] = true;
                    }
                }
            }
        }
        return params_in_variants;
    };

    get_global_params = function (fields_conf, params_in_variants) {
        var param,
            output = [];
        for (param in fields_conf) {
            if (fields_conf.hasOwnProperty(param)) {
                if (params_in_variants[param] === undefined) {
                    output.push(param);
                }
            }
        }
        return output;
    };

    // TOKENS MANAGEMENT

    are_tokens_list_equal = function (tokens1, tokens2) {
        var i;
        if (tokens1.length !== tokens2.length) {
            return false;
        }
        for (i = 0; i < tokens1.length; i += 1) {
            if (tokens1[i].value !== tokens2[i].value || tokens1[i].label !== tokens2[i].label) {
                return false;
            }
        }
        return true;
    };

    // RANGE MANAGEMENT

    normalize_range_tokens = function (tokens, full_range) {
        var i,
            get_numeric,
            min,
            MIN,
            max,
            MAX,
            numeric_tokens,
            token,
            value,
            value1,
            value2;

        get_numeric = function (value) {
            value = value.trim();
            return value === '' ? NaN : Number(value);
        };
        MIN = full_range.min;
        MAX = full_range.max;
        numeric_tokens = [];
        for (i = 0; i < tokens.length; i += 1) {
            token = tokens[i].replace(/\(?([^\)]*)\)?/g, '$1').split(':'); // removing external brackets
            if (token.length === 1) {
                value = get_numeric(token[0]);
                if (!isNaN(value)) {
                    if (value >= MIN && value <= MAX) { numeric_tokens.push({min: value, max: value}); }
                }
            } else if (token.length === 2) {
                value1 = get_numeric(token[0]);
                value2 = get_numeric(token[1]);
                if (!isNaN(value1) && !isNaN(value2)) {
                    min = Math.max(Math.min(value1, value2), MIN);
                    max = Math.min(Math.max(value1, value2), MAX);
                    if (min <= max && min >= MIN && max <= MAX) { numeric_tokens.push({min: min, max: max}); }
                } else if (!isNaN(value1) && token[1] === '') {
                    if (value1 <= MAX) { numeric_tokens.push({min: value1, max: MAX}); }
                } else if (!isNaN(value2) && token[0] === '') {
                    if (value2 >= MIN) { numeric_tokens.push({min: MIN, max: value2}); }
                }
            }
        }
        return numeric_tokens;
    };

    sum_range_tokens = function (ranges, full_range) {
        var i,
            st,
            en,
            cmp,
            saved,
            output = [];

        if (ranges.length === 0) { return ranges; }
        cmp = function (a, b) { return a > b ? 1 : a < b ? -1 : 0; };
        ranges.sort(function (a, b) {
            var first_cmp = cmp(a.min, b.min);
            return first_cmp === 0 ? cmp(a.max, b.max) : first_cmp;
        });

        saved = ranges[0];
        for (i = 1; i < ranges.length; i += 1) {
            st = ranges[i].min;
            en = ranges[i].max;
            if (st <= saved.max) {
                saved.max = saved.max > en ? saved.max : en;
            } else {
                output.push({min: saved.min, max: saved.max});
                saved.min = st;
                saved.max = en;
            }
        }
        if (saved.min !== full_range.min || saved.max !== full_range.max) {
            output.push({min: saved.min, max: saved.max});
        }
        return output;
    };

    format_range_tokens = function (tokens) {
        return tokens.map(function (token) {
            var min = String(token.min),
                max = String(token.max),
                value;
            value = min + ':' + max;
            if (min === max) {
                return {value: value, label: '(' + min + ')'};
            }
            if (min === '-Infinity') {
                return {value: value, label: '(-∞; :' + max + ')'};
            }
            if (max === 'Infinity') {
                return {value: value, label: '(' + min + ':∞)'};
            }
            return {value: value, label: '(' + min + ':' + max + ')'};
        });
    };

    // HTML MANAGEMENT

    get_fields_conf = function ($fields_div, field) {
        var array_keys_dict,
            get_field_conf,
            field_prefix,
            output_params;

        array_keys_dict = function (values) {
            var i,
                output = {};
            for (i = 0; i < values.length; i += 1) {
                output[values[i].value] = values[i];
            }
            return output;
        };
        get_field_conf = function ($field) {
            if ($field[0].tagName === 'SELECT') {
                return (function () {
                    var items;
                    items = $.makeArray($('option', $field).map(function () {
                        var $option = $(this);
                        return {'value': $option.attr('value'), 'label': $option.html()};
                    }).filter(function () {
                        return this.value !== '';
                    }));
                    return {'type': 'ITEM',
                            'items': items,
                            'keys': array_keys_dict(items),
                            'str2value': function (str) { return str.split(TOKENS_SEP); }
                            };
                }());
            }
            if ($field.attr('type').toLowerCase() === 'number') {
                return (function () {
                    var min,
                        max,
                        output,
                        range_str;

                    min = $field.attr('min');
                    max = $field.attr('max');
                    output = {'type': 'RANGE',
                            'min': min === undefined ? -Infinity : Number(min),
                            'max': max === undefined ? Infinity : Number(max),
                            'str2value': function (str) {
                            return str.split(TOKENS_SEP).map(function (item) {
                                return item.split(':').map(function (item) {
                                    return Number(item);
                                });
                            });
                        }
                        };
                    range_str = [
                        'from <b>' + (min === undefined ? '-∞' : min) + '</b>',
                        'to <b>' + (max === undefined ? '∞' : max) + '</b>' ];
                    if (range_str.length > 0) {
                        output.infotip = '<p class="offermaker_field_info">Values ' + range_str.join(' ') + '</p>';
                    }
                    return output;
                }());
            }
            return {'type': 'ANYITEM', 'str2value': function (str) { return str.split(TOKENS_SEP); }};
        };

        field_prefix = field + '__';
        output_params = {};
        $(':input', $fields_div[0]).each(
            function () {
                var key = $(this).attr('name').replace(field_prefix, '');
                output_params[key] = get_field_conf($(this));
            }
        );
        return output_params;
    };

    get_offer_encoder = function (offer, $offer_field, $editor_panel, fields_conf) {
        return function () {
            // modyfikacja offer
            var field_name,
                field_value,
                new_global_params = {},
                new_variants;
            $('.variant__default :input[name^="default__"]', $editor_panel).each(function () {
                var $this = $(this);
                field_value = $this.val();
                if (field_value !== undefined && field_value !== '') {
                    field_name = $this.attr('data-field');
                    new_global_params[field_name] = fields_conf[field_name].str2value(field_value);
                }
            });
            new_variants = [];
            /*jslint unparam: true*/
            $('.offermaker_table').each(function (group_index, group_item) {
                var new_group = [];
                $('.offermaker_variant', $(group_item)).each(function (variant_index, variant_item) {
                    var new_params = {};
                    $('.offermaker_cell', $(variant_item)).each(function (cell_index, cell_item) {
                        var $the_field,
                            the_field_name,
                            the_field_value;

                        $the_field = $(':input[id^="field__"]', $(cell_item));
                        the_field_name = $the_field.attr('data-field');
                        the_field_value = $the_field.val().trim();
                        if (the_field_value !== '') {
                            new_params[the_field_name] = fields_conf[the_field_name].str2value(the_field_value);
                        }
                    });
                    if (!$.isEmptyObject(new_params)) {
                        new_group.push({params: new_params});
                    }
                });
                if (new_group.length > 0) {
                    new_variants.push(new_group);
                }
            });
            /*jslint unparam: false*/
            offer.params = new_global_params;
            offer.variants = new_variants;
            $offer_field.val(JSON.stringify(offer));
        };
    };

    get_field_factory = function (fields_conf, offer_encoder) {
        return function (field_id, field_name, field_values, cell) {
            var field_conf = fields_conf[field_id],
                $input,
                $input_panel,
                $input_container,
                handler,
                HANDLERS;

            if (Object.prototype.toString.call(field_values) !== '[object Array]') {
                field_values = field_values === undefined ? [] : [field_values];
            }
            $input = $('<input type="text" name="' + field_name + '" id="field__' + field_name + '" ' +
                        'data-field="' + field_id + '"/>');
            if (cell) {
                $input_panel = $('<td class="offermaker_cell offermaker_field field_' + field_id + '"></td>');
                $input_container = $('<div class="offermaker_field_container"></div>');
                $input_panel.append($input_container);
                $input_container.append($input);
            } else {
                $input_panel = $('<div class="offermaker_field field_' + field_id + '"><label for="field__' + field_name + '">' + field_id +
                         '</label></div>');
                $input_panel.append($input);
            }

            HANDLERS = {
                'ITEM': function () {
                    $input.tokenfield({
                        autocomplete: {
                            delay: 100,
                            source: function (request, response) {
                                var filtered = field_conf.items.filter(function (item) {
                                    return item.label.indexOf(request.term) !== -1;
                                });
                                response(filtered);
                            }
                        },
                        showAutocompleteOnFocus: true
                    });
                    $input.change(function () {
                        var filtered = $input.val().split(TOKENS_SEP).filter(function (item) {
                            return field_conf.keys[item];
                        }).map(function (item) {
                            return field_conf.keys[item];
                        });
                        if (!are_tokens_list_equal($input.tokenfield('getTokens'), filtered)) {
                            $input.tokenfield('setTokens', filtered);
                        }

                    });
                    $input.tokenfield('setTokens', field_values.map(function (item) { return field_conf.keys[item]; }));
                    return $input;
                },
                'ANYITEM': function () {
                    $input.tokenfield();
                    $input.tokenfield('setTokens', field_values);
                    return $input;
                },
                'RANGE': function () {
                    var MIN,
                        MAX;

                    MIN = field_conf.min;
                    MAX = field_conf.max;
                    if (!cell && field_conf.infotip) {
                        $input_panel.append(field_conf.infotip);
                    }
                    $input.tokenfield();

                    $input.change(function (event) {
                        var old_val,
                            input_tokens,
                            full_range,
                            tokens;

                        old_val = $input.val();
                        input_tokens = old_val.split(TOKENS_SEP);
                        full_range = {min: MIN, max: MAX};
                        tokens = format_range_tokens(
                            sum_range_tokens(
                                normalize_range_tokens(input_tokens, full_range),
                                full_range
                            )
                        );
                        if (!are_tokens_list_equal($input.tokenfield('getTokens'), tokens)) {
                            $input.tokenfield('setTokens', tokens);
                            if (tokens.length === 0) {
                                $('#' + $input.attr('id') + '-tokenfield').val('');
                            }
                            event.stopImmediatePropagation();
                        }
                    });
                    $input.tokenfield('setTokens', format_range_tokens(
                        field_values.map(
                            function (item) {
                                return { min: item[0] === null ? -Infinity: item[0],
                                         max: item[1] === null ? Infinity : item[1] };
                            }
                        )
                    ));
                    return $input;
                }
            };
            handler = HANDLERS[field_conf.type] || function () { return undefined; };
            $input = handler();
            $input.change(function () {
                offer_encoder();
            });
            return $input_panel;
        };
    };

    get_variant_factory = function (field_factory) {
        return function (name, params, variant, row) {
            var i,
                $panel,
                param,
                $row,
                $td_delete,
                value;

            if (row) {
                $row = $('<tr class="variant__' + name + ' offermaker_variant" class="offermaker_panel">');
                for (i = 0; i < params.length; i += 1) {
                    param = params[i];
                    value = variant.params !== undefined ? variant.params[param] : undefined;
                    $row.append(field_factory(param, name + '__' + param, value, true));
                }
                $td_delete = $('<td class="offermaker_cell_operations"><a href="#" class="deletelink"/></td>');
                $('a', $td_delete).click(function () { $row.remove(); return false; });
                $row.append($td_delete);
                return $row;
            }
            $panel = $('<div class="variant__' + name + '" class="offermaker_panel">');
            for (i = 0; i < params.length; i += 1) {
                param = params[i];
                value = variant.params !== undefined ? variant.params[param] : undefined;
                $panel.append(field_factory(param, name + '__' + param, value));
            }
            return $panel;
        };
    };

    get_th_field = function (param, fields_conf) {
        return $('<th class="field_' + param + '" data-field="' + param + '">' + param +
                (fields_conf[param].infotip || '') + '</th>');
    };

    get_table_factory = function (fields_conf, variant_factory, selector_panel_factory) {
        var param,
            total_fields = 0;
        for (param in fields_conf) {
            if (fields_conf.hasOwnProperty(param)) { total_fields += 1; }
        }
        return function (group, variants) {
            var i,
                $add_row,
                $editor_panel,
                $header_row,
                params,
                $panel,
                $table;

            if (variants.length === 0) { return; }
            params = get_params_for_group(variants);

            $panel = $('<div class="group_' + group + '" class="offermaker_group_panel">');
            $panel.append(selector_panel_factory(group, params));
            $table = $('<table class="offermaker_table"/>');
            $panel.append($table);

            $header_row = $('<tr class="offermaker_header">');
            for (i = 0; i < params.length; i += 1) {
                $header_row.append(get_th_field(params[i], fields_conf));
            }
            $header_row.append('<th/');
            $table.append($header_row);

            for (i = 0; i < variants.length; i += 1) {
                $table.append(variant_factory(group + '-' + (i + 1) , params, variants[i], true));
            }

            $add_row = $('<tr class="offermaker_summary"><td colspan="' + String(total_fields + 1) + '"><a href="#" class="addlink">Add variant</a></td></tr>');
            $editor_panel = $('.editor_selector_panel', $table.parent());
            $table.append($add_row);
            $('a', $add_row).click(function () {
                var new_params = $('th', $table).map(function (index, item) { return $(item).attr('data-field'); });
                variant_factory(group + '-' + i, new_params, {}, true).insertBefore($('tr:last', $table));
                i += 1;
                return false;
            });
            return $panel;
        };
    };

    get_selector_panel_factory = function (fields_conf, field_factory, group_column_operation_factory, $editor_panel) {
        return function (group, selected_params) {
            var checked,
                $delete_group,
                field_id,
                handleCheckboxClick,
                $input,
                param,
                $panel = $('<div class="editor_selector_panel"/>'),
                $selector_field;

            handleCheckboxClick = function (param) {
                $(':input', $selector_field).change(function () {
                    var $this = $(this);
                    if ($this.is(':checked')) {
                        group_column_operation_factory('add', group, param);
                    } else {
                        group_column_operation_factory('remove', group, param);
                    }
                });
            };

            for (param in fields_conf) {
                if (fields_conf.hasOwnProperty(param)) {
                    field_id = 'selector__' + group + '__' + param;
                    checked = array_has(selected_params, param) === false ? '' : ' checked ';
                    $input = $('<input type="checkbox" ' + checked + ' name="' + field_id + '" id="id__' +
                                    field_id + '" data-field="' + param + '"/>');
                    $selector_field = $('<label for="id_' + field_id + '"/>');
                    $selector_field.append($input);
                    $selector_field.append(String(param));
                    handleCheckboxClick(param);
                    $panel.append($selector_field);
                }
            }
            $delete_group = $('<div class="group_deletelink"><a href="#" class="deletelink">Delete group of variant</a></div>');
            $delete_group.click(function () {
                var selected_fields,
                    $global_params_panel = $('.variant__default', $editor_panel);

                $panel.parent().remove();
                group_column_operation_factory('remove', group, param);
                selected_fields = get_selected_fields($editor_panel);
                $.each(get_global_params(fields_conf, selected_fields), function () {
                    var field = String(this);
                    if ($global_params_panel.find('.field_' + field).length === 0) {
                        $global_params_panel.append(field_factory(field, 'default__' + field));
                    }
                });
            });
            $panel.append($delete_group);
            return $panel;
        };
    };

    get_selected_fields = function ($editor_panel) {
        var selected_fields = {};
        $editor_panel.find('.editor_selector_panel :input').each(function () {
            var $this = $(this),
                field;
            if ($this.is(':checked')) {
                field = $this.attr('data-field');
                selected_fields[field] = true;
            }
        });
        return selected_fields;
    };

    revert_not_selected_fields = function (fields_conf, $editor_panel, field_factory) {
        var $global_params_panel = $('.variant__default', $editor_panel),
            selected_fields = get_selected_fields($editor_panel);

        $.each(get_global_params(fields_conf, selected_fields), function () {
            var field = String(this);
            if ($global_params_panel.find('.field_' + field).length === 0) {
                $global_params_panel.append(field_factory(field, 'default__' + field));
            }
        });
    };

    remove_selected_field = function (selected_field, $editor_panel) {
        var $global_params_panel = $('.variant__default', $editor_panel);
        $global_params_panel.find('.field_' + selected_field).remove();
    };

    get_group_column_operation_factory = function (fields_conf, field_factory, $editor_panel) {
        return function (operation, group, field) {
            var $table = $editor_panel.find('.group_' + group + ' table'),
                trs,
                last_index;
            if (operation === 'add') {
                trs = $table.find('tr');
                last_index = trs.length - 1;
                trs.each(function (index) {
                    var $cell,
                        $row = $(this);
                    if (index === last_index) {
                        return undefined;
                    }
                    if (index === 0) {
                        get_th_field(field, fields_conf).insertBefore($('th:last', $row));
                    } else {
                        $cell = field_factory(field, group + '-' + String(index - 1) + '__' + field, undefined, true);
                        $cell.insertBefore($('td:last', $row));
                    }
                });
                remove_selected_field(field, $editor_panel);
            } else if (operation === 'remove') {
                $('td.field_' + field + ', th.field_' + field, $table).remove();
                revert_not_selected_fields(fields_conf, $editor_panel, field_factory);
            }
        };
    };

    tables_factory = function ($editor_panel, table_factory, variant_factory,
                               global_params, offer) {
        var i,
            $add_group_link,
            $table_panel;

        $editor_panel.append(variant_factory('default', global_params, offer));
        for (i = 0; i < offer.variants.length; i += 1) {
            $table_panel = table_factory(String(i + 1), offer.variants[i]);
            if ($table_panel !== undefined) {
                $editor_panel.append($table_panel);
            }
        }

        $add_group_link = $('<div class="group_addlink"><a href="#" class="addlink">Add group of variants</a></div>');
        $('a', $add_group_link).click(function () {
            i += 1;
            $table_panel = table_factory(String(i), {});
            if ($table_panel !== undefined) {
                $table_panel.insertBefore($('div:last', $editor_panel));
            }
            return false;
        });
        $editor_panel.append($add_group_link);
    };

    mark_incompatible_variants = function (conflicted_variants, $editor_panel) {
        $.each(conflicted_variants, function () {
            var $row,
                groups_str,
                $conflicted_variant,
                conflicted_groups_classes,
                $conflicted_groups;

            $row = $('.variant__' + this['variant'], $editor_panel);
            $conflicted_variant = $('<span href="#" class="validation_info variant_conflicted_info"/>');
            groups_str = this['groups'].join(', ');
            $conflicted_variant.prop('title', 'Variant conflicted with following groups of variants: ' + groups_str);
            conflicted_groups_classes = $($.map(this['groups'], function (item) {
                return '.group_' + item;
            }));
            $conflicted_groups = $($.makeArray(conflicted_groups_classes).join(', '), $editor_panel);
            $row.addClass('offermaker_conflicted_variant');

            $conflicted_variant.hover(
                function () {
                    $conflicted_groups.addClass('offermaker_conflicted_group');
                }, function () {
                    $conflicted_groups.removeClass('offermaker_conflicted_group');
                });

            $('.offermaker_variant :input[id^="field__"], a.deletelink', $editor_panel).one('click',
                function () {
                    $('.variant_conflicted_info', $editor_panel).remove();
                    $('.offermaker_conflicted_variant', $editor_panel).removeClass('offermaker_conflicted_variant');
                }
            );

            $('.offermaker_cell_operations', $row).append($conflicted_variant);
        });

    };

    window.offermaker.editor = function (field) {
        var $input,
            $editor_panel,
            offer,
            fields_conf,
            $field_panel,
            global_params,
            offer_encoder,
            field_factory,
            group_column_operation_factory,
            variant_factory,
            selector_panel_factory,
            table_factory;


        $input = $('input[name=' + field + ']');
        $editor_panel = $('#' + field + '_panel');

        offer = JSON.parse($input.val());
        offer = $.isEmptyObject(offer) ? {variants: [], params: {}} : offer;
        fields_conf = get_fields_conf($('#' + field + '_fields'), field);
        global_params = get_global_params(fields_conf, get_params_in_variants(offer));
        offer_encoder = get_offer_encoder(offer, $input, $editor_panel, fields_conf);

        field_factory = get_field_factory(fields_conf, offer_encoder);
        group_column_operation_factory = get_group_column_operation_factory(fields_conf, field_factory, $editor_panel);
        variant_factory = get_variant_factory(field_factory);
        selector_panel_factory = get_selector_panel_factory(fields_conf, field_factory,
                                                                group_column_operation_factory, $editor_panel);
        table_factory = get_table_factory(fields_conf, variant_factory, selector_panel_factory);
        tables_factory($editor_panel, table_factory, variant_factory, global_params, offer);

        $field_panel = $editor_panel.parents('.field-' + field);
        if ($field_panel.hasClass('errors')) {
            $('.errorlist li', $field_panel).each(function () {
                var $this = $(this),
                    splitted,
                    error_data;
                splitted = $this.text().split('|');
                $this.text(splitted[0]);
                if (splitted[1] === 'CONFLICTED-VARIANT') {
                    error_data = JSON.parse(splitted[2] || '[]');
                    mark_incompatible_variants(error_data, $editor_panel);
                }
            });
            console.log('Error validation!');
        }
    };
}());