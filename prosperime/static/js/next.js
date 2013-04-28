
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.IndustryChange = Backbone.Model.extend({
		// nothing... is this even needed?
	});



	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.IndustryChanges = Backbone.Collection.extend({

		urlRoot: '/next/',
		model: IndustryChange, 

		initialize: function() {
			this._meta = {}
		},

		url: function() {	
			url = this.urlRoot
			if (this._meta['q1']) url = this.urlRoot + this._meta['q1']		
			if (this._meta['q2']) url += '&' + this._meta['q2']
			return url
		},

	});

	
	// Instantiate Collections
	window.changes = new IndustryChanges;

	//-------------//
	// ** Views ** //
	//-------------//


	/* * * Header View * * */
	window.HeaderView = Backbone.View.extend ({

		el: $('#header-container'),
		template: _.template($('#header-template').html()),

		events: {
			"click #save-button":"saveIndustry",
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'saveIndustry');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			var model = collection.models[0]

			console.log(model)

			// Check if this is a new search. If so, allow user to 
			// bookmark this industry
			var new_industry = true
			for (var i = 0; i < model.get('related_industries').length; i++) {
				if (model.get('start_id') == model.get('related_industries')[i][0])
					new_industry = false
			};

			if (new_industry) {
				var new_el = "<div id='save-button' class='pull-right inline-block people-box' data-id='" + model.get('start_id') + "'>Save this search</div>"
				$('#lvl1-header-container').append(new_el)

				// Attach click handler to button after added
				var id = model.get('start_id')
				$('#save-button').on("click", function() {
					var id = $(this).data("id")

					// Make sure industry not a duplicate!
					for (var h = 0; h < model.get('related_industries'); h++) {
						if (id == model.get('related_industries')[h][0]) {
							return false;
						}
					}

					// Save Industry
					$.post('/careers/addIndustry/', {
						id:id}, function(response) {
							if (response["result"] == "success") {
								console.log("Success")
								// $('#save-button').fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100)
							} else {
								console.log("Failed to save industry: " + response["errors"])
							}
						}, "json");
					collection.fetch()
					collection.render()
				})
			}

			this.$el.append(this.template({
				'industries':model.get('related_industries'),
				'current':model.get('start_name'),
			}));

			return this;
		},

		remove: function() {
			$(this.el).empty().detach()
			return this
		},

		saveIndustry: function(id) {

			console.log("save: " + id)
		},
	});

	/* * * Filters View * * */
	window.FiltersView = Backbone.View.extend({
		el: $('#search-filters-container'),
		template: _.template($('#search-filters-template').html()),

		events: {
			'click input.search-filters':'checkboxSelected',

		},

		initialize: function() {
			_.bindAll(this,'render', 'checkboxSelected');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);

			/* Filters Constants */
			// this.lvl1filters = ['Most Common', 'Red Herring', 'My Network', 'Prosperime Community'] 
			this.lvl1filters = ['Most Common']
			this.lvl2filters = ['Entity']
		},

		render: function() {
			console.log('2')
			this.$el.empty()
			var level = this.collection.models[0].get('lvl')
			if (level == 1) var filters = this.lvl1filters
			else var filters = this.lvl2filters
			this.$el.append(this.template({'filters':filters}))

			this.collection.models[0].set({'ordering':'decreasing'})
			
		},

		checkboxSelected: function() {
			// console.log(this.collection.models[0].get('transitions'))
			// this.collection.models[0].set({'ordering':'increasing'})
			// var model = this.collection.models[0]
			// this.collection.reset(model)
		},
	});



	/* * * 1 * * */
	window.Lvl1View = Backbone.View.extend ({

		el: $('#search-results-container'),
		template: _.template($('#lvl1-template').html()),

		events: {
			'mouseenter #search-results-table-lvl1 tbody tr': 'tableOver',
			'mouseleave #search-results-table-lvl1 tbody tr': 'tableOut',
			'click #search-results-table-lvl1 tbody tr': 'changeClicked',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'tableOver', 'tableOut', 'changeClicked');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			console.log('render')
			this.$el.empty()
			var collection = this.collection // important! (context)
			var model = collection.models[0]

			this.$el.append(this.template({
				'start_id':model.get('start_id'),
				'start_name':model.get('start_name'),
				'total_people':model.get('total_people'),
				'transitions':model.get('transitions'),
				'ordering':model.get('ordering'),
			}))

			$('#industry-header').html(model.get('start_name'))

			return this;
		},


		tableOver: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		tableOut: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		changeClicked: function(ev) {
			var row_id =  $(ev.currentTarget).attr('id')
			var from = row_id.split('-')[0]
			var to = row_id.split('-')[1]
			// this.collection._meta['q1'] = '#?i1='+from
			// this.collection._meta['q2'] = 'i2='+to
			// var url = this.collection.url()
			var url = '?i1='+from+'&i2='+to
			console.log(url)
			App.navigate(url, {trigger:true})

		},

	});

	/* * * 2 * * */
	window.Lvl2View = Backbone.View.extend ({

		el: $('#search-results-container'),
		template: _.template($('#lvl2-template').html()),

		events: {
			'mouseenter #search-results-table-lvl2 tbody tr': 'tableOver',
			'mouseleave #search-results-table-lvl2 tbody tr': 'tableOut',
			'click span.previous-search':'goBack',
			'click #search-results-table-lvl2 tbody tr':'goToProfile',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'tableOver', 'tableOut', 'goToProfile', 'goBack');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			console.log(collection)

			var model = collection.models[0]

			this.$el.append(this.template({
				'start_id':model.get('start_id'),
				'start_name':model.get('start_name'),
				'end_id':model.get('end_id'),
				'end_name':model.get('end_name'),
				'total_people':model.get('total_people'),
				'people':model.get('people'),
			}))

			$('#industry-header').html(model.get('start_name'))

			// Now add timelines
			var constants = {
				'paper_w':700,
				'paper_h':100,
				'midline':50,
				'start_offset':0,
				'padding':3,
				'top_text_offset':37,
				'bottom_text_offset':23,
				'box_style':3,
			}

			_.each(model.get('people'), function(value, key) {

				var move = value[1]
				var positions = [{'title':move.start_title, 'org':move.start_entity_name}, {'title':move.end_title, 'org':move.end_entity_name}]
				monospaced_timeline(constants, positions, "content-"+ key)

			});

			return this;
		},

		tableOver: function(ev) {
			$(ev.currentTarget).toggleClass('info')
			// $(ev.currentTarget).children(".first-col").children(".flat-button").toggleClass("hide")
		},

		tableOut: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		goToProfile: function(ev) {
			var row_id =  $(ev.currentTarget).attr('id')
			window.location = "/profile/" + row_id + "/"
		},

		// Returns to lvl1 search by manipulating url
		goBack: function(ev) {
			var current = window.location.toString()
			App.navigate(current.substring(current.indexOf('?'), current.indexOf('&')), {trigger:true})
		},
	});


	window.DotLvl1View = Backbone.View.extend({

		el:$('#search-results-container'),


		initialize: function() {
			_.bindAll(this,'render', 'industryClicked', 'back');
			this.collection.on('change', this.render, this);
			this.collection.on('reset',this.render, this);

		},

		render: function() {
			console.log(this.collection)

			clear_svg()
			render_dot_lvl1_viz(this.collection, this.industryClicked)
		},

		back: function(data, dot, paper) {

			// First, delete existing stuff
			var paperDom = paper.canvas;
    		paperDom.parentNode.removeChild(paperDom); // From StackOverflow... 
    		paper.remove()
    		dot_ids.length = 0
    		option_dot_ids.length = 0
    		lvl2_elem_ids.length = 0

			// Then, re-draw...
			//	TODO: fix - this hits HTTP (although cached), not needed
			window.changes.fetch()
		},

		industryClicked:function(i2_data, dot_clicked, paper) {

			// First, delete all other options
			for (var j = 0; j < dot_ids.length; j++) {
				if (dot_ids[j] != dot_clicked.id) {
					// Delete line, number, label, then dot
					var dot = paper.getById(dot_ids[j])
					paper.getById(dot.data("line_id")).remove()
					paper.getById(dot.data("label_id")).remove()
					paper.getById(dot.data("number_id")).remove()
					dot.remove()
				} else {
					// Delete line, label
					paper.getById(dot_clicked.data("line_id")).remove()
					paper.getById(dot_clicked.data("label_id")).remove()
				}
			};

			// Reset dot_ids to only include chosen dot
			// NOTE: may be faster and hide and move rather than delete and redraw
			dot_ids = [dot_clicked.id]

			// Next, animate chosen industry to other side
			animate_clicked_dot(dot_clicked, paper, i2_data[0], this.back)

			// Finally, connect dots
			draw_lvl2_connections(i2_data, paper)
		},

	

	});


	//---------------//
	// ** Routers ** //
	//---------------//
	window.NextRouter = Backbone.Router.extend({
		routes: {
			'':'empty',
			':query&:query':'doubleQuery',
			':query':'singleQuery',

		},

		initialize: function() {
			this.changes = window.changes;

		},

		empty: function() {
			console.log('empty search')
		},

		singleQuery: function(query) {
			console.log('single query: ' + query)
			// this.filterView = new FiltersView({collection:this.changes})
			// this.lvl1view = new Lvl1View({collection:this.changes})

			// // Keep this call last
			// this.headerview = new HeaderView({collection:this.changes})


			this.dot1View = new DotLvl1View({collection:this.changes})
			this.changes._meta['q1'] = query
			this.changes._meta['q2'] = null
			this.changes.fetch()

		},

		doubleQuery: function(q1, q2) {
			console.log('double query: ' + q1 + ' ' + q2)

			if (q2 == 'undefined') {
				App.history.back()
				App.history.back()
				return
			}

			this.filterView = new FiltersView({collection:this.changes})
			this.lvl2view = new Lvl2View({collection:this.changes})
			this.changes._meta['q1'] = q1
			this.changes._meta['q2'] = q2
			this.changes.fetch()

		},
	});


	window.App = new NextRouter();
	
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});


