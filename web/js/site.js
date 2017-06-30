$(document).ready(function() {
	var entry_template = Handlebars.compile($("#entry-template").html());
	var footer_template = Handlebars.compile($("#footer-template").html());

	var xhr = $.ajax({
		dataType: 'json',
		cache: false,
		// TODO -- this is temporary while WiP.
		url: 'http://threebean.org/example-reviewrot.json',
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

