$(document).ready(function() {
	$("a.generic-nav").click(function() {
		
		$("a.generic-nav").removeClass("selected").addClass("unselected");
		$(this).removeClass("unselected").addClass("selected");
		var view = $(this).data('stats-view');
		$("span.stats-holder").each(function() {
			if ($(this).data('stats-view') != view) {
				$(this).hide();
			} else {
				$(this).show();
			}
		});
	});
})