/* Constants */
var start_dot_r = 50
var paper_w = 1000
var paper_h = 450
var midline = (paper_h / 2) + 25
var max_r = get_max_radius()
var y_range = paper_h - (2 * max_r) // set in helpers.js = 50
var y_max = y_range / 2
var text_buffer = 15
var start_x = 150
var options_x = 400
var max_options = 5 // max # industries to show
var max_names = 3 // max # names of related people to show
var i2_x = 825
var header_y = 25
var l2_line_length = 25
var l2_p1 = start_x+200
var l2_p2 = i2_x-200
var p1_start = start_x + start_dot_r + l2_line_length
var p2_start = i2_x - start_dot_r - l2_line_length

/* Containers */
var dot_ids = []
var option_dot_ids = []
var industry_dot_ids = []
var lvl2_elem_ids = []

/* Attributes */
var chosen_dot_attributes = {
	'fill':'rgb(41,98,152)',
	'stroke-width':0,
	'cursor':'pointer'
};

var option_dot_attributes = {
	'fill':'#679FD2',
	'stroke-width':0,
	'cursor':'pointer'
};

var number_attributes = {
	'stroke':'#fffffe',
	'font-size':14,
	'cursor':'pointer',
	'font-fmamily':"'Source Sans Pro', 'Helvetica'"
}

