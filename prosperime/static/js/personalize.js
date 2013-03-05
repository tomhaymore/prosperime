// jQuery.fun.exists = function(){return this.length>0;}

// initiate arrays for adding personalization
var selected_careers = [];
var selected_jobs = [];

// var checkTask = function(task_id,task_cat) {
// 	var task_selector = "#task-" + task_cat + "-status";
// 	$.ajax({
// 		url: '/tasks/' + task_id + '/status'
// 	}).done(function (data) {
// 		if (data.task.status == "SUCCESS") {
// 			// if task is finished
// 			$(task_selector).html("<span class='success-message'>We have finished processing your " + task_cat + ".</span>")
// 			return 'success';
// 		} else {
// 			// if task is not finished yet
// 			$(task_selector).html("<span class='wait-message'>We are still processing your " + task_cat + ".</span>")
// 			// refresh page in a few seconds
// 			return 'fail';
// 		}
// 	});
// };

$(document).ready(function() {
// 	// check for profile task
// 	if ($("#task-profile-status").exists()) {
// 		// get task id
// 		var profile_task_id = $(this).data('task-id');
// 		var status = checkTask(profile_task_id,'profile');
// 		if (status == 'fail') {
// 			setInterval(checkTask(profile_task_id,'profile'),1000*5);
// 		} 
// 		// setInterval(function() {
// 		// 	$.ajax({
// 		// 		url: profile_task_url,
// 		// 	}).done(function (data) {
// 		// 		if (data.task.status == "SUCCESS") {
// 		// 			// if task is finished
// 		// 			$("#task-profile-status").html("<span class='success-message'>Your profile has finished processing.</span>")
// 		// 		} else {
// 		// 			// if task is not finished yet
// 		// 			$("#task-profile-status").html("<span class='wait-message'>We are still processing your profile.</span>")
// 		// 			// refresh page in a few seconds
// 		// 		}
// 		// 	});
// 		// },1000*10);
// 	}
// 	// check for connections task 
// 	if ($("#task-connections.status").exists()) {
// 		// get task id
// 		var connections_task_id = $(this).data('task-id');
// 		var status = checkTask(connections_task_id,'connections');
// 		if (status == 'fail') {
// 			setInterval(checkTask(connections_task_id,'connections'),1000*10);
// 		} 
// 		// var connections_task_url = '/tasks/' + connections_task_id + '/status'
// 		// setInterval(function() {
// 		// 	$.ajax({
// 		// 		url: profile_task_url,
// 		// 	}).done(function (data) {
// 		// 		if (data.task.status == "SUCCESS") {
// 		// 			// if task is finished
// 		// 			$("#task-connections-status").html("<span class='success-message'>Your profile has finished processing.</span>")
// 		// 		} else {
// 		// 			// if task is not finished yet
// 		// 			$("#task-connections-status").html("<span class='wait-message'>We are still processing your profile.</span>")
// 		// 			// refresh page in a few seconds
// 		// 		}
// 		// 	});
// 		// },1000*10);
// 	}

	$.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken",
                                     $("input[name='csrfmiddlewaretoken']").val());
            }
        }
    });
    $("input#personalize-job-name").typeahead({
    	name: 'jobs',
    	remote: '/careers/jobs?q=%QUERY',
    	limit: 10
    	})
	$("div.personalize-career-entry").click(function() {
		console.log($(this).data('career-id'))
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
			selected_jobs.push($(this).data('job-name'));
		});
		console.log(selected_careers);
		console.log(selected_jobs);
		$.post('/add_personalization/',{'selected_careers':selected_careers,'selected_jobs':selected_jobs}, function(data) {
			if (data == "success") {
				// check to see what page we're on; redirect to next personalization page or back to home
				if window.location == "/personalize/careers/" {
					window.location = '/personalize/jobs';
				} else if (window.location == "/personalize/jobs/") {
					window.location = '/home';	
				}
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