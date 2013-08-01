// $(window).scroll(function(e){ 
//   $el = $('#sidebar'); 
//   if ($(this).scrollTop() > 200 && $el.css('position') != 'fixed'){ 
//     $('#sidebar').css({'position': 'fixed', 'top': '0px'}); 
//   } 
// });

// $(document).ready(function() {
// 	$('.hidden').show();
// 	$('.hidden').mouseover(function() {
	  
// 	(this).show();
//   	}).mouseout(function(){
//     $(this).hide();
//   });
//   $('span').click(function() {
//   		$(this).show();
//   });
	
// });

$(function() {
  	
	$(".ui-widget-overlay").on("click",function() {
		console.log("click overlay");
		$(".ui-dialog").dialog("close");
	});
  	// listen for rollovers on form elements for showig info
	$(".form-input-container").focus(function() {
		var yOffset = $(this).offset().top
		var labelId = $(this).find("input").attr("id");
		$(".form-help[data-target='"+labelId+"']").show().offset({top:yOffset})

	});
	$(".form-input-container").blur(function() {
		var labelId = $(this).find("input").attr("id");
		$(".form-help[data-target='"+labelId+"']").hide();
	});

	$("#search-conversations-button").on("click", function(ev) {

		// var url = $.param({'query':$("input#search-conversations-input").val()});
		var url = "search/" + encodeURIComponent($("input#search-conversations-input").val()) + "/"

		window.location = url;
		// window.App.navigate(url, {trigger:true})
	});
});