var label_attributes = {
	'font-size':24,
	'font-family':"'Source Sans Pro', 'Helvetica'"
}


var option_label_attributes = {
	'text-anchor':'start',
	'font-size':14,
}

var l2_text_attributes = {
	'font-size':14,
	'font-family':'"Source Sans Pro", "Helvetica"',
	'cursor':'pointer'
}

// Convenience, holds major data structures needed to redraw svg
//	keeps us from having to pass variables between svg methods and
//	backbone (messy)
var svg_wrapper = {
	'paper':null,
	'collection':null,
	'transitions':null,
	'transition_data':null,
	'lvl1_index':0,
	'lvl2_index':0,
	'clickhandler':null,
};


var render_dot_lvl1_viz = function(collection, clickhandler) {

	// Create paper, sort transitions by num people
	var paper = new Raphael('svg-main-container',paper_w,paper_h)
	var data = collection.models[0].attributes
	transitions = _.sortBy(data['transitions'], function(value) {return -value[1];})
	var length = (transitions.length > max_options) ? max_options : transitions.length

	// Set wrapper variables
	svg_wrapper['paper'] = paper
	svg_wrapper['collection'] = collection
	svg_wrapper['transitions'] = transitions
	svg_wrapper['lvl1_index'] = length
	svg_wrapper['clickhandler'] = clickhandler

	// Draw dots, lines, and text
	draw_lvl1_elems(clickhandler, length, 0)

	/* Construct SVG for Start Industry Last (highest Z value) */
	draw_start_elems(data["total_people"], paper)
	var start_label = paper.text(start_x,header_y,"From: " +  data["start_name"]).attr(label_attributes)
};



