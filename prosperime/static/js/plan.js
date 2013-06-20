$(function () {
	$("#go-plan-position-button").click(function() {
		var ideal = $("#plan-positions-search-box").val();
		window.location.href = "?ideal="+ideal;
	});
	$('#plan-positions-search-box').typeahead({
    	name: 'jobs',
    	remote: '/careers/jobs?q=%QUERY',
    	limit: 5
    	});

});