/* Raphael Extension giving ID's to sets */
Raphael.st.setID = function(id) {
	this.id = id;
};

Raphael.st.setData = function(name, value) {
	this.data[name] = value
};

// Not tested
Raphael.st.unbindAll = function() {
	while(this.events.length) {
		var e = this.events.pop()
		e.unbind()
	}
};

$(function() {

	// global variables
	var current_selected_position, // holds object of position currently selected
		start_pos_id,
		start_pos_title,
		start_entity_name,
		start_ideal_id,
		chosen_data, // stores selected path, useful for keeping track of length
		lines, // stores line objects
		options,
		options_data,
		options_data_raw,
		option_index = 0,
		shuffle_button,
		shuffle_text_id = -1,
		chosen_data,
		chosen_path, // container set for all selected options
		no_display_ids,
		index_length,
		no_options_display; 


	// init positioning variables
	var x,
		y,
		x_offset,
		y_offset = 15,
		vert = 350,
		paper_w = 1250,
		paper_h = 350,
		midline = paper_h / 2,
		dot_radius = 14,
		x_start = 75,
		dot_distance = 150,
		text_y_offset = 10,
		text_x_offset = 10,
		text_offset1 = 50, // 40
		text_offset2 = 30, //25
		text_offset3 = 10,
		title_text_y_offset = 45,
		chosen_title_text_y_offset = 10,
		chosen_title_text_x_offset = 35,
		entity_text_y_offset = 25,
		entity_list_x_offset = 35,
		entity_list_y_offset = 10,
		prop_text_x_offset = 50,
		prop_text_y_offset = 50,
		shuffle_x_spacer = 45,
		shuffle_y_spacer = 55;
		
	// constants and instance variables
	var current_pos = current_positions_json,
		global_pos_id,
		options_data = [],
		chosen_data = [],
		line_data = [],
		shuffle_button_id = -1;

	// initialize svg space
	var paper = new Raphael("path-container", paper_w, paper_h)

	// If existing path, render it and comments
	if (path_id != -1) {
		render_existing_path()
		$('#comments-container').css("visibility", "visible")
	}

	// Click handler for seleting positions
	$('select#position-select').change(function() {
		var el = $(this).find(":selected")
		current_position_clicked(el);
	});

	/* Event Handlers */

	var current_position_clicked = function(el) {
		
		option_index = 0;
		index_length = null;
		clear_path();
		// assign target for easier reference
		var opt = el;

		// check to see if need to remove no options
		if (no_options_display != null) {
			no_options_display.remove();
		}

		// If already selected, do nothing
		if (current_selected_position != null && opt.val() == current_selected_position.val()) {
			return false;
		} else {
			current_selected_position = opt; // update selection
		};

		// update global variables with new starting position
		start_pos_id = opt.data("pos_id")
		start_pos_title = opt.data("title")
		start_entity_name = opt.data("entity_name")
		start_ideal_id = opt.data("ideal_id")

		// add this as the first position in path
		if (chosen_path != null) {
			chosen_path.remove();
		};
		chosen_data = [];
		chosen_data.push({"entity_name":start_entity_name,"pos_title":start_pos_title,"pos_id":start_pos_id,"ideal_id": start_ideal_id})
		render_chosen_path()
		get_and_render_options(start_ideal_id,start_pos_id);
		// add_first_position({'start_pos_id':start_pos_id,'start_pos_title':start_pos_title,'start_entity_name':start_entity_name,'start_ideal_id':start_ideal_id})
	}

	// attributes

	var chosen_dot_attributes = {
		'fill':'#2980B9', //'fill':'rgb(41,98,152)',
		'stroke-width':0
	};

	var option_dot_attributes = {
		'fill':'#3498DB', //'fill':'#679FD2',
		'stroke-width':0,
		'fill-opacity':0,
	};

	var option_wedge_attributes = {
		'stroke-width':0,
		'fill':'rgb(41,98,152)'
	}

	var saved_dot_attributes = {
		'fill':'#2980B9', //'fill':'#043A68',
		// 'stroke-opacity':.5,
		// 'stroke':'#3980B9',
		// 'stroke-width':18,
		'stroke-width':0,
	};

	var chosen_line_attributes = {
		'stroke':'#c0c0c0',
		'stroke-linecap':'round',
		'stroke-opacity':'.8'
	};

	var option_line_attributes = {
		'stroke-dasharray':'-',
	};

	var initial_text_attributes = {
		"font-size":14,
		"font-family": '"Helvetica Neue", "Helvetica"',
		"text-anchor": "middle",
		"font-weight": "normal",
		"width": "100px",
		"fill-opacity":1
	};

	var text_attributes = {
		"font-size":14,
		"font-family": '"Helvetica Neue", "Helvetica"',
		"text-anchor": "middle",
		"font-weight": "normal",
		"width": "100px",
		"fill-opacity":0
	};

	var chosen_text_attributes = {
		"font-size":14,
		"font-family": '"Helvetica Neue", "Helvetica"',
		"text-anchor": "start",
		"font-weight": "normal",
		"width": "100px",
		"fill-opacity":0
	};

	var option_text_attributes = {
		"font-size":14,
		"text-anchor":"start",
		"font-family":'"Open Sans", "Helvetica"'
	};

	var shuffle_button_attr = {
		'fill':'rgb(48,91,152)',
		'fill-opacity':1,
		'stroke-width':0,
		'cursor':'pointer'
	}

	var shuffle_text_attr = {
		// 'stroke':'#f0f0f0',
		'font-size':14,
		'font-family':"Helvetica",
		'fill':'#f0f0f0',
		'text-anchor':'start',
		'cursor':'pointer',
		'fill-opacity':1
	}

	var render_chosen_path = function() {
		if (!chosen_path) {
			chosen_path = paper.set();
		} else {
			chosen_path.remove();
		};
		convert_chosen_data();
	}

	var convert_chosen_data = function() {
		for (var i = 0; i < chosen_data.length; i++) {
			// set positioning variables
			x = x_start + dot_distance * i;
			y = midline;

			if ((i+1) % 2 == 0) {
				
				var title_y = midline + text_offset2;
				var entity_name_y = midline + text_offset1;
			}
			else {

				var title_y = midline - text_offset1;
				var entity_name_y = midline - text_offset2;
			}

			// create svg elements
			var dot = add_dot({'x':x,'y':y,'radius':dot_radius,'attr':chosen_dot_attributes});
			var title_text = add_text({'x':x,'y':title_y,'text':chosen_data[i]['pos_title'],'attr':initial_text_attributes});
			var entity_text = add_text({'x':x,'y':entity_name_y,'text':chosen_data[i]['entity_name'],'attr':initial_text_attributes});
			
			// set relevant data on dot
			dot.data("pos_id", chosen_data[i]['pos_id'])
			dot.data("title_text_id", title_text.id)
			dot.data("entity_text_id", entity_text.id)
			dot.data("ideal_id", chosen_data[i]['pos_id'])

			// initialize nested set
			var group = paper.set();

			// add to nested set
			group.push(dot,title_text,entity_text);

			// add to umbrella set
			chosen_path.push(group);

			lines = paper.set();

			if (i > 0) {
				line_params = {
					'x_start':x_start + ((i-1) * dot_distance) + dot_radius,
					'y_start':midline,
					'x_finish':x_start + (i*dot_distance) + dot_radius,
					'y_finish':midline,
					'attr':chosen_line_attributes
				};
				var line = add_line(line_params);
				// add line to set
				lines.push(line);
				// add line data to array
				line_data.push(line.id);
				line.toBack();
			}
			
		}
	}

	/* Triggered by selecting new first position */
	var add_first_position = function(params) {

		// Check if path already exists, in which case delete	
		if (chosen_data.length > 0) {
			clear_path()
		}

		/* Create SVG Elements */
		var dot = add_dot({'x':x_start,'y':midline,'radius':dot_radius,'attr':chosen_dot_attributes});
		var title_text = add_text({'x':x_start,'y':midline - title_text_y_offset,'text':start_pos_title,'attr':initial_text_attributes});
		var entity_text = add_text({'x':x_start,'y':midline - entity_text_y_offset,'text':start_entity_name,'attr':initial_text_attributes});

		/* Set relevant data on dot element */
		dot.data("pos_id", start_pos_id)
		dot.data("title_text_id", title_text.id)
		dot.data("entity_text_id", entity_text.id)
		dot.data("ideal_id", start_ideal_id)

		/* Add 'back' to do */
		dot.click(go_back)

		/* Update data structure */
		chosen_data.push({"dot_id":dot.id, "pos_id":start_pos_id, "ideal_id": start_ideal_id})

		/* Get and render options */
		get_and_render_options(start_ideal_id,start_pos_id)
	};

	var add_rect = function(params) {
		var rect = paper.rect(params.x,params.y,params.width,params.height,params.r).attr(params.attr);
		return rect
	};

	var add_dot = function(params) {
		var dot = paper.circle(params.x,params.y,params.radius).attr(params.attr);
		return dot
	};

	var add_text = function(params) {
		var text = paper.text(params.x,params.y,params.text).attr(params.attr);
		return text
	}

	var add_line = function(params) {
		var line = paper.path("M" + params['x_start'] + ',' + params['y_start'] + ' L' + params['x_finish'] + ','  + params['y_finish']).attr(params['attr']);
		return line;
	}

	var clear_path = function() {
		// Delete dots, options and lines
		remove_chosen_dots()
		remove_options()
		remove_all_lines()
	}

	var remove_chosen_dots = function() {

		// Remove in reverse order
		for (var k = chosen_data.length - 1; k >= 0; k--) {
			var dot = paper.getById(chosen_data[k]["dot_id"])
			if (dot != null) {
				remove_dot_all(dot);
			}
		}
		chosen_data.length = 0;
	};

	// removes all lines in svg
	var remove_all_lines = function() {
		if (lines != null) {
			for (var d = 0; d < lines.length; d++) {
				lines[d].remove();
			}
		}
		// for (var d = 0; d < line_data.length; d++) {
		// 	paper.getById(line_data[d]).remove()
		// }
		lines = null;
		// line_data = null;
	};

	// removes lines connected to specific dot
	var remove_dot_lines = function(dot) {
		for (var d = 0; d < lines.length; d++) {
			if (lines[d]['dot_id'] == dot.id) { // check for match
				lines[d].remove()
			}
		}
	}

	var go_back = function(ev) {
		// remove clicked dot, text and lines
		remove_dot_all($(ev.currentTarget));

		// fade out options
		fade_out_options();
	};	

	// removes dot and associated elements
	var remove_dot_all = function(dot) {
		// remove associated elements first
		paper.getById(dot.data("title_text_id")).remove();
		paper.getById(dot.data("entity_text_id")).remove();
		remove_dot_lines(dot);
		// finally remove dot
		dot.remove();
	};

	// fades out current options
	var fade_out_options = function() {
		params = {
			'fill-opacity':0
		}
		options.animate(params,100,null,remove_options) // after fading out, remove completely
		// options_text.animate(params,10,null,remove_text)  // for now lets keep text and dots in options
	};

	var fade_in_options = function() {
		params = {
			'fill-opacity':1
		}
		options.animate(params,100);
	};

	// removes current options
	var remove_options = function() {
		if (options != null) {
			options.remove();
		}
	};

	// wrapper for retrieving, converting and then displaying options
	var get_and_render_options = function(ideal_id,pos_id) {
		options_data_raw = get_options(ideal_id,pos_id);
		convert_and_render_data();
		options = convert_data();
		// console.log(options);
		render_options();
	};

	var convert_and_render_data = function() {
		convert_data();
		render_options();
	}

	// converts JSON from API to raphael objects
	var convert_data = function() {
		
		// assign global retrieved data for easier processing
		data = options_data_raw;
		if (!data) {
			if (options != null) {
				options.remove();	
				options = paper.set();
			};
			return false;
		}
		// remove set to start fresh
		if (options != null) {
			options.remove();
			options = paper.set();	
		}
		options = paper.set();

		// get length of data
		var length = data.length - option_index > 5 ? 5 + option_index : data.length - option_index;
		if (!index_length) {
			index_length = length;
		}

		// // get starting point for rendering options
		// if (index == null) {
		// 	option_index = 0;
		// }

		// loop through data
		for (var i = option_index; i < index_length; i++) {
			// set positioning variables
			x = dot_distance * chosen_data.length + x_start;
			console.log(option_index,index_length);
			
			// check to see if there is only one option; if so, set to midline
			if (length == 1) {
				y = midline;
			} else {
				y = y_offset + ( (vert - y_offset - 55) / length * (i))
			}
			
			
			// get list of entities
			var entity_list_text = null;
			var orgs = data[i].orgs;
			for (var j = 0; j < orgs.length; j++) {
				if (j == 0) {
					var entity_list_text = orgs[j].name;
				} else if (j == 1) {
					entity_list_text = entity_list_text + ", " + orgs[j].name;
				} else if (j == 2) {
					var rem_count = orgs.length - j;
					entity_list_text = entity_list_text + " and " + rem_count + " others";
				} 
			}

			// for each option, create set for dot and text, then nest than under larger set
			var dot = add_dot({'x':x,'y':y,'radius':dot_radius,'attr':option_dot_attributes});
			var title = add_text({'x':x+chosen_title_text_x_offset,'y':y-chosen_title_text_y_offset,'text':data[i].ideal_title,'attr':chosen_text_attributes});
			var prop = add_text({'x':x-prop_text_x_offset,'y':y,'text':data[i].prop,'attr':text_attributes});
			var entities = add_text({'x':x+entity_list_x_offset,'y':y+entity_list_y_offset,'text':entity_list_text,'attr':chosen_text_attributes});
			
			// add data to dot
			dot.data("title_text_id", title.id)
			dot.data("entity_text_id", entities.id)
			dot.data("pos_id", start_pos_id) // dots don't represent individual positions, pass in start position id to avoid circling back
			dot.data("ideal_id", data[i].ideal_id)
			dot.data("prop_text_id",prop.id)
			dot.data("entity_name",entity_list_text);
			dot.data("pos_title",data[i].ideal_title);

			// add hover handlers
			dot.hover(function() {
				this.attr("r", 16).attr("fill-opacity",1)
				paper.getById(this.data("title_text_id")).attr("font-weight","bold")
				paper.getById(this.data("entity_text_id")).attr("font-weight","bold")

			}, function() {
				this.attr("r",dot_radius).attr("fill-opacity",.5)
				paper.getById(this.data("title_text_id")).attr("font-weight","normal")
				paper.getById(this.data("entity_text_id")).attr("font-weight","normal")
			});

			// add click handler
			dot.click(function() {
				option_clicked(this)
			})

			// update data structure
			options_data.push({'dot_id':dot.id, 'position_id':start_pos_id, 'title_text_id': title.id, 'entity_text_id': entities.id,'prop_text_id':prop.id})
			
			// initialize local set
			var option = paper.set();
			option.push(dot,title,prop,entities);

			// push local set into umbrella set
			options.push(option);
		}
		return options;
	}

	/* Renders the options returned from AJAX call */
	var render_options = function() {

		// if no options returned... then do nothing!
		if (!options || options.length == 0) {
			console.log("No options returned.");
			console.log(options);
			display_no_options();
			deactivate_shuffle_button();
			return false;
		}

		// enable/disable shuffle button
		if (options_data_raw.length > 5) {
			activate_shuffle_button();
		} else {
			deactivate_shuffle_button();
		};

		// fade in all options
		fade_in_options();
	};

	var display_no_options = function() {
		no_options_display = paper.set();
		rect_attr = {
			"stroke-width":1,
			"stroke":"rgb(48,91,152)"
		};

		rect_params = {
			"x":150,
			"y":midline-12,
			"width":250,
			"height":25,
			"r":2,
			"attr":rect_attr
		};

		text_attr = {
			"text-anchor":"start",
			"fill":"rgb(48,91,152)",
			"font-size":14,
			"font-family": '"Helvetica Neue", "Helvetica"',
			"text-anchor": "middle",
			"font-weight": "normal",
			"width": "100px"
		};

		text_params = {
			"x":285,
			"y":midline,
			"text":"There are no paths for that option",
			"attr":text_attr
		};

		var rect = add_rect(rect_params);
		var text = add_text(text_params);
		no_options_display.push(rect,text);

	}

	var activate_shuffle_button = function() {

		if (shuffle_button != null) {
			return true;
		}
		shuffle_button = add_rect({'x':dot_distance*chosen_data.length+shuffle_x_spacer,'y':vert-shuffle_y_spacer,'width':125,'height':35,'r':2,'attr':shuffle_button_attr});
		shuffle_text = add_text({'x':dot_distance*chosen_data.length+shuffle_x_spacer+20,'y':vert-shuffle_y_spacer+20,'text':"More options",'attr':shuffle_text_attr});
		
		// add Click Handler
		shuffle_button.click(shuffle_options)
		shuffle_text.click(shuffle_options)

	};

	var deactivate_shuffle_button = function() {
		if (shuffle_button != null) {
			shuffle_button.remove();
			shuffle_text.remove();	
		}
		
		
	};

	var shuffle_options = function() {
		
		if (options_data_raw.length - option_index > 5) {
			option_index += 5;
			index_length = option_index + options_data_raw.length - option_index;
			console.log('index length',index_length);
		} else {
			option_index += options_data_raw.length - option_index;
			index_length = options_data_raw.length;

		}
		convert_and_render_data();
	}

	var option_clicked = function(el) {
		// reset counters
		option_index = 0;
		index_length = 0;

		var id = el.id;
		var ideal_id = el.data('ideal_id');
		var dot = paper.getById(id);
		// // Remove clicks from previous dots
		// if (chosen_data.length > 0) {
		// 	for (var l = 0; l < chosen_data.length; l++) {
		// 		paper.getById(chosen_data[l]["dot_id"]).unclick(go_back)
		// 	}
		// }

		// for (var i = 0; i < options.length; i++) {
		// 	if (options[i][0].id !=id) {
		// 		options[i].remove()
		// 	}
		// }
		// for (var j = 0; j < options_data.length; j++) {
		// 	if (options_data[j]["dot_id"] != id) {
		// 		paper.getById(options_data[j]["dot_id"]).remove()
		// 		paper.getById(options_data[j]["title_text_id"]).remove()
		// 		paper.getById(options_data[j]["entity_text_id"]).remove()
		// 		paper.getById(options_data[j]["prop_text_id"]).remove()
		// 	}
		// }


		

		// pop remaining dot from options (the one that was clicked)
		// var clicked_group = options.pop();
		
		// chosen_path.push(clicked_group);
		console.log(dot.data('entity_name'),dot.data('pos_title'));
		chosen_data.push({"dot_id":el.id, "pos_id":el.data("pos_id"), "ideal_id": el.data("ideal_id"), "entity_name":dot.data('entity_name'),"pos_title":el.data("pos_title")})
		render_chosen_path();
		// Move selected elements && change styling
		// el.animate({'cy':midline, 'fill':'#2980b9'}, '500', '<>')
		// title_text.animate({"x":x_start + (dot_distance * chosen_data.length), "y": title_y}, '500','<>')
		// entity_text.animate({"x":x_start + (dot_distance * chosen_data.length), "y": entity_name_y}, '500','<>')


		// Unbind Events
		// while(el.events.length) {
		// 	var e = el.events.pop()
		// 	e.unbind()
		// }

		// because most recent, bind "go back" event
		el.click(go_back)		

	
		
		// update data structure
		
		options_data.length = 0
		
		current_option_index = 0

		// get and render next options
		get_and_render_options(ideal_id,start_pos_id);
	}


	/**************/
	/* AJAX Calls */
	/**************/

	var get_options = function(ideal_id,pos_id) {

		/* NOTE: using synchronous AJAX call to hold the chain until
			returns. Consider changing this to one big callback */

		var ret_val = null
		// console.log("Ids for Ajax call:",ideal_id,pos_id)
		jQuery.ajaxSetup({async:false})

		$.get("/careers/getNextBuildStepIdeal/", {'id':ideal_id,'pos_id':pos_id}, function(response) {
			var length = (response.length > 5) ? 5 : response.length;
			// y_offset = Math.ceil(y_range/(length - 1)) // assuming 5 options...
			ret_val = response
			console.log(ret_val);
		}, "json");

		jQuery.ajaxSetup({async:true})
		return ret_val
	};


	var save_attempted = false
	var save = function() {

		// Animate to show clicked
		$('#build-save-button').fadeOut(100).fadeIn(100)

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

		var position_ids = []
		for (var g = 0; g < chosen_data.length; g++) {
			position_ids.push(chosen_data[g]["pos_id"])
		}

		// Don't allow path of length 0 to save
		if (position_ids.length == 0) {
			$('#are-you-sure-prompt').html("There are no positions in this path! Start adding positions below.").css("visibility", "visible");
			return false;
		} 


		// If no title, prod the users for one
		if (title == "Untitled" && !save_attempted) {
			$('#are-you-sure-prompt').html("Want to give this path a title? Click on the title above to give it a name.").css("visibility", "visible");
			
			save_attempted = true;
			return false;
		}


		console.log("Pre-save: [title:" + title + "] [position_ids:" + position_ids + "] [path_id:" + path_id + ']')

		// Post to DB
		$.post("/careers/saveBuildPath/",
			{'title':title, 'position_ids':position_ids, 'path_id':path_id, 'csrfmiddlewaretoken':"csrf_token"},
			function(response) {
				if (response["result"] == "success") {
					console.log("Success")
					$('.save-button').html("Saved")

					// Now that saved, cab be deleted
					var delete_html = "<div id='delete-button'  onclick='delete_path()'>Delete</div>"
					$('#delete-button-container').html(delete_html)

					$('#comments-container').css("visibility", "visible").append("No comments yet")

					// Set new path id
					path_id = response["path_id"]
					console.log("new path id set to : " + path_id)

					$('#are-you-sure-prompt').empty().css("visibility", "hidden")

				} else {
					console.log("Failure: " + response["errors"])
				}
			},
			"json"
		)

	};
});


	// Hover handler - blue highlight 
	$('#build-positions-table tr').hover(function(ev) {
		$(ev.currentTarget).toggleClass("info")
	}, function(ev) {
		$(ev.currentTarget).toggleClass("info")
	});

	

	var position_selected_pos_id = null
	var position_selected_title = null
	var position_selected_entity_name = null
	var position_selected_ideal_id = null
	var position_selected_text = null

	// Autocomplete for current position
	$('#build-positions-search-box').autocomplete({
    	serviceUrl: '/careers/positionAutocomplete/',
    	minChars: 2,
    	onSelect: function(suggestion) {

    		position_selected_text = $('#build-positions-search-box').val()
			position_selected_pos_id = suggestion.pos_id
			position_selected_title = suggestion.title
			position_selected_entity_name = suggestion.entity_name
			position_selected_ideal_id = suggestion.ideal_id
	    }
    });

	// Add click handler to search box
    $('#add-build-position-button').click(function(ev) {

    	var text = $('#build-positions-search-box').val()

    	if (text != position_selected_text || text.length == 0) {
    		$('.control-group').each(function() {
    			$(this).toggleClass("error").append("<label class='control-label' id='error-label' style='visibility:hidden' for='build-positions-search-box'>Sorry, please select a position from the search box.</label>")
    			$('#error-label').css('visibility','visible').hide().fadeIn(500)
    		})
    		return false;
    	}

    	// Remove previous warning labels if applicable, animate box
    	$('.control-label').each(function() { $(this).remove(); });
    	$('.control-group').each(function() { $(this).removeClass("error") });
    	$('#build-positions-search-box').val("").fadeOut(175).fadeIn(175).fadeOut(175).fadeIn(175)

    	// If there's something there
		add_first_position(position_selected_pos_id, position_selected_ideal_id, position_selected_title, position_selected_entity_name)

		// Add click handler to row
		$('#build-positions-table td:last').click(current_position_clicked)

		// Add to "current" list
		current_pos.push({'entity_name':position_selected_entity_name, 'ideal_id':position_selected_ideal_id, 'pos_id':position_selected_pos_id, 'title':position_selected_title})
    });



	// Title change handlers....
	var enterPressed = function(ev) {
		if (ev.which == 13 && $('.build-input').length > 0) {
			$('.build-header-name').html($('.build-input').val()).removeClass("italicize").click(title_change_handler)
			$(document).off("keypress")
		} else if (ev.which == 13 && $('.build-input').length == 0) {
			$('.build-header-name').html("Untitled").click(title_change_handler)
		}
	};

	var title_change_handler = function(ev) {
		var current_text = $('.build-header-name').html()
		var new_html = "<input class='build-input' type='text' placeholder='" + current_text + "' name='path-title-input'>"
		$('.build-header-name').html(new_html).off("click")
		$(document).keypress(enterPressed)
	};

	$('.build-header-name').click(title_change_handler)

	/* Eventually, allow user to click off and save */
		// $(document).click(function(ev) {
		// 	if ($(ev.currentTarget) != $(this)) {
		// 		alert("clicked off this")
		// 	} else {
		// 		alert("clicked this")
		// 	}
		// })

