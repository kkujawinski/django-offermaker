(function($) {
	
$(function() {

	var loader_on = function() {
		
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
        $field = $('input[name=' + field_data.field + ']');
        if (field_data.value !== undefined) {
            $field.val(field_data.value);
        }
        if (field_data.readonly !== undefined) {
            // set $field readonly
        }
    };


	var input_change_handler = function(event) {
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
	
	$(':input').change(input_change_handler);
	
	
});
	
})(jQuery);