// Animates clicked dot to the right side of the screen, increases
//	its size, changes color, and adds an industry label
var animate_clicked_dot = function(dot, paper, industry_name, back_handler) {
	
	// Animate dot and number
	paper.getById(dot.data("number_id")).animate({'x':i2_x, 'y':midline}, '2e1')
	dot.animate({'cx':i2_x, 'cy':midline}, '2e1')
	dot.attr(chosen_dot_attributes)
	dot.attr("r",start_dot_r)

	// Create new industry label, add id to dot
	var industry_label = paper.text(i2_x, header_y, "To: " + industry_name).attr(label_attributes)
	dot.data("industry_label_id", industry_label.id)

	// ? var back_arrow = paper.path("M"+(i2_x-10)+"," +header_y+" L"+(i2_x-5)+","+(header_y-5)+" L"+(i2_x-5)+","+(header_y+5)).attr({'stroke-width':10});

	// Unbind old click events and bind "back" handler
	unbind_events(dot)
	unbind_events(paper.getById(dot.data("number_id")))
	set_click_handlers(dot, paper.getById(dot.data("number_id")), [], back_handler, paper)
};


var draw_lvl2_connections = function(data, paper) {

	var keys = Object.keys(data[2])
	var length = (keys.length > 5) ? 5 : keys.length;

	if (keys.length > 5) render_option_dots(paper, true, 2)
	else render_option_dots(paper, false, 2)

	var line_left = paper.path("M" + (start_x + start_dot_r) + ", " + midline + " L" +p1_start+ ", "+midline)
	var line_right = paper.path("M" + (i2_x - start_dot_r) + ", " + midline + " L" +p2_start+ ", "+midline)

	svg_wrapper["transition_data"] = data
	svg_wrapper["lvl2_index"] = length


	draw_lvl2_elems(data, keys, length, 0)


};



var render_option_dots = function(paper, is_active, level) {

	// Render dots for the first time
	if (option_dot_ids.length == 0) {
		var dot = paper.circle((start_x + i2_x) / 2, 25, 21).attr({
			'fill':'#C0392B',
			'stroke-width':0,
		});

		var chevron = paper.path("M"+((start_x+i2_x)/2 - 10)+","+(20)+"L"+((start_x+i2_x)/2)+","+(35)+" L"+((start_x+i2_x)/2 + 10)+","+20+" L"+((start_x+i2_x)/2 -10)+","+20).attr({
			'stroke':'#fffffe',
			'fill':'#fffffe'
		});

		// Add data to dot and update DST
		dot.data("chevron_id",chevron.id)
		option_dot_ids.push(dot.id)


		// Add click handlers
		if (is_active)
			set_handlers([dot,chevron], option_handler, level)
		else
			dot.attr('fill', '#ECF0F1')

	// Or, update to active
	} else if (is_active) {
		// unbind old events
		var dot = paper.getById(option_dot_ids[0])
		unbind_events(dot)
		unbind_events(paper.getById(dot.data("chevron_id")))

		// bind new events
		set_handlers([dot, paper.getById(dot.data("chevron_id"))], option_handler, level)

		dot.attr('fill', '#C0392B')

	// Or, update to inactive
	} else { 
		// unbind events
		var dot = paper.getById(option_dot_ids[0])
		unbind_events(dot)
		unbind_events(paper.getById(dot.data("chevron_id")))

		// change color of dot
		dot.attr('fill','#ECF0F1')

	}
};

