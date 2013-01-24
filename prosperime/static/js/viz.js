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

	var timeline_hover = function(elem, index) {
		timeline_class = $(elem).attr("class")
		u_id = timeline_class.match(/\d+/g);
		document.getElementsByClassName(u_id + '-list')[index].style.fontWeight="bold"
	}

	var timeline_hover_out = function(elem, index) {
		u_id = $(elem).attr('class').match(/\d+/g);
		document.getElementsByClassName(u_id + '-list')[index].style.fontWeight="normal"
	}


