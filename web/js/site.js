var average_age = function(requests) {
	var total = 0;
	$.each(requests, function(key, value) { total = total + value.time; });
	return {
		age: moment.unix(total / requests.length).fromNow(true),
		// TODO - someday we can make this warning or danger.
		cls: 'default'
	}
}
$(document).ready(function() {
	var entry_template = Handlebars.compile($("#entry-template").html());
	var stats_template = Handlebars.compile($("#stats-template").html());
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
				if (value.title.indexOf("WIP") == -1) {
					$('#reviews').append(entry_template(value));
				} else {
					$('#wip-header').removeClass('hidden');
					$('#wip-reviews').append(entry_template(value));
				}
			});
			$('.page-header').append(stats_template(average_age(data)));
		}
	})
});

