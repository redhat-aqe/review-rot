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
		url: 'https://raw.githubusercontent.com/nirzari/review-rot/master/web/js/default-data.json',

		error: function() {
			$('error-message').removeClass('hidden');
		},
		success: function(data) {
			var modified = xhr.getResponseHeader("Last-Modified")
			$('.footer').append(footer_template({
				generated: moment(modified).fromNow()
			}));
			$.each(data, function(key, value) {
				value.pretty_repo = prettify_repo(value.url);
				// Strip off the pull request from the URL to get the base URL of the repo
				value.repo_url = value.url.split('/').slice(0, -2).join('/');
				if (value.updated_time) {
					value.relative_updated_time = moment.unix(value.updated_time).fromNow();
				}
				if (value.title.toUpperCase().indexOf("WIP") == -1) {
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

function prettify_repo(full_repo) {
	// The expression below will parse the URL and manipulate the
	// pathname to remove leading forward slash and extract the
	// repo name from it. Usually the last two parts of pathname
	// are something like:
	//   pull/63 -> GitHub
	//   merge_requests/29 -> GitLab
	//   pull-request/18 -> Pagure
	// So removing the last two parts is a good enough heuristic for
	// determining the repo name.
	return new URL(full_repo).pathname.split('/').filter(x=>x).slice(0, -2).join('/');
}