// For Comment Textarea Button show/hide
var checkCommentButton = function() {
	if ($('#comment-textarea').val().length > 0)
		$('#comment-button').css('visibility', 'visible')
	else 
		$('#comment-button').css('visibility', 'hidden')
}

// To Make Comment (AJAX)
var submitComment = function() {
	var comment = $('#comment-textarea').val()

	$.post("/social/saveComment/", {'path_id':path_id, 'body':comment, 'type':"path", 'csrfmiddlewaretoken':"csrf_token"},
	function(response) {
		if (response["result"] == "success") {
			console.log("Success")

			// Append new comment to comments
			var template = _.template($('#inline-comment-template').html())

			$('#comments-container-header').after(template({
				'profile_pic':response["profile_pic"],
				'user_name':response["user_name"],
				'date_created':response["date_created"],
				'body':comment,
			}))

			// Clear comment box
			$('#comment-textarea').val("")

		} else {
			console.log("Failure: " + response["errors"])
		}
	},"json");
}

/****************/
/* SVG for Path */
/****************/



/* Create Paper */


/* If existing path elements, render those first */
var render_existing_path = function() {

	var positions = path_steps
	if (positions == null || positions.length == 0) return false;

	for (var e = 0; e < positions.length; e++) {
		
		var title = positions[e].title
		var entity_name = positions[e].entity_name
		var pos_id = positions[e].pos_id
		var ideal_id = positions[e].ideal_id
		var x = x_start + (chosen_data.length * dot_distance)

		// Alternate location of text
		if (e % 2 == 0) {
			var title_y = midline - text_offset1
			var entity_name_y = midline - text_offset2
		}
		else {
			var title_y = midline + text_offset2
			var entity_name_y = midline + text_offset1
		}

		/* Create SVG Elements */
		var dot = paper.circle(x, midline, dot_radius).attr(saved_dot_attributes)
		var title_text = paper.text(x, title_y, title).attr(text_attributes)
		var entity_text = paper.text(x, entity_name_y, entity_name).attr(text_attributes)

		/* Set relevant data on dot element */
		dot.data("pos_id", pos_id)
		dot.data("title_text_id", title_text.id)
		dot.data("entity_text_id", entity_text.id)
		dot.data("ideal_id", ideal_id)

		/* Update data structure */
		chosen_data.push({"dot_id":dot.id, "pos_id":pos_id, "ideal_id": ideal_id})

		/* Draw connecting line */
		if (e > 0) {
			var line = paper.path("M" + (x_start + ((chosen_data.length - 2) * dot_distance) + dot_radius + 4) + ', ' + midline + ' L' + (x_start + ((chosen_data.length - 1) * dot_distance) - dot_radius - 4) + ','  + midline).attr(chosen_line_attributes)
			line_data.push(line.id)
		}			
	}

	/* Add 'back' to last dot */
	dot.click(go_back)

	/* Get and render options */
	get_and_render_options(ideal_id,pos_id)
};












