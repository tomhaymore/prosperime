
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.QueuedPosition = Backbone.Model.extend({
		// nothing... is this even needed?
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

	//-------------//
	// ** Views ** //
	//-------------//


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
			'click #left-chevron':'queueLeft',
			'click #right-chevron':'queueRight',
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
			var html = '<i class="icon-chevron-left icon-3x profile-chevron" id="left-chevron"></i>'
				for (var i = 0; i < collection.queue_indices.length; i++) {
					html += '<div class="queue-position">'
					html += '<div class="queue-position-position">Position: '
					html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].title + '</span></div>' 
					html += '<div class="queue-position-entity">Company: '
					html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].entity_name + '</span></div>'
					html += '<div class="queue-position-owner">Position Owner: '
					html += '<span class="queue-position-title">' + positions[collection.queue_indices[i]].owner + '</span></div>'
					html += '</div>'
				}
			html += '<i class="icon-chevron-right icon-3x profile-chevron" id="right-chevron"></i>'
			$(collection.$el).html(html)
		},

		render: function() {
			var collection = this // important! (context)

			this.collection.each(function(queueItem) {
				var positions = queueItem.attributes['positions']
				collection.num_positions = positions.length
				collection.positions = positions

				if (positions.length > 4) {
					for (var m = 0; m < 4; m++) collection.queue_indices.push(m)
					collection.overflow = true
				} else {
					for (var j = 0; j < positions.length; j++) collection.queue_indices.push(i)
				}

				console.log(positions)
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
			// this.savedPaths = window.savedPaths;
			// this.savedPaths.bind('remove', this.remove)
		},

		// Note... this is going to fetch even when not your profile...
		empty: function() {
			this.queueView = new QueueListView({collection:this.queue})
			queue.fetch()

		},

		
		
	});


	window.App = new ProfileRouter();
	
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