// Click event on red option arrow
var option_handler = function(level) {
	console.log("option_handler called w/ level:" + level)

	// Render more industry changes
	if (level == 1) {

		// Get metadata
		var transitions = svg_wrapper["transitions"]
		var current_index = svg_wrapper["lvl1_index"]

		// Delete what's currently there
		delete_lvl1()

		// Redraw i2 dots & set index for next click
		if (transitions.length >= current_index + 5) {
			draw_lvl1_elems(svg_wrapper["clickhandler"], 5, current_index)
			svg_wrapper["lvl1_index"] = current_index + 5
		} else {
			var remainder = transitions.length - current_index
			draw_lvl1_elems(svg_wrapper["clickhandler"], remainder, current_index)
			svg_wrapper["lvl1_index"] = 0
		}

		// Redraw start dot
		draw_start_elems(svg_wrapper["collection"].models[0].attributes["total_people"], svg_wrapper["paper"])

	// Render more people
	} else {
		// console.log("currently rendering: " + svg_wrapper["lvl2_index"])
		var data = svg_wrapper["transition_data"]
		var keys = Object.keys(data[2])
		var current_index = svg_wrapper["lvl2_index"]

		delete_lvl2()
		console.log(current_index)
		if (keys.length >= current_index + 5) {
			draw_lvl2_elems(data, keys, 5, current_index)
			svg_wrapper["lvl2_index"] = current_index + 5
		} else {
			var remainder = keys.length - current_index
			draw_lvl2_elems(data, keys, remainder, current_index)
			svg_wrapper["lvl2_index"] = 0
		}
	}
};


// Helper function draws transition lines, dots, numbers, and text
var draw_lvl1_elems = function(clickhandler, length, start_index) {

	var paper = svg_wrapper["paper"]
	var data = svg_wrapper["collection"].models[0].attributes

	if (transitions.length > 5) render_option_dots(paper, true, 1)
	else render_option_dots(paper, false, 1)

	// Main loop for drawing dots
	for (var i = start_index; i < start_index + length; i++) {

		// Used for original indexing (spacing, mostly)
		var effective_i = i % 5
		var y_offset = Math.ceil(y_range/(length - 1))

		// Construct line to dot
		if (length == 1) {
			var hinge = midline
			var y = midline
		} else {
			var y = midline - y_max + (y_offset * effective_i)
			var hinge = (y > midline)? y + 10 : y - 10
		}


		// Calls helper to size dot relative to total_people 
		var dot_r = size_dot(data['total_people'], transitions[i][1])

		// Construct dot w/ number in the middle
		var dot = paper.circle(options_x,y,dot_r).attr(option_dot_attributes)
		var number = paper.text(options_x,y,transitions[i][1]).attr(number_attributes)
	
		
		var line = paper.path("M"+start_x+', '+midline+"Q125, " + hinge  + " " + (options_x-dot_r) + "," + y)
	
		// Construct labels of related people
		var people_keys = Object.keys(transitions[i][2])
		var names_length = (people_keys.length > max_names) ? max_names : people_keys.length
		var label_text = transitions[i][0] + "    ("
		for (var j = 0; j < names_length; j++) {
			var name = transitions[i][2][people_keys[j]][0]
			if (j < names_length - 1) label_text += name + ', '
			else label_text += name + ')'
		}
		var label = paper.text(options_x+dot_r+text_buffer, y, label_text).attr(option_label_attributes)
		
		// Set click handlers
		set_click_handlers(dot, number, transitions[i], clickhandler, paper)

		// Set data on dot element, push id to DST
		dot.data('label_id', label.id)
		dot.data('number_id', number.id)
		dot.data('line_id', line.id)
		dot_ids.push(dot.id)
	}
}

