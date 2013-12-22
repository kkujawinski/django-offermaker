(function($) {

	var input_change_handler = function(form, options) {
        options = options || {};
        var $form = $(form);
        var $global_error = undefined;

        var error_msg_factory = options.error_msg_factory || function(msg) {
            return '<div class="alert alert-error">'
                + '  <button type="button" class="close" data-dismiss="alert">&times;</button>'
                + msg + '</div>';
        }

        var loader_on = function() {
            if ($global_error) {
                $global_error.remove();
            }
        };
        var loader_off = function() {

        };
        var prepare_data = function() {
            var inputs = $(":input:not([type=hidden])");
            var output = new Object();
            for (i = 0; i < inputs.length; i++) {
                output[inputs[i].name] = $(inputs[i]).val();
            }
            return output;
        };
        var handle_field = function(field_data) {
            if (field_data.field == '__all__') {
                $global_error = $(error_msg_factory('No matching variants'));
                $form.prepend($global_error);
            } else {
                $field = $('input[name=' + field_data.field + ']');
                if (field_data.value !== undefined) {
                    $field.val(field_data.value);
                }
                if (field_data.readonly !== undefined) {
                    // set $field readonly
                }
            }
        };

        return function(event) {
            loader_on();

            $.ajax({
                url: document.location.pathname,
                dataType: 'json',
                data: prepare_data(),
                headers: {'X_OFFER_FORM_XHR': '1'},
                success : [function(data) {
                    for (i = 0; i < data.length; i++) {
                        handle_field(data[i]);
                    }
                    console.log(data);
                }],
                complete: [loader_off],
                timeout: 40000
            });
        };
	};

    $.fn.offer_form = function(options) {
        return this.each(function() {
        	$(this, ':input').change(input_change_handler(this, options));
        });
    };

})(jQuery);