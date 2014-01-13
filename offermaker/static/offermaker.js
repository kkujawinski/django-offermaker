(function($) {

	var input_change_handler = function(form, options) {
        options = options || {};
        var $form = $(form);
        var $inputs = $(':input:not([type=hidden])', $form);
        var $global_error = undefined;
        var break_current_variant = false;

        var error_alert_factory = options.error_alert_factory || function($field, msg) {
            var $error = $('<div class="alert alert-danger alert-dismissable">'
                           + '<button type="button" class="close" '
                           + 'data-dismiss="alert" aria-hidden="true">&times;</button>'
                           + msg + '</div>');
            $('.alert-placeholder', $form).append($error);
            return $error;
        };
        var tooltip_factory = options.tooltip_factory || function($field, msg) {
            var $tooltip = $('<span class="input-group-addon glyphicon glyphicon-info-sign" title="' + msg + '"/>');
            $field.parent().append($tooltip);
            $(function() {
                if ($tooltip.tooltip) {
                    $tooltip.tooltip({'placement': 'bottom', 'container': 'body'});
                }
            });
            return $tooltip
        };
        var msgs = options.msgs || {
            'NO_VARIANTS': 'No matching variants',
            'INFO_ITEMS': 'Available values are: %s.',
            'INFO_FIXED': 'Only available value is %s.',
            'RANGE_left': 'to %2$s',
            'RANGE_right': 'from %1$s',
            'RANGE_both': 'from %1$s to %2$s',
            'AND': ' and '
        };
        var iteration_str = options.iteration_str || function(items) {
            return items.slice(0,-2).concat(items.slice(-2).join(msgs['AND'])).join(', ');
        };
        var msg_factory = options.msg_factory || function(msg_id, params) {
            if (params instanceof Array) {
                return vsprintf(msgs[msg_id], params);
            } else {
                return sprintf(msgs[msg_id], params);
            }
        };
        var CONST = {
            'RANGE_HYP': '-',
            'RANGE_SEP': ' ',
            'ITEMS_SEP': ' ',
        }

        var _decode_items = function(encoded) {
            return encoded.split(CONST.ITEMS_SEP);
        };
        var _encode_items = function(decoded) {
            return decoded.join(CONST.ITEMS_SEP)
        };
        var _decode_ranges = function(encoded) {
            var ranges = encoded.split(CONST.RANGE_SEP);
            var output = [];
            for (var i = 0; i < ranges.length; i++) {
                output[i] = ranges[i].split(CONST.RANGE_HYP);
            }
            return output;
        };
        var _encode_ranges = function(decoded) {
            return $.map(decoded, function(x) {
                return vsprintf('%1$s' + CONST.RANGE_HYP + '%2$s', x);
            }).join(CONST.RANGE_SEP);
        };

        var loader_on = function() {
            if ($global_error) {
                $global_error.remove();
            }
        };
        var loader_off = function() {

        };
        var prepare_data = function() {
            var output = new Object();
            for (var i = 0; i < $inputs.length; i++) {
                output[$inputs[i].name] = $($inputs[i]).val();
            }
            return output;
        };
        var array_has = function(haystack, needle) {
            for (var i = 0; i < haystack.length; i++){
                if (haystack[i] == needle) return i;
            }
            return false;
        }
        var handle_select_field = function($field, field_data) {
            var items = field_data.fixed ? [field_data.fixed] : field_data.items;
            if (items !== undefined && items.length > 0) {
                $('option', $field).each(
                    function() {
                        var $this = $(this);
                        var val = $this.val();
                        if (val !== '' && array_has(items, val) === false) {
                            $this.addClass('om-not-available');
                        }
                    }
                );
            }
        };
        var handle_text_field = function($field, field_data) {
            $field.attr('om-restriction-ranges', '');
            $field.attr('om-restriction-items', '');
            var items = field_data.fixed ? [field_data.fixed] : field_data.items;
            var ranges = field_data.ranges;
            if (items !== undefined && items.length == 1) {
                var $tooltip = tooltip_factory($field, msg_factory('INFO_FIXED', items[0]));
                $field.attr('om-restriction-items', _encode_items(items));
            } else if (items !== undefined && items.length > 1) {
                var items_str = iteration_str(items);
                var $tooltip = tooltip_factory($field, msg_factory('INFO_ITEMS', items_str));
                $field.attr('om-restriction-items', _encode_items(items));
            } else if (ranges !== undefined) {
                var ranges_str = iteration_str($.map(ranges, function(x) {
                    if (x[0] === undefined) { return msg_factory('RANGE_left', x); }
                    if (x[1] === undefined) { return msg_factory('RANGE_right', x); }
                    if (x[0] === x[1] ) { return x[0] }
                    else { return msg_factory('RANGE_both', x); }
                }));
                var $tooltip = tooltip_factory($field, msg_factory('INFO_ITEMS', ranges_str));
                $field.attr('om-restriction-ranges', _encode_ranges(ranges));
            }
            if ($tooltip !== undefined) {
                $tooltip.addClass('om-tooltip');
            }
        };
        var handle_field = function(field_data, break_current_variant, target_empty) {
            if (field_data.field != '__all__') {
                $field = $(':input[name=' + field_data.field + ']');
                var value = field_data.value || field_data.fixed;
                if (value !== undefined && !target_empty) {
                    $field.val(value);
                }
                if (field_data.readonly !== undefined) {
                    // set $field readonly
                }
                if ($field[0].tagName == 'SELECT') {
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
        var global_reset = function() {
            $('.om-global-error').remove();
        }
        var restrictions_reset = function() {
            $('.om-not-available', $form).removeClass('om-not-available');
            $('.om-tooltip', $form).remove();
            break_current_variant = false;
        };
        var _ranges_match = function(ranges, val) {
            var matched = false;
            for (var i = 0; i < ranges.length; i++) {
                var range = ranges[i]
                if (range[0] === undefined || range[0] <= val) {
                    if (range[1] === undefined || val <= range[1]) {
                       matched = true;
                       break;
                    }
                }
            }
            return matched
        };
        var are_restrictions_obeyed = function($target) {
            if ($target[0].tagName == 'SELECT') {
                var $selected = $target.find(':selected');
                return !$selected.hasClass('om-not-available');
            } else if ($target[0].tagName == 'INPUT') {
                var input_type = $target.attr('type').toLowerCase();
                if (input_type == 'text' || input_type == 'number') {
                    val = $target.val();
                    if ($target.attr('om-restriction-items') && $target.attr('om-restriction-items') != '') {
                        var items = _decode_items($target.attr('om-restriction-items'));
                        return array_has(items, val) !== false;
                    } else if ($target.attr('om-restriction-ranges') && $target.attr('om-restriction-ranges') != '') {
                        var ranges = _decode_ranges($target.attr('om-restriction-ranges'));
                        return _ranges_match(ranges, val);
                    }
                }
            }
            return true;
        };
        var are_init_restrictions_obeyed = function($target) {
            if ($target[0].tagName == 'INPUT') {
                var input_type = $target.attr('type').toLowerCase();
                if (input_type == 'text' || input_type == 'number') {
                    val = $target.val();
                    if ($target.attr('om-init-restriction-items') && $target.attr('om-init-restriction-items') != '') {
                        var items = _decode_items($target.attr('om-init-restriction-items'));
                        return array_has(items, val) !== false;
                    } else if ($target.attr('om-init-restriction-ranges')
                                && $target.attr('om-init-restriction-ranges') != '') {
                        var ranges = _decode_ranges($target.attr('om-init-restriction-ranges'));
                        return _ranges_match(ranges, val);
                    }
                }
            }
            return true;
        };
        var $inputs = $(':input', $form);
        var handle_all_field = function(field) {
            if (field.errors) {
                if (field.errors == 'NoMatchingVariants') {
                    var $global_error = error_alert_factory($form, msg_factory('NO_VARIANTS'));
                }
                $global_error.addClass('om-global-error');
            }
        }
        var handler = function(event, success_handler) {
            if (success_handler === undefined) {
                success_handler = function() {};
            }
            if (event && event.target) {
                var $target = $(event.target);
                var target_empty = $target.val() === ""
                if ($target.val() != '' && !are_restrictions_obeyed($target)) {
                    var event_initiator = $target.attr('name')
                    if (are_init_restrictions_obeyed($target)) {
                        if (confirm('Are you sure to break current variant?')) {
                            var break_current_variant = true;
                        }
                    }
                }
            }
            var prepared_data = prepare_data();
            prepared_data['__break_current_variant__'] = break_current_variant;
            prepared_data['__initiator__'] = event_initiator;
            global_reset();
            loader_on();
            $.ajax({
                url: document.location.pathname,
                dataType: 'json',
                data: prepared_data,
                headers: {'X_OFFER_FORM_XHR': '1'},
                success : [function(data) {
                    var __all__ = undefined;
                    for (var i = 0; i < data.length; i++) {
                        if (data[i].field == '__all__') {
                            __all__ = data[i];
                        }
                    }
                    if (__all__) {
                        $inputs.attr('disabled', true);
                        $target.attr('disabled', false);
                        handle_all_field(__all__);
                    } else {
                        $inputs.attr('disabled', false);
                        restrictions_reset();
                        for (var i = 0; i < data.length; i++) {
                            handle_field(data[i], break_current_variant, target_empty);
                        }
                    }
                }],
                complete: [success_handler, loader_off],
                timeout: 40000
            });
        };
        $(function() {
            handler(undefined, function() {
                $inputs.each(function() {
                    var $this = $(this);
                    var restriction_items = $this.attr('om-restriction-items');
                    if (restriction_items) {
                        $this.attr('om-init-restriction-items', restriction_items);
                    }
                    var restriction_ranges = $this.attr('om-restriction-ranges');
                    if (restriction_ranges) {
                        $this.attr('om-init-restriction-ranges', restriction_ranges);
                    }
                });
            });
        });
        var keyup_after_click_handler = function(change_handler) {
            var keyup_occurred = false;
            $inputs.bind('keyup mouseup', function(event) {
                keyup_occurred = true;
            });
            $inputs.bind('change', function(event) {
                if (keyup_occurred) {
                    setTimeout(change_handler(event), 1);
                }
            });
        };
        keyup_after_click_handler(handler);
	};

    $.fn.offer_form = function(options) {
        return this.each(function() {
            input_change_handler(this, options);
        });
    };

})(jQuery);
