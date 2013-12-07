(function($) {
	
$(function() {

	var loader_on = function() {
		
	};
	var loader_off = function() {
		
	};
	
	var input_change_handler = function(event) {
		loader_on();
		$.ajax({
			url: document.location.pathname,
			dataType: 'json',
			data: {},
			headers: {'X-OfferForm-XHR': '1'},
			success : [function() {
				
			}],
			complete: [loader_off],
			timeout: 40000
		});
		
	};
	
	$(':input').change(input_change_handler);
	
	
});
	
})(jQuery);

