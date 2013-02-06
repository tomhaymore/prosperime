$(document).ready(function() {
	window.onhashchange = function() {
		if(window.location.hash == "#network") {
		// $("a#discover-nav-network").click( function() {
			$("a#discover-nav-network").parent("div").addClass('discover-nav-selected').removeClass("discover-nav-unselected");
			$("a#discover-nav-justlikeyou").parent("div").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
			$("div.discover-careers-network").show();
			$("div.discover-careers-justlikeyou").hide();
		};
		if(window.location.hash == "#justlikeyou") {
		// $("a#discover-nav-justlikeyou").click( function() {
			$("a#discover-nav-justlikeyou").parent("div").addClass('discover-nav-selected').removeClass("discover-nav-unselected");
			$("a#discover-nav-network").parent("div").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
			$("div.discover-careers-network").hide();
			$("div.discover-careers-justlikeyou").show();
		};
		if(window.location.hash == "#career-network") {
		// $("a#discover-paths-show-network").click( function() {
			// alert('network');
			$("a#discover-paths-show-network").parent("div").removeClass("discover-nav-unselected").addClass('discover-nav-selected');
			$("a#discover-paths-show-all").parent("div").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
			$("div.discover-paths-network").show();
			$("div.discover-paths-all").hide();
		};
		if(window.location.hash == "#career-community") {
		// $("a#discover-paths-show-all").click( function() {
			// alert('community');
			$("a#discover-paths-show-all").parent("div").removeClass("discover-nav-unselected").addClass('discover-nav-selected');
			$("a#discover-paths-show-network").parent("div").removeClass("discover-nav-selected").addClass('discover-nav-unselected');
			$("div.discover-paths-network").hide();
			$("div.discover-paths-all").show();
		};	
	};
})