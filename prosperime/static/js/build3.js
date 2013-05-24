	/* AJAX Calls */
	var save = function() {

		// Remove any previous error messages
		removeAllMessages()

		// Animate to show clicked
		$('#build-save-button').fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100)

		// Get Path Info
		var title = $('.build-header-name').html()

		// Check if they left the title box open, set
		//	title accordingly
		if ($('.build-input').length > 0) {
			if ($('.build-input').val().length > 0)
				title = $('.build-input').val()
			else 
				title = "Untitled"
		}

		// Require a name for path
		if (title == "Untitled") {
			displayErrorMessage("You haven't named this path yet! To do so, click on 'Untitled'")
			return false;
		}

		var position_ids = []
		for (var g = 0; g < path_data.length; g++) {
			position_ids.push(path_data[g]["ideal_id"])
		}


		console.log("Pre-save: [title:" + title + "] [position_ids:" + position_ids + "] [path_id:" + path_id + ']')

		// // Post to DB
		// $.post("/careers/saveBuildPath/",
		// 	{'title':title, 'position_ids':position_ids, 'path_id':path_id, 'csrfmiddlewaretoken':"csrf_token"},
		// 	function(response) {
		// 		if (response["result"] == "success") {
		// 			console.log("Success")
		// 			$('.save-button').html("Saved")

		// 			// // Now that saved, cab be deleted
		// 			// var delete_html = "<div id='delete-button'  onclick='delete_path()'>Delete</div>"
		// 			// $('#delete-button-container').html(delete_html)

		// 			$('#comments-container').css("visibility", "visible").append("No comments yet")

		// 			// Set new path id
		// 			path_id = response["path_id"]
		// 			console.log("new path id set to : " + path_id)
		// 		} else {
		// 			console.log("Failure: " + response["errors"])
		// 		}
		// 	},
		// 	"json"
		// )

	};

	/* AJAX call to get options given start pos_id and current ideal_id */
	var getOptions = function(ideal_id) {
		jQuery.ajaxSetup({async:false});
		var return_value = null
		$.get("/careers/getNextBuildStep/", {'id':ideal_id,'pos_id':start_pos_id}, function(response) {
			options = response
		}, "json");

		jQuery.ajaxSetup({async:true})
		return options
	};

	/************/
	/* Handlers */
	/************/

	/* Event Handler for Selecting a New Position */
	var selectNewPosition = function() {

		// Get Selected element
		var selected = $('#build-new-position-select').find(":selected")

		// Clean Canvas
		cleanCanvas()

		// Modify CSS of box and hide search box
		$('#new-position-box').removeClass("new-position").removeClass("high-padding").addClass("current-position").addClass("medium-padding").empty().append(selected.data("title")+"</br>"+selected.data("entity_name")).unbind("click").css("background-color", "rgba(41,128,185,1)").after("<div class='new-position position-box high-padding'>New Position</div>").removeAttr("id").data("index", current_positions_javascript.length)
		$('.new-position').attr('id', 'new-position-box')
		$('#build-new-position-select').css("visibility", "hidden")
		$('#new-position-box').click(searchStartingPositions)

		var position = {'ideal_id':selected.data("ideal_id"), 'pos_id':selected.data("pos_id"), "title":selected.data("title"), 'entity_name':selected.data("entity_name")}
		drawPathBox(position, x_start, color_map[1], true, -1)

		// then change the class of the current and insert a new guy after

		addBackButton(x_start)
		start_pos_id = selected.data("pos_id")
		enableSave()

		// finalmente, add to currentpositions, so that can be re-clicked
		current_positions_javascript.push(position)

		// Render options
		getAndRenderOptions(selected.data("ideal_id"))
	};

	/* Hover for info-box entities, displays description */
	var entityOver = function(el) {
		var description = options[$(el).data("option-index")]['entities'][$(el).data("entity-index")]['description']
		if (description == null) description = "Sorry, no description available."
		$(el).append("<div class='info-box-entity-description'>"+description+"</div>")
	};

	/* Hover for info-box entities, removes all descriptions */
	var entityOut = function(el) {
		$('.info-box-entity-description').each(function() {
			$(this).remove();
		});
	};

	/* Animates out other options, moves clicked to center, and
			gets new options from its ideal_id */
	var optionClicked = function(index) {

		// Get clicked option and its indices
		var clicked_option = null
		var selected_index = null
		for (var z = 0; z < option_data.length; z++) {
			if (option_data[z]['index'] == index) {
				clicked_option = option_data[z]
				selected_index = z
				break;
			}
		}

		console.log(clicked_option)

		// Get ideal_id
		var ideal_id = options[index]['ideal_id']

		// Fade out other options
		removeOptions(selected_index)

		// Fade out next arrows
		removeShufflers()

		// Unbind events
		unbind_events(paper.getById(clicked_option["box_id"]))

		// Move and animate chosen to the middle
		paper.getById(clicked_option["box_id"]).animate({"fill":"#2980B9", "fill-opacity":0.7, "x":current_x, "y":y_start, "width":pb_w, "height":pb_h, "stroke-width":2}, "250", "<>")
		paper.getById(clicked_option["title_id"]).animate({"stroke":"#fffffe", "x":current_x+(pb_w/2), "y":y_start+t_offset1}, "250", "<>", function() { this.attr(text_single_attr) });
		paper.getById(clicked_option["badge_id"]).animate({"fill-opacity":0}, "250", "<>", function() { this.remove() });
		paper.getById(clicked_option["badge_text_id"]).remove()

		// Add back button
		addBackButton(current_x)

		// Add line to previous
		drawPathLine(current_x, options[index]["duration"])

		// Update DST's (path_data), (current_x)
		path_data.push({"ideal_id":ideal_id, "box_id":clicked_option["box_id"], "title_id":clicked_option["title_id"]})
		current_x += pb_w + pb_offset

		// Make the container bigger
		$("#path-container-svg").css("overflow", "scroll")

		// Scroll right, render options
		// var current_scroll = $('#path-container-svg').scrollLeft()
		// $('#path-container-svg').scrollLeft(current_scroll + pb_w + pb_offset)

		// Render options from clicked option
		getAndRenderOptions(ideal_id) 
	};

	/* Moves a single box upwards to new 'y' value, resets hover
			handlers accordingly */
	var scrollBoxUp = function(y, option_data) {
		// Animate box up
		paper.getById(option_data["box_id"]).animate({"y":y}, "250", "<>")
		paper.getById(option_data["title_id"]).animate({"y":y+t_opt_offset}, "250", "<>")
		paper.getById(option_data["badge_id"]).animate({"cy":y}, "250", "<>")
		paper.getById(option_data["badge_text_id"]).animate({"y":y}, "250", "<>")

		// Set 'x' outside -- closure!
		var x = paper.getById(option_data["box_id"]).attr("x")

		// Reset handlers
		paper.getById(option_data["box_id"]).unhover().hover(function() {
			showInfo(options[option_data["index"]], option_data["index"])
			this.animate({"width":ob_w+12, "x":x-6, "height":ob_h+6, "y":y-3}, '100', '<>')
		}, function() {
			this.animate({"width":ob_w, "x":x, "height":ob_h, "y":y}, '100', '<>')
		});
	};

	/* Handler for scroll arrow click */
	var scrollOptions = function() {
		
		// Set y values of current boxes
		var option_y_values = []
		for (var jk = 0; jk < option_data.length; jk++) {
			option_y_values.push(option_data[jk]["y"])
		}

		// Remove top option
		var deceasedOption = option_data.pop()
		paper.getById(deceasedOption["box_id"]).animate({"opacity":0}, "250", "<>", function() { this.remove() })
		paper.getById(deceasedOption["title_id"]).animate({"opacity":0}, "250", "<>", function() { this.remove() })		
		paper.getById(deceasedOption["badge_id"]).animate({"opacity":0}, "250", "<>", function() { this.remove() })
		paper.getById(deceasedOption["badge_text_id"]).remove()


		// Move lower options up
		for (var p = option_data.length - 1; p >= 0; p--) {
			scrollBoxUp(option_y_values[p+1], option_data[p])
			option_data[p]['y'] = option_y_values[p+1]
		};

		// Add new option to bottom
		var next_index = (option_data[0]["index"] == options.length - 1) ? 0 : option_data[0]["index"] + 1;
		drawOptionBox(options[next_index], current_x, option_y_values[0], next_index)
	};

	var backClicked = function() {

		// Remove existing messages
		if ($('.main-message').length > 0) removeAllMessages()

		// Hide info box
		hideInfo()

		// Remove options
		removeOptions(null)

		// Remove most recent path via pop
		var most_recent = path_data.pop()
		paper.getById(most_recent["box_id"]).animate({"opacity":0}, "500", "<>", function() { this.remove() }) 	
		paper.getById(most_recent["title_id"]).animate({"opacity":0}, "500", "<>", function() { this.remove() }) 	
		if ('entity_id' in most_recent)
			paper.getById(most_recent["entity_id"]).animate({"opacity":0}, "500", "<>", function() { this.remove() }) 	

		// Remove back buttons
		removeBackButton()

		// Remove shufflers
		removeShufflers()


		// Disable save button if applicable & reset current_x
		if (path_data.length == 0) {
			$('.save-button').each(function() { $(this).attr("disabled", true)})
			current_x = x_start
			normalizeCurrentPos()
			displayWelcomeMessage()
		} else {

		// else, re-render options off of previous
			current_x = current_x - pb_offset - pb_w

			// remove most recent line
			var last_line = line_data.pop()
			paper.getById(last_line["line_id"]).animate({"opacity":0}, "250", "<>", function() { this.remove() });
			if (last_line["duration_id"] != null)
				paper.getById(last_line["duration_id"]).animate({"opacity":0}, "250", "<>", function() { this.remove() });
		
			// redraw back button on this guy
			addBackButton(current_x - pb_w - pb_offset)

			// render options of el
			getAndRenderOptions(path_data[path_data.length-1]["ideal_id"])
		}	

	};

	/****************/
	/* Main Helpers */
	/****************/

	/* Display error message when trying to save */
	var displayErrorMessage = function(message) { 
		$('.warning-message').append(message).fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100)
	};

	/* Display "no more options" message */
	var displayEndMessage = function() {
		$('#current-positions-container').append("<div id='end-message' class='main-message'>Sorry, we actually aren't sure what comes after that, but we're <br/>hard at work figuring it out. Go back to keep exploring this path.</div>")
	};

	/* Display welcome message */
	var displayWelcomeMessage = function() {
		$('#current-positions-container').append("<div class='main-message'>Click on a starting position to begin exploring your ideal career path.</div>")
	};

	/* Remove any and all messages */
	var removeAllMessages = function() {
		$('.main-message').each(function() { $(this).fadeOut(500, function() { this.remove() })});
		$('.warning-message').empty()
	};

	/* Adds back button to most recent path el */
	var addBackButton = function(x) {
		// Remove previous
		removeBackButton()

		// Create circle and 'x'
		var circle = paper.circle(x+pb_w,y_start,12).attr(back_button_attr).click(backClicked)
		var x = paper.text(x+pb_w,y_start,"x").attr(back_button_x_attr).click(backClicked)
		back_button_data.push(circle.id, x.id)
	};

	/* Remove disabled state and class from save button */
	var enableSave = function() {
		$('.save-button').each(function() { $(this).removeAttr("disabled").removeClass("disabled").click(save) })
	};

	/* Sets entire Build back to beginning state */
	var cleanCanvas = function() {
		normalizeCurrentPos() // restore all current position_ids
		removeAllMessages() // remove warning and welcome messages
		removeShufflers() // remove next arrow and dots
		clearPaper() // remove all path and option elements
	};

	/* Removes the back button from most recent path el */
	var removeBackButton = function() {
		if (back_button_data.length > 0) {
			paper.getById(back_button_data[0]).remove()
			paper.getById(back_button_data[1]).remove()			
			back_button_data.length = 0
		};
	};

	/* Removes shuffle arrow and dots */
	var removeShufflers = function() {
		if (shuffle_data.length > 0) {
			for (var j = 0; j < shuffle_data.length; j++) {
				paper.getById(shuffle_data[j]).animate({"opacity":0}, "250", "<>", function() { this.remove() });
			};
			shuffle_data.length = 0;
		};
	};

	/* Takes each current pos, unselects, unbinds and re-adds hover
			and click handlers */
	var normalizeCurrentPos = function() {

		$(".current-position").each(function() {
			$(this).unbind() // unbind old events. !important!

			$(this).hover(function() {
				$(this).css("background-color", blue)
			}, function() { $(this).css("background-color", blue_opaque) }
			).click(function() {
				addStartingPosition(this)
			}).css("background-color", blue_opaque)
		});
	};

	/* Removes options - box, text, badge, and badge text */
	// Takes an optional index NOT to remove (used for optionClicked)
	var removeOptions = function(exception_index) {

		for (var m = 0; m < option_data.length; m++) {
			if (exception_index == null || exception_index != m) {
				paper.getById(option_data[m]["box_id"]).animate({"opacity":0}, '500', '<>', function() { this.remove() })
				paper.getById(option_data[m]["title_id"]).animate({"opacity":0}, '500', '<>', function() { this.remove() })
				paper.getById(option_data[m]["badge_id"]).animate({"opacity":0}, '500', '<>', function() { this.remove() })
				paper.getById(option_data[m]["badge_text_id"]).animate({"opacity":0}, '500', '<>', function() { this.remove() })
			};
		};
		option_data.length = 0;
	};

	/* Removes all options, path items, and lines, reset DST's, and
			resets current_x */
	var clearPaper = function() {

		removeOptions(null)

		// Remove lines
		for (var n = 0; n < line_data.length; n++) {
			paper.getById(line_data[n]['line_id']).remove()
			if (line_data[n]['duration_id'] != null)
				paper.getById(line_data[n]['duration_id']).remove()
		};
		line_data.length = 0;

		// Remove path
		for (var l = 0; l < path_data.length; l++) {
			paper.getById(path_data[l]['box_id']).remove()
			paper.getById(path_data[l]['title_id']).remove()
			if ('entity_id' in path_data[l])
				paper.getById(path_data[l]['entity_id']).remove()
		};
		path_data.length = 0;

		// Reset current_x
		current_x = x_start
	};

	/* Creates ellipsis dots and scroll arrow */
	var activateScrolling = function(opt_y, y_offset) {

		// Set y value of dots
		opt_y += y_offset - 15

		// Add dots
		for (var z = 0; z < 3; z++) {
			opt_y+=16
			var circle = paper.circle(current_x+(ob_w/2), opt_y, 5).attr(shuffle_attr)
			shuffle_data.push(circle.id)
		}

		// Add arrow
		var arrow_x = current_x + (ob_w/2)
		var arrow = paper.path("M"+arrow_x+","+(y_offset-70)+"L"+(arrow_x-15)+","+(y_offset-50) +"L"+(arrow_x+15)+","+(y_offset-50)+"z").attr(shuffle_attr).click(scrollOptions)
		shuffle_data.push(arrow.id)
	}

	/* Draws an option box at 'x', 'y' from options['index'] */
	var drawOptionBox = function(position, x, y, index) {

		// Draw box, set handlers
		var option_box = paper.rect(x,y,ob_w,ob_h,ob_r).attr({
			'stroke':color_map[1], 'fill':color_map[1], 'fill-opacity':0, 'opacity':0, 'stroke-width':2,
		}).hover(function() {
			showInfo(position, index)
			this.animate({"width":ob_w+12, "x":x-6, "height":ob_h+6, "y":y-3}, '100', '<>')
		}, function() {
			this.animate({"width":ob_w, "x":x, "height":ob_h, "y":y}, '100', '<>')
		}).click(function() {
			optionClicked(index) // = index in the "options" array
		})

		// Animate to full opacity
		option_box.animate({'opacity':1}, '300', '<>')

		// Ensure title will fit
		if (position["title"].length > 20) var pos_title = break_string(20, position["title"])
		else var pos_title = position["title"]
		
		// Title 
		var title = paper.text(x+(ob_w/2),y+t_opt_offset, pos_title).attr(text_options_attr)
		title.data("box_id",option_box.id)
		title.click(function() { optionClicked(index) });

		// // Box needs to animate on hover here, too
		// title.hover(function() {
		// 	paper.getById(this.data("box_id")).animate({"width":ob_w+12, "x":x-6, "height":ob_h+6, "y":y-3}, '250', '<>')
		// }, function() {
		// 	paper.getById(this.data("box_id")).animate({"width":ob_w, "x":x, "height":ob_h, "y":y}, '150', '<>')
		// })

		// Create probability badge and text
		var badge = paper.circle(x+ob_w,y,badge_r).attr(opt_badge_attr)
		var badge_text = paper.text(x+ob_w,y,position['prop']).attr(text_single_attr)

		// Update DST's	
		option_data.unshift({"title":position['title'], "box_id":option_box.id, "title_id":title.id, 'badge_id':badge.id, 'badge_text_id':badge_text.id, "index":index, "y":option_box.attr("y")})
	};

	/* Draws path box for selected position */
	var drawPathBox = function(position, x, color, isStarting, index) {

		// Draw box, set handlers
		var box = paper.rect(x,y_start,pb_w,pb_h,pb_r).attr(path_box_attr).hover(function() {
			this.attr("fill-opacity",1)
			if (!isStarting && index >= 0) showInfo(position, index)
		}, function() {
			this.attr("fill-opacity",0.7)
		});

		// Format text to fit 
		var text_offset = t_offset_t
		var entity_offset = t_offset_e
		if (position['title'].length > 25) {
			var pos_title = break_string(25, position["title"])
			text_offset += 6
			entity_offset += 8
		} else { var pos_title = position['title']}

		// Add text
		var title = paper.text(x+(pb_w/2),y_start+text_offset, pos_title).attr(text_double_attr)
		var entity_name = paper.text(x+(pb_w/2),y_start+entity_offset, position["entity_name"]).attr(text_double_attr)

		// Draw line to previous
		if (!isStarting && 'duration' in position) drawPathLine(current_x, position["duration"])
		else if (!isStarting) drawPathLine(current_x, null)

		// Update DST's
		path_data.push({"ideal_id":position["ideal_id"], "box_id":box.id, "title_id":title.id, "entity_id":entity_name.id})
		current_x += pb_w + pb_offset

	};

	/* Draws a line from current_x to previous el */
	var drawPathLine = function(current_x, duration) {
		var line = paper.path("M"+(current_x-pb_offset+line_offset)+","+midline+"L"+(current_x-line_offset)+","+midline).attr(line_attr).animate({'opacity':1} ,'500', '<>', function() {
			
			// If no duration, return here
			if (duration == null) {
				line_data.push({'line_id':line.id, 'duration_id':null})
				return false;
			}

			// Else, add duration
			var text = paper.text(current_x-(pb_offset/2),midline-line_offset,duration).attr(duration_attr).animate({'opacity':1}, '500', '<>')
			line_data.push({'line_id':line.id, 'duration_id':text.id})
		})
	};	

	/* Hides everything in info box */
	var hideInfo = function() {
		$("#info-box-header").fadeOut(250)
		$(".info-box-sub-header").each(function() {
			$(this).fadeOut(200).css("visibility","hidden")
		})
		$('#info-box-stats').fadeOut(250)
		$("#info-box-people").fadeOut(250)
		$("#info-box-entities").fadeOut(250)
	};

	/* Displays info given option[option_index] */
	var showInfo = function(data, option_index) {

		// Header & Sub-Headers
		$("#info-box-header").empty().fadeIn().append(data["title"])
		$(".info-box-sub-header").each(function() {
			$(this).fadeIn(10).css("visibility","visible")
		})

		// Stats
		$('#info-box-stats').empty().fadeIn(10).append("<div class='info-box-stat'>Average Time: " + data['duration'] + "</div>")
		$('#info-box-stats').append("<div class='info-box-stat'>Percent Who Move to this Position: " + data["prop"] + "</div>")

		// People
		$("#info-box-people").empty().fadeIn(10)
		for (var j = 0; j < data["people"].length; j++) {
			var person = data["people"][j]
			var title = person["title"] + " at " + person["entity_name"]
			if (title.length > 40) { // 40 is just the number of chars that cuts on my laptop... check this
				title = person["title"] + " at<br/>" + person["entity_name"]
			}		

			var person_html = "<div class='info-box-person'><div class='info-box-people-pic'><a href='/profile/"+person["id"]+"'><img src='"+person["profile_pic"]+"'/></a></div><div class='info-box-people-text'><a href='/profile/"+person["id"]+"'><span class='info-box-people-name'>"+person["name"] +"</span></a><br/><span class='info-box-people-title'>"+title+"</span></div></div>"

			$("#info-box-people").append(person_html)
		};

		// Entities
		$("#info-box-entities").empty().fadeIn(10)
		for (var l = 0; l < data["entities"].length; l++) {
			$('#info-box-entities').append("<div class='info-box-entity' data-option-index='"+option_index+"' data-entity-index='"+l+"'>"+data['entities'][l]['name']+"</div>")
		}
		$(".info-box-entity").each(function() {
			$(this).hover(function() { entityOver($(this)) },
			 function() { entityOut($(this)) });
		});
	};

	/* Renders options */
	var renderOptions = function(options, y_offset) {

		// Set length based on max displayed (4) */
		var length = (options.length > max_options) ? max_options : options.length;

		// Iterate through and draw boxes
		for (var i = 0; i < length; i++) {
			var opt_y = (y_offset) * (i) + (y_offset) - 25 // ghetto math
			drawOptionBox(options[i], current_x, opt_y, i)
		}

		// If > max # of options, allow scrolling
		if (options.length > max_options)
			activateScrolling(opt_y, y_offset)
	};


	/* Main Methods */
	var addStartingPosition = function(el) {


		normalizeCurrentPos()
		removeAllMessages()
		removeShufflers()

		var index = $(el).data("index")
		var starting_position = current_positions_javascript[index]

		// Clear Paper
		clearPaper()

		// Don't allow this to click again
		$(el).unbind()

		// Change CSS
		$(el).css("background-color", "rgba(41,128,185,1)")

		drawPathBox(starting_position, x_start, color_map[1], true, 0)
		
		// Add back button
		addBackButton(x_start)

		// Set start pos id
		start_pos_id = starting_position["pos_id"]

		console.log("calling getAndRenderOptions from @addStartingPosition")
		getAndRenderOptions(starting_position['ideal_id'])
		enableSave()
	};

	var searchStartingPositions = function() {
		console.log("called")

		var left = $('#new-position-box').offset().left
		var offset_left = (left > 150) ? left-150 : 0;
		$('#build-new-position-select').css("visibility", "visible").css("left", offset_left).hide().fadeIn(250)
		$('#new-position-box').empty().append("Select This Position").unbind('mouseenter').unbind('mouseleave').unbind("click").click(selectNewPosition)
	};



	/* Just a way to decompose (and debug) two bigger methods */
	var getAndRenderOptions = function(ideal_id) {
		
		// Get options from server
		options = getOptions(ideal_id)	
		// console.log(options)

		// If none returned, display message
		if (options.length == 0) {
			displayEndMessage()
			return false;
		}

		// Else, calculate offset for y positioning & render
		var offset_denominator = (options.length > 4) ? 6 : options.length + 2
		var y_offset = (options.length == 1) ? 175 : Math.ceil(425/(offset_denominator))
		renderOptions(options,y_offset)
	};

	/* Renders existing path */
	var renderExistingPath = function() {
	
		// Iterate through path, draw boxes
		for (var j = 0; j < path.length; j++) {
			if (j == 0) drawPathBox(path[j], current_x, color_map[1], true, -1)
			else drawPathBox(path[j], current_x, color_map[1], false, -1)
		};
		
		// Add back button to latest
		addBackButton(current_x-pb_w-pb_offset)

		// Set start pos id
		start_pos_id = path[0]["pos_id"]

		// Render options off of last path item
		getAndRenderOptions(path[path.length-1]['ideal_id'])
		// enableSave()	
	}







	/* Constants */
	var paper;
	var midline = 175;
	var pb_w = 160; var pb_h = 65; var pb_r = 2; var pb_offset = 75;
	var ob_w = 150; var ob_h = 50; var ob_r = 2;
	var x_start = 50;
	var y_start = midline - (pb_h/2)
	var line_offset = 5
	var t_offset1 = 35; var t_offset2 = 20; var t_opt_offset=25;
	var t_offset_t = 20; var t_offset_e = 40;
	var badge_r = 16
	var path_id = -1 // if new path, id = -1
	var max_options = 4;

	var current_x = x_start
	var start_pos_id;

	/* Data Structures */
	var path_data = []
	var line_data = []
	var option_data = [] // holds SVG data for option boxes, as well as index of option in the "options" array
	var border_data = []
	var options = null
	var shuffle_data = []
	var back_button_data = []


	/* SVG Styling */
	var text_double_attr={'fill':'#fffffe','opacity':'1','font-size':13, 'font-family':"'Arimo', 'Helvetica Neue', 'Helvetica'"}
	var text_single_attr={'fill':'#fffffe','opacity':'1','font-size':13, 'font-family':"'Arimo', 'Helvetica Neue', 'Helvetica'", 'font-weight':'lighter'}
	var line_attr={'stroke':'#68696b', 'stroke-width':2, 'opacity':0}
	var text_options_attr={'stroke':'#68696b', 'font-size':13, 'cursor':'pointer', 'font-family':'"Arimo", "Helvetica Neue", "Helvetica"'}
	var opt_badge_attr = {'stroke':'rgb(41,128,185)', 'fill':'rgb(41,128,185)'}
	var path_box_attr = {'stroke':'#2980B9', 'fill':'#2980B9', 'fill-opacity':'0.7', 'stroke-width':2 }
	var duration_attr = {'stroke':'#68696b', 'opacity':0} // to animate in
	var back_button_attr = {'stroke':'#E74C3C', 'fill':'#E74C3C', 'cursor':'pointer'}
	var back_button_x_attr = {'stroke':'#fffffe', 'cursor':'pointer', 'font-size':14}
	var shuffle_attr = {'fill':'#2980B9','stroke':'#2980B9'}

	/* Colors */
	var blue = "rgba(41,128,185,1)"
	var blue_opaque = "rgba(41,128,185,0.7)"


	var color_map = {
		1:"#2980B9",
	}




	$(function() {
		paper = new Raphael("path-container-svg",2500,400)
		
		if (path) {
			enableSave()
			renderExistingPath()
			$('#path-container-svg').css("overflow", "scroll")
		}
		else displayWelcomeMessage()
	});


	/* TODO
	: rendering just 2 results --> "Account Executire @ EventBrite"
	: make newposition box clickable
	: need to automatically scroll right... gradually... 
	: email dead end idealpos
	: triply long text
	: need to show level
	: three line current-position when added from new position
	: disable all saving

	CHECK: 
	: long entity names (not just long pos title... rarer)
	: super long title names i.e. > 40 characters

	A2:
	: industry changes = color changes... how to do w/ idealpos?
	: lvl changes indicated in line color
	: convert info box to a template, esp people
	: allow deleting paths
	: saving
	: save tmp paths in session
	: better animations
	*/

