


// Note: pass the later dates as mo2 and yr2

	var upper_timeline_limit = 200;

	var months_difference = function(mo1, yr1, mo2, yr2, compress, round) {
		var diff = 12 * (yr2 - yr1);
		diff += (mo2 - mo1);

		if(compress) {
			diff = diff / 2
			if (round == "upper") diff = Math.ceil(diff)
			if (round == "lower") diff = Math.floor(diff)
		}
		return diff;
	};

	var prepare_for_timeline = function(list) {
		// First, sort list by start date
		list = _.sortBy(list, function(current) {
			return current.start_date.substring(3) + current.start_date.substring(0,2)				
		});

		var start_mo = list[0].start_date.substring(0,2)
		var start_yr = list[0].start_date.substring(3)

		// for now, let's assume that they're doing something currently
		var d = new Date()
		var end_mo = d.getMonth() + 1
		var end_yr = d.getFullYear()

		var total_time = months_difference(parseInt(start_mo), parseInt(start_yr), end_mo, end_yr, false)
						
		list['total_time'] = total_time
		list['start_mo'] = start_mo
		list['start_yr'] = start_yr
		return list
	};

	var timeline_hover_in = function(elem, index) {
		var timeline_class = $(elem).attr("class")
		var u_id = timeline_class.match(/\d+/g);
		document.getElementsByClassName(u_id + '-timeline')[index].style.border="1px solid blue"
	}

	var timeline_hover_out = function(elem, index) {
		var u_id = $(elem).attr('class').match(/\d+/g);
		document.getElementsByClassName(u_id + '-timeline')[index].style.border="none"
	}

	var positionClicked = function(classname, index) {
		// Grab the description element
		var parent = document.getElementsByClassName(classname)[index]
		var description = parent.getElementsByClassName('timeline-description')[0]
		var header = parent.getElementsByClassName('timeline-header')[0]

		// If hidden, show; if shown, hide
		if (description.style.display == "none") {
			description.style.display="inherit"
			header.style.fontWeight="bold"
			header.parentNode.style.borderTop="1px solid black"
			header.parentNode.style.borderLeft="1px solid black"
			header.parentNode.style.borderRight="1px solid black"
			header.parentNode.style.borderRadius="4px 4px 0px 0px"
		} else {
			description.style.display="none"
			header.style.fontWeight="normal"
			header.parentNode.style.border="none"
			header.parentNode.style.borderRadius="none"
		}
	}

	var create_path_and_add_position = function(parent) {
		var title = parent.getElementsByClassName('save_path_box_form_title')[0].value
		var pos_id = parent.getElementsByClassName('save_path_box_form_position')[0].value

		// Todo: add error messages for this
		if (title.length == 0 || title.length > 32) return

		console.log('create new path. title: ' + title + ', pos_id: ' + pos_id)
		window.location='/saved_paths/create/' + title + '/' + pos_id + '/'	
	}

	var open_saved_paths = function(saved_paths, elem, pos_id) {
		
		// THIS DOES NOT WORK YET
		// Don't make another box if one is already there. Delete it.
		var existing_boxes = elem.getElementsByClassName('save_path_box')
		if (existing_boxes.length != 0) {
			console.log(existing_boxes)
			elem.removeChild(existing_boxes[0])
		}

		// Create a new element
		var path_box = document.createElement('div')
		path_box.setAttribute('class', 'save_path_box')
		
		// If existing paths, show them:
		if (saved_paths.length > 0) {
			var headerString  = '<div class="save_path_box_header">Add this job to one of your career paths: </div>'
			headerString += '<ul class="save_path_box_existing_list">'
			path_box.innerHTML = headerString

			// Add to existing saved paths
			for(var i = 0; i < saved_paths.length; i++) {
				var divString = '<li class="save_path_box_existing_elem">'
				divString += '<a href="/saved_paths/save/' + saved_paths[i] + '/' + pos_id + '/">'
				divString += saved_paths[i]
				divString += '</a></li>'

				path_box.innerHTML += divString
			}

			path_box.innerHTML += '</ul>'
		}

		// Or, allow user to create a new path
		var createForm = '<div><div class="save_path_box_header">Or create a new career path.</div>'
		createForm += '<input class="save_path_box_form_title" placeholder="Enter new title here..." type="text" name="title" min="1" max="32">'
		createForm += '<input class="save_path_box_form_position" type="hidden" name="pos_id" value="' + pos_id + '">'
		createForm += '<input class="btn btn-small" type="submit" value="Create" onclick="create_path_and_add_position(this.parentNode)"/>'
		createForm += '</div>'
		

		path_box.innerHTML += createForm

		// Finally, add new element to the dom
		elem.appendChild(path_box)
	};


