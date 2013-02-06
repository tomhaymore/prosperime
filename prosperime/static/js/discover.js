$(document).ready(function() {
	$("a#discover-nav-network").click( function() {
		$(this).addClass('discover-nav-selected').removeClass("discover-nav-unselected");
		$("a#discover-nav-justlikeyou").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
		$("div.discover-careers-network").show();
		$("div.discover-careers-justlikeyou").hide();
	});
	$("a#discover-nav-justlikeyou").click( function() {
		$(this).addClass('discover-nav-selected').removeClass("discover-nav-unselected");
		$("a#discover-nav-network").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
		$("div.discover-careers-network").hide();
		$("div.discover-careers-justlikeyou").show();
	});
	$("a#discover-paths-show-network").click( function() {
		$(this).addClass('discover-nav-selected').removeClass("discover-nav-unselected");
		$("a#discover-paths-show-all").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
		$("div.discover-paths-network").show();
		$("div.discover-paths-all").hide();
	});
	$("a#discover-paths-show-all").click( function() {
		$(this).addClass('discover-nav-selected').removeClass("discover-nav-unselected");
		$("a#discover-paths-show-network").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
		$("div.discover-paths-network").hide();
		$("div.discover-paths-all").show();
	})			
})