
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.QueuedPosition = Backbone.Model.extend({
		// nothing... is this even needed?
	});

	window.GoalCareer = Backbone.Model.extend({
		// nothing
	});



	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.QueuePath = Backbone.Collection.extend({

		urlRoot: '/saved_path/queue',
		model: QueuedPosition, 

		// comparator: function(collection) {
		// 	return(collection.get('index'))
		// },

		initialize: function() {
			this._meta = {}
		},

		url: function() {	
			return '/saved_paths/queue/'
		},

	});

	
	// Instantiate Collections
	window.queue = new QueuePath;

	/* Not hitting the server for this data, don't need to extend */
	window.goalCareers = new Backbone.Collection(backbone_careers_init_data, {
		model: GoalCareer,
	});


	//-------------//
	// ** Views ** //
	//-------------//


	window.GoalCareerView = Backbone.View.extend({
		el:$('#goal-careers-container'),
		
		events: {
			'click #career-chevron-left':'queueLeft',
			'click #career-chevron-right':'queueRight',
			'mouseenter .queue-position':'mouseEnter',
			'mouseleave .queue-position':'mouseOut',
			'click .queue-position':'goToCareer',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'create_queue_box', 'queueLeft', 'queueRight', 'renderNewBoxes', 'mouseOut', 'mouseEnter', 'goToCareer');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
			this.collection.bind('remove', this.remove);
			this.modelCount = 0
			this.overflow = false
			this.queue_indices = []
			this.render()
		},

		create_queue_box: function(title, id) {
			return '<div class="queue-position" data-id="'+ id + '"><br/>' + title + '</div>'
		},

		render: function() {
			// Add text to header
			$('#goal-careers-header').html('Careers of Interest')

			var collection = this // important! (context)
			var html = ""

			this.collection.each(function(goalCareer) {
				console.log(goalCareer)

				var title = goalCareer.get("title")
				var id = goalCareer.get("id")
				if (collection.modelCount++ < 4)
					html += collection.create_queue_box(title, id)
			});
			if (this.modelCount > 4) {
				collection.queue_indices = [0,1,2,3]
				collection.overflow = true
				html = '<i class="icon-chevron-left icon-3x profile-chevron" id="career-chevron-left"></i>' + html
				html += '<i class="icon-chevron-right icon-3x profile-chevron" id="career-chevron-right"></i>'
			}
			this.$el.html(html)

			return this;
		},

		renderNewBoxes: function() {

			/* Construct New HTML */
			var new_html = '<i class="icon-chevron-left icon-3x profile-chevron" id="career-chevron-left"></i>'
			for (var l = 0; l < 4; l++) {
				var model = this.collection.models[this.queue_indices[l]]
				new_html += this.create_queue_box(model.get('title'), model.get('id'))
			}
			new_html += '<i class="icon-chevron-right icon-3x profile-chevron" id="career-chevron-right"></i>'
			
			/* Append new HTML to DOM */
			this.$el.html(new_html)
		},


		queueLeft: function(ev) {
			if (this.overflow) {

				/* Reorder Queue Indices */
				for (var n = 0; n < this.queue_indices.length; n++) {
					if (this.queue_indices[n] == 0) this.queue_indices[n] = this.modelCount- 1
					else this.queue_indices[n] -= 1
				}
				this.renderNewBoxes()
			}
		},

		queueRight: function(ev) {
			if (this.overflow) {

				/* Reorder Queue Indices */
				for (var q = 0; q < this.queue_indices.length; q++) {
					if (this.queue_indices[q] == (this.modelCount - 1)) this.queue_indices[q] = 0
					else this.queue_indices[q] += 1				
				}
				this.renderNewBoxes()
			}
		},

		mouseEnter: function(ev) {
			if (!$(ev.currentTarget).hasClass('queue-position-hover'))
				$(ev.currentTarget).toggleClass('queue-position-hover')
		},

		mouseOut: function(ev) {
			if ($(ev.currentTarget).hasClass('queue-position-hover'))
				$(ev.currentTarget).removeClass('queue-position-hover')
		},

		goToCareer: function(ev) {
			console.log('here')
			var id = $(ev.currentTarget).data('id')
			window.location = "/career/" + id 

		}

	});


	// Single Saved Path Single View
	window.QueueSingleView = Backbone.View.extend({

		events: {
		
		},

		initialize: function() {
			this.model.on('change', this.render, this); 
			_.bindAll(this, 'render')
			this.model.bind('remove', this.remove)
		},

		render: function() {
			console.log('render el')
			var renderedContent = this.model.toJSON();
			console.log(renderedContent)
			$(this.el).html(renderedContent);
			return this;
		},

	});


	window.QueueListView = Backbone.View.extend ({

		el: $('#queue'),

		events: {
			'click #queue-chevron-left':'queueLeft',
			'click #queue-chevron-right':'queueRight',
			'mouseenter .queue-position':'mouseEnter',
			'mouseleave .queue-position':'mouseOut',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'create_queue_boxes', 'queueLeft', 'queueRight', 'mouseOut', 'mouseEnter');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
			this.collection.bind('remove', this.remove);
			this.queue_indices = []
			this.overflow = false
		},

		create_queue_boxes: function(collection, positions) {
			var html = '<i class="icon-chevron-left icon-3x profile-chevron" id="queue-chevron-left"></i>'
				for (var i = 0; i < collection.queue_indices.length; i++) {
					html += '<div class="queue-position">'
					html += "<div class='queue-position-position'>" + positions[collection.queue_indices[i]].title + "</div>"
					if (positions[collection.queue_indices[i]].title.length > 25) html += "<br/>"
					else html += "<br/><br/>"
					html += "<div class='queue-position-entity'>" + positions[collection.queue_indices[i]].entity_name + "</div>"
					// html += '<div class="queue-position-position">Position: '
					// html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].title + '</span></div>' 
					// html += '<div class="queue-position-entity">Company: '
					// html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].entity_name + '</span></div>'
					// // html += '<div class="queue-position-owner">Position Owner: '
					// html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].owner + '</span></div>'
					html += '</div>'
				}
			html += '<i class="icon-chevron-right icon-3x profile-chevron" id="queue-chevron-right"></i>'
			$(collection.$el).html(html)
		},

		render: function() {

			// Add text to header
			$('#queue-header').html('Positions of Interest')

			var collection = this // important! (context)

			this.collection.each(function(queueItem) {
				var positions = queueItem.attributes['positions']
				collection.num_positions = positions.length
				collection.positions = positions

				if (positions.length > 4) {
					for (var m = 0; m < 4; m++) collection.queue_indices.push(m)
					collection.overflow = true
				} else {
					for (var j = 0; j < positions.length; j++) collection.queue_indices.push(j)
				}

				// console.log(positions)
				collection.create_queue_boxes(collection, positions)
			});

			return this;
		},

		remove: function(ev) {
			_gaq.push(['_trackEvent', 'savedPaths', 'removePosition', 'single'])

			var self = this.collection

			// Grab path_id from the url (route)
			var path_id = Backbone.history.fragment.split('=')[1]

			// Parse pos_id from the id of the clicked element
			var pos_id = $(ev.target).parent().attr('id')
			pos_id = pos_id.split('-')[1].split(':')[1]

			$.post('/saved_paths/remove/', {path_id: path_id, pos_id: pos_id, 
				}, function(response) {
					if (response['success']) {
						// manually refresh?
						self.fetch()
						self.reset()
					} else {
						console.log('removal failed...')
					}
				}, 'json');
		},

		queueLeft: function(ev) {
			if (this.overflow) {
				console.log('Left: ' + this.queue_indices)
				console.log('Num Pos: ' + this.num_positions)

				for (var n = 0; n < this.queue_indices.length; n++) {
					if (this.queue_indices[n] == 0) this.queue_indices[n] = this.num_positions - 1
					else this.queue_indices[n] -= 1
				}
				this.create_queue_boxes(this, this.positions)
			}

		},

		queueRight: function(ev) {
			if (this.overflow) {
				console.log('Right: ' + this.queue_indices)
				console.log('Num Pos: ' + this.num_positions)

				for (var q = 0; q < this.queue_indices.length; q++) {
					if (this.queue_indices[q] == (this.num_positions - 1)) this.queue_indices[q] = 0
					else this.queue_indices[q] += 1				
				}
				this.create_queue_boxes(this, this.positions)
			}
		},

		mouseEnter: function(ev) {
			if (!$(ev.currentTarget).hasClass('queue-position-hover'))
				$(ev.currentTarget).toggleClass('queue-position-hover')
		},

		mouseOut: function(ev) {
			if ($(ev.currentTarget).hasClass('queue-position-hover'))
				$(ev.currentTarget).removeClass('queue-position-hover')
		},

	});



	//---------------//
	// ** Routers ** //
	//---------------//
	window.ProfileRouter = Backbone.Router.extend({
		routes: {
			'':'empty',
		},

		initialize: function() {
			this.queue = window.queue;
			this.goalCareers = window.goalCareers;
		},

		// Note... this is going to fetch even when not your profile...
		empty: function() {
			this.goalCareerView = new GoalCareerView({collection:this.goalCareers})
			this.queueView = new QueueListView({collection:this.queue})
			queue.fetch()
		},

		
		
	});


	window.App = new ProfileRouter();
	
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



