$(document).ready(function() {
	$("a.generic-nav").click(function() {
		var view = $(this).data('stats-view');
		// console.log(view);
		$("a.generic-nav").removeClass("selected").addClass("unselected");
		$(this).removeClass("unselected").addClass("selected");
		var view = $(this).data('stats-view');
		_gaq.push(['_trackEvent','Major','Filter','School',view])
		$("span.stats-holder").each(function() {
			if ($(this).data('stats-view') != view) {
				$(this).hide();
			} else {
				$(this).show();
			}
		});
	});
})