var selected_careers = [];
var selected_jobs = [];

$(document).ready(function() {
	$.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken",
                                     $("input[name='csrfmiddlewaretoken']").val());
            }
        }
    });
	$("div.personalize-career-entry").click(function() {
		$(this).toggleClass("personalize-unselected");
		$(this).toggleClass("personalize-selected");
	});
	$("#personalize-add-job").click(function() {
		// alert($("#personalize-job-name").val());
		var job_name = $("#personalize-job-name").val();
		$("ul#personalize-jobs-list").append("<li data-job-name='"+job_name+"' data-job-id=''>"+job_name+"</li>")
	}); 
	$("#personalize-next-button").click(function()  {
		$("div.personalize-career-entry").each(function() {
			if ($(this).hasClass("personalize-selected")) {
				selected_careers.push($(this).data('career-id'));
			}
		});
		$("ul#personalize-jobs-list li").each(function() {
			selected_jobs.push({'name':$(this).data('job-name'),'id':$(this).data('job-id')});
		});
		console.log(selected_careers);
		console.log(selected_jobs);
		$.post('/add_personalization/',{'selected_careers':selected_careers,'selected_jobs':selected_jobs}, function(data) {
			if (data == "success") {
				window.location = '/home';
			} else {
				var warning = "<div id='messages'>";
				warning += "<ul class='messages'>";
				warning += "<li class='warning'>We were unable to save your preferences. Please try again.</li>";
				warning += "</ul>";
				warning += "</div>";
				$('div.messages-container').append(warning);
			}
		});
	});
})