$(document).ready(function() {
	$("a#discover-nav-network").click( function() {
		$("div.discover-careers-network").show();
		$("div.discover-careers-justlikeyou").hide();
	});
	$("a#discover-nav-justlikeyou").click( function() {
		$("div.discover-careers-network").hide();
		$("div.discover-careers-justlikeyou").show();
	});
	$("a#discover-paths-show-network").click( function() {
		$("div.discover-paths-network").show();
		$("div.discover-paths-all").hide();
	});
	$("a#discover-paths-show-all").click( function() {
		$("div.discover-paths-network").hide();
		$("div.discover-paths-all").show();
	})			
})