var draw_lvl2_elems = function(data, keys, length, start_index) {

	var paper = svg_wrapper["paper"]

	// Iterate through, add line segments, dots, and text
	for (var i = start_index; i < start_index + length; i++) {

		var effective_i = i % 5
		var y_offset = Math.ceil(y_range/(length - 1))

		var transition = data[2][keys[i]]
		console.log(transition)

		if (length == 1) {
			var y = midline
			var hinge = midline
		} else {
			var y = midline - y_max + (y_offset * effective_i)
			var hinge = (y > midline)? y + 10 : y - 10
		}

		var l1 = paper.path("M"+p1_start+', '+midline+" Q" + (p1_start+l2_line_length) + ", " + hinge  + " " + (l2_p1) + "," + y)
		var node1 = paper.circle(l2_p1, y, 8).attr(option_dot_attributes)
		var l2 = paper.path("M"+p2_start+", "+midline+" Q"+ (p2_start-l2_line_length)+", "+hinge+" "+(l2_p2)+","+y)
		var node2 = paper.circle(l2_p2, y, 8).attr(option_dot_attributes)
		var connector_line = paper.path("M" + (l2_p1 + 8) + ", " + y + " L" + (l2_p2 - 8) + ", " + y)
	
		// Start Entity, End Entity, Person Name
		var node1_text = paper.text(l2_p1, y - 18, transition[1]['start_entity_name']).attr(l2_text_attributes)
		var node2_text = paper.text(l2_p2, y - 18, transition[1]['end_entity_name']).attr(l2_text_attributes)
		var connector_text = paper.text((start_x + i2_x) / 2, y+14, transition[0]).attr(l2_text_attributes);
		
		var handler = function(id) { window.location="/profile/" + id }
		set_handlers([node1_text, node2_text, connector_text], handler, keys[i])
	
		var ids = [l1.id, node1.id, l2.id, node2.id, connector_line.id, node1_text.id, node2_text.id, connector_text.id]
		lvl2_elem_ids.push(ids)
	};
}

// Deletes all dots, lines, numbers, and text
var delete_lvl1 = function() {
	var paper = svg_wrapper["paper"]
	for (var l = 0; l < dot_ids.length; l++) {
		var dot = paper.getById(dot_ids[l])
		paper.getById(dot.data("label_id")).remove()
		paper.getById(dot.data("number_id")).remove()
		paper.getById(dot.data("line_id")).remove()
		dot.remove()
	};
	dot_ids.length = 0

	var start_dot = paper.getById(industry_dot_ids[0])
	paper.getById(start_dot.data("number_id")).remove()
	start_dot.remove()

	industry_dot_ids.splice(0,1)
}

// Deletes all dots, lines, node text, and connector text
var delete_lvl2 = function() {

	var paper = svg_wrapper["paper"]
	for (var n = 0; n < lvl2_elem_ids.length; n++) {
		var ids = lvl2_elem_ids[n]
		for (var m = 0; m < ids.length; m++) {
			paper.getById(ids[m]).remove()
		}
	};

	lvl2_elem_ids.length = 0
};


// Draws i1 dot and number on the left side of the screen
var draw_start_elems = function(total_people, paper) {
	var start_dot = paper.circle(start_x,midline,start_dot_r).attr(chosen_dot_attributes)
	var start_num = paper.text(start_x,midline,total_people).attr(number_attributes)

	// Add data to dot and add to DST (note added @ index 0)
	start_dot.data("number_id", start_num.id)
	industry_dot_ids.splice(0,0,start_dot.id)
}


var clear_svg = function() {
	dot_ids.length = 0;
	option_dot_ids.length = 0;
	industry_dot_ids.length = 0;
	lvl2_elem_ids.length = 0;

	var paper = svg_wrapper["paper"]
	console.log(paper)
	if (paper && paper.width > 0) {
		var paperDom = paper.canvas;
		paperDom.parentNode.removeChild(paperDom); // From StackOverflow... 
		paper.remove()
		svg_wrapper['paper'] = null
	}

}
 



/* Helpers (no knowledge of instance variables, dom) */

// Helper method to set click handlers, needed for namespacing issues
var set_click_handlers = function(dot, number, data, handler, paper) {
	dot.click(function() {
		handler(data, dot, paper)
	});
	number.click(function() {
		handler(data, dot, paper)
	});
};

// Expects an array of items
var set_handlers = function(items, handler, data) {
	for (var n = 0; n < items.length; n++) {
		items[n].click(function() {
			handler(data)
		})
	}
};











