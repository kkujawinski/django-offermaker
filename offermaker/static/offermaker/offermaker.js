(function ($) {
    "use strict";

    var input_change_handler = function (form, options) {
        var $form,
            $inputs,
            $global_error,
            break_current_variant,
            ajax_extra_params,
            error_alert_factory,
            tooltip_factory,
            msgs,
            iteration_str,
            msg_factory,
            CONST,
            decode_items,
            encode_items,
            encode_ranges,
            decode_ranges,
            loader_on,
            loader_off,
            prepare_data,
            array_has,
            detect_mobile,
            handle_select_field,
            handle_text_field,
            handle_field,
            global_reset,
            restrictions_reset,
            ranges_match,
            are_restrictions_obeyed,
            are_init_restrictions_obeyed,
            handle_all_field,
            handler,
            keyup_after_click_handler;



        options = options || {};
        $form = $(form);
        $inputs = $(':input:not([type=hidden])', $form);
        $global_error = undefined;

        ajax_extra_params = options.ajax_extra_params || function (params) { return params; };

        if (options.bootstrap3) {
            error_alert_factory = options.error_alert_factory || function (msg) {
                var $error = $('<div class="alert alert-danger alert-dismissable">'
                               + '<button type="button" class="close" '
                               + 'data-dismiss="alert" aria-hidden="true">&times;</button>'
                               + msg + '</div>');
                $('.alert-placeholder', $form).append($error);
                return $error;
            };
            tooltip_factory = options.tooltip_factory || function ($field, msg) {
                var tooltip;
                if (detect_mobile()) {
                    var $tooltip = $('<p class="infotip">' + msg + '</p>');
                    $field.parent().append($tooltip);
                } else {
                    $tooltip = $('<span class="input-group-addon glyphicon glyphicon-info-sign" title="' + msg + '"/>');
                    $field.parent().append($tooltip);
                    $(function () {
                        if ($tooltip.tooltip) {
                            $tooltip.tooltip({'placement': 'bottom', 'container': 'body'});
                        }
                    });
                }
                return $tooltip;
            };
        } else {
            error_alert_factory = options.error_alert_factory || function (msg) {
                var $error = $('<p class="error"><span>' + msg + '</span></p>');
                $('.alert-placeholder', $form).append($error);
                return $error;
            };
            tooltip_factory = options.tooltip_factory || function ($field, msg) {
                var $tooltip = $('<p class="infotip">' + msg + '</p>');
                $field.parent().append($tooltip);
                return $tooltip;
            };
        }

        msgs = options.msgs || {
            'NO_VARIANTS': 'No matching variants',
            'INFO_ITEMS': 'Available values are: %s.',
            'INFO_FIXED': 'Only available value is %s.',
            'RANGE_left': 'to %2$s',
            'RANGE_right': 'from %1$s',
            'RANGE_both': 'from %1$s to %2$s',
            'AND': ' and '
        };
        iteration_str = options.iteration_str || function (items) {
            return items.slice(0, -2).concat(items.slice(-2).join(msgs.AND)).join(', ');
        };
        msg_factory = options.msg_factory || function (msg_id, params) {
            if (params instanceof Array) {
                return vsprintf(msgs[msg_id], params);
            }
            return sprintf(msgs[msg_id], params);
        };
        CONST = {
            'RANGE_HYP': '-',
            'RANGE_SEP': ' ',
            'ITEMS_SEP': ' '
        };

        decode_items = function (encoded) {
            return encoded.split(CONST.ITEMS_SEP);
        };
        encode_items = function (decoded) {
            return decoded.join(CONST.ITEMS_SEP);
        };
        decode_ranges = function (encoded) {
            var i,
                ranges = encoded.split(CONST.RANGE_SEP),
                output = [];
            for (i = 0; i < ranges.length; i += 1) {
                output[i] = ranges[i].split(CONST.RANGE_HYP);
            }
            return output;
        };
        encode_ranges = function (decoded) {
            return $.map(decoded, function (x) {
                return vsprintf('%1$s' + CONST.RANGE_HYP + '%2$s', x);
            }).join(CONST.RANGE_SEP);
        };
        loader_on = function () {
            if ($global_error) {
                $global_error.remove();
            }
        };
        loader_off = function () {
            return undefined;
        };
        prepare_data = function () {
            var i,
                output = {};
            for (i = 0; i < $inputs.length; i += 1) {
                output[$inputs[i].name] = $($inputs[i]).val();
            }
            return output;
        };
        array_has = function (haystack, needle) {
            var i;
            for (i = 0; i < haystack.length; i += 1) {
                if (haystack[i] === needle) { return i; }
            }
            return false;
        };
        detect_mobile = function () {
            return (navigator.userAgent.match(/Android/i)
                    || navigator.userAgent.match(/webOS/i)
                    || navigator.userAgent.match(/iPhone/i)
                    || navigator.userAgent.match(/iPad/i)
                    || navigator.userAgent.match(/iPod/i)
                    || navigator.userAgent.match(/BlackBerry/i)
                    || navigator.userAgent.match(/Windows Phone/i));
        };
        handle_select_field = function ($field, field_data) {
            var $this,
                val,
                items_str,
                $tooltip,
                items = field_data.fixed ? [field_data.fixed] : field_data.items;
            if (items !== undefined && items.length > 0) {
                $('option', $field).each(
                    function () {
                        $this = $(this);
                        val = $this.val();
                        if (val !== '' && array_has(items, val) === false) {
                            $this.addClass('om-not-available');
                        }
                    }
                );
                items_str = iteration_str($.map(items, function(item) {
                    return $('option[value=' + item + ']', $field).html();
                }).sort());
                $tooltip = tooltip_factory($field, msg_factory('INFO_ITEMS', items_str));
                if ($tooltip !== undefined) {
                    $tooltip.addClass('om-tooltip');
                }
            }
        };
        handle_text_field = function ($field, field_data) {
            var items,
                ranges,
                $tooltip,
                items_str,
                ranges_str;

            $field.attr('om-restriction-ranges', '');
            $field.attr('om-restriction-items', '');
            items = field_data.fixed ? [field_data.fixed] : field_data.items;
            ranges = field_data.ranges;
            if (items !== undefined && items.length === 1) {
                $tooltip = tooltip_factory($field, msg_factory('INFO_FIXED', items[0]));
                $field.attr('om-restriction-items', encode_items(items));
            } else if (items !== undefined && items.length > 1) {
                items_str = iteration_str(items);
                $tooltip = tooltip_factory($field, msg_factory('INFO_ITEMS', items_str));
                $field.attr('om-restriction-items', encode_items(items));
            } else if (ranges !== undefined) {
                ranges_str = iteration_str($.map(ranges, function (x) {
                    if (x[0] === undefined || x[0] === null) { return msg_factory('RANGE_left', x); }
                    if (x[1] === undefined || x[1] === null) { return msg_factory('RANGE_right', x); }
                    if (x[0] === x[1]) { return x[0]; }
                    return msg_factory('RANGE_both', x);
                }));
                $tooltip = tooltip_factory($field, msg_factory('INFO_ITEMS', ranges_str));
                $field.attr('om-restriction-ranges', encode_ranges(ranges));
            }
            if ($tooltip !== undefined) {
                $tooltip.addClass('om-tooltip');
            }
        };
        handle_field = function (field_data, break_current_variant, target_empty) {
            var value,
                $field;

            if (field_data.field  !== '__all__') {
                $field = $(':input[name=' + field_data.field + ']');
                value = field_data.value || field_data.fixed;
                if (value !== undefined && !target_empty) {
                    $field.val(value);
                }
                if (field_data.readonly !== undefined) {
                    // set $field readonly
                    return undefined;
                }
                if ($field[0].tagName === 'SELECT') {
                    handle_select_field($field, field_data);
                } else {
                    handle_text_field($field, field_data);
                }
                if (break_current_variant) {
                    if (!are_restrictions_obeyed($field)) {
                        $field.val('');
                    }
                }
            }
        };
        global_reset = function () {
            $('.om-global-error').remove();
        };
        restrictions_reset = function () {
            $('.om-not-available', $form).removeClass('om-not-available');
            $('.om-tooltip', $form).remove();
        };
        ranges_match = function (ranges, val) {
            var i,
                matched = false,
                range;
            for (i = 0; i < ranges.length; i += 1) {
                range = ranges[i];
                if (range[0] === undefined || range[0] <= val) {
                    if (range[1] === undefined || val <= range[1]) {
                        matched = true;
                        break;
                    }
                }
            }
            return matched;
        };
        are_restrictions_obeyed = function ($target) {
            var input_type,
                items,
                ranges,
                $selected,
                val;

            if ($target[0].tagName === 'SELECT') {
                $selected = $target.find(':selected');
                return !$selected.hasClass('om-not-available');
            }
            if ($target[0].tagName === 'INPUT') {
                input_type = $target.attr('type').toLowerCase();
                if (input_type === 'text' || input_type === 'number') {
                    val = $target.val();
                    if ($target.attr('om-restriction-items') && $target.attr('om-restriction-items')  !== '') {
                        items = decode_items($target.attr('om-restriction-items'));
                        return array_has(items, val) !== false;
                    }
                    if ($target.attr('om-restriction-ranges') && $target.attr('om-restriction-ranges')  !== '') {
                        ranges = decode_ranges($target.attr('om-restriction-ranges'));
                        return ranges_match(ranges, val);
                    }
                }
            }
            return true;
        };
        are_init_restrictions_obeyed = function ($target) {
            var input_type,
                items,
                ranges,
                val;

            if ($target[0].tagName === 'INPUT') {
                input_type = $target.attr('type').toLowerCase();
                if (input_type === 'text' || input_type === 'number') {
                    val = $target.val();
                    if ($target.attr('om-init-restriction-items') && $target.attr('om-init-restriction-items')  !== '') {
                        items = decode_items($target.attr('om-init-restriction-items'));
                        return array_has(items, val) !== false;
                    }
                    if ($target.attr('om-init-restriction-ranges')
                                && $target.attr('om-init-restriction-ranges')  !== '') {
                        ranges = decode_ranges($target.attr('om-init-restriction-ranges'));
                        return ranges_match(ranges, val);
                    }
                }
            }
            return true;
        };
        $inputs = $(':input', $form);
        handle_all_field = function (field) {
            if (field.errors) {
                if (field.errors === 'NoMatchingVariants') {
                    $global_error = error_alert_factory(msg_factory('NO_VARIANTS'));
                }
                $global_error.addClass('om-global-error');
            }
        };
        handler = function (event, success_handler) {
            var $target,
                target_empty,
                event_initiator,
                prepared_data,
                break_current_variant = false;

            if (success_handler === undefined) {
                success_handler = function () { return undefined; };
            }
            if (event && event.target) {
                $target = $(event.target);
                target_empty = $target.val() === "";
                if ($target.val()  !== '' && !are_restrictions_obeyed($target)) {
                    event_initiator = $target.attr('name');
                    if (are_init_restrictions_obeyed($target)) {
                        if (confirm('Are you sure to break current variant?')) {
                            break_current_variant = true;
                        }
                    }
                }
            }
            prepared_data = prepare_data();
            /*jslint nomen: true*/
            prepared_data.__break_current_variant__ = break_current_variant;
            prepared_data.__initiator__ = event_initiator;
            /*jslint nomen: false*/
            prepared_data = ajax_extra_params(prepared_data);
            global_reset();
            loader_on();
            $.ajax({
                url: document.location.pathname,
                dataType: 'json',
                data: prepared_data,
                headers: {'X_OFFER_FORM_XHR': '1'},
                success : [function (data) {
                    var i,
                        ALL;
                    for (i = 0; i < data.length; i += 1) {
                        if (data[i].field === '__all__') {
                            ALL = data[i];
                        }
                    }
                    if (ALL) {
                        $inputs.attr('disabled', true);
                        $target.attr('disabled', false);
                        handle_all_field(ALL);
                    } else {
                        $inputs.attr('disabled', false);
                        restrictions_reset();
                        for (i = 0; i < data.length; i += 1) {
                            handle_field(data[i], break_current_variant, target_empty);
                        }
                    }
                }],
                complete: [success_handler, loader_off],
                timeout: 40000
            });
        };
        $(function () {
            handler(undefined, function () {
                $inputs.each(function () {
                    var $this = $(this),
                        restriction_ranges,
                        restriction_items;
                    restriction_items = $this.attr('om-restriction-items');
                    if (restriction_items) {
                        $this.attr('om-init-restriction-items', restriction_items);
                    }
                    restriction_ranges = $this.attr('om-restriction-ranges');
                    if (restriction_ranges) {
                        $this.attr('om-init-restriction-ranges', restriction_ranges);
                    }
                });
            });
        });
        keyup_after_click_handler = function (change_handler) {
            $inputs.bind('change', function (event) {
                setTimeout(change_handler(event), 1);
            });
        };
        keyup_after_click_handler(handler);
    };

    $.fn.offer_form = function (options) {
        return this.each(function () {
            input_change_handler(this, options);
        });
    };

}(jQuery));