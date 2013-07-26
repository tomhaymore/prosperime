$(function() {
	// listen for rollovers on form elements for showig info
	$(".form-input-container").hover(function() {
		var yOffset = $(this).offset().top
		var labelId = $(this).find("input").attr("id");
		$(".form-help[data-target='"+labelId+"']").show().offset({top:yOffset})

	},function() {
		var labelId = $(this).find("input").attr("id");
		$(".form-help[data-target='"+labelId+"']").hide();
	});

});