/******************/
/* Event Handlers */
/******************/




















var delete_path = function(ev) {

	$.post("/careers/deleteSavedPath/", {'id':path_id, 'csrfmiddlewaretoken': "csrf_token"}, function(response) {
		if (response["result"] == "success") {
			console.log("Success")

			$('#delete-button').fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100)

			// Once deleted... go to a new path
			window.location = "/build/"
			
		} else {
			console.log("Failure: " + response["errors"])
		}
	}, "json");
};


/***********/
/* Helpers */
/***********/
var remove_options = function() {

	// Delete option dots, titles, entity names
	for (var j = 0; j < options_data.length; j++) {
		paper.getById(options_data[j]["dot_id"]).remove()
		paper.getById(options_data[j]["title_text_id"]).remove()
		paper.getById(options_data[j]["entity_text_id"]).remove()
		paper.getById(options_data[j]["prop_text_id"]).remove()
	}
	options_data.length = 0
	current_option_index = 0
}

var add_position_to_current_table = function(pos_id, ideal_id, title, entity_name) {
	normalize_rows();

	var new_html = "<tr class='selected'><td class='build-start-position' data-pos_id='"+ pos_id + "' data-title='" + title + "' data-entity_name='" + entity_name + "' data-ideal_id='"+ ideal_id + "'>" + title + " at " + entity_name + " </td></tr>"
	$('#build-positions-table > tbody:last').append(new_html)
};





var normalize_rows = function() {
	// Color all rows white
	$('#build-positions-table tr').each(function() {
		
		// If it was already selected, unselect and re-add hover //		handler
		if ($(this).hasClass("selected")) {
			$(this).removeClass("selected").hover(function(ev) {
				$(ev.currentTarget).toggleClass("info")
			}, function(ev) {
				$(ev.currentTarget).toggleClass("info")
			});
		}
	});
};



