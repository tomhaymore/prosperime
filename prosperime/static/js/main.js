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
});
