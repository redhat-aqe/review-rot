$(document).ready(function() {
	var entry_template = Handlebars.compile($("#entry-template").html());
	var footer_template = Handlebars.compile($("#footer-template").html());

	var xhr = $.ajax({
		dataType: 'json',
		cache: false,

		// A user needs to change this value to get their site to work.
		url: 'https://raw.githubusercontent.com/nirzari/review-rot/396e5a7e878e5ac9779973c7a42ca5de311a6ed5/web/js/default-data.json',

		error: function() {
			$('error-message').removeClass('hidden');
		},
		success: function(data) {
			var modified = xhr.getResponseHeader("Last-Modified")
			$('.footer').append(footer_template({
				generated: moment(modified).fromNow()
			}));
			$.each(data, function(key, value) {
				$('#reviews').append(entry_template(value));
			});
		}
	})
});

