
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.SavedPath = Backbone.Model.extend({
		// ??
	});

	window.PositionData = Backbone.Model.extend({
		// 
	});

	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.SavedPaths = Backbone.Collection.extend({

		urlRoot: '/saved/',
		model: SavedPath, 

		comparator: function(collection) {
			return(collection.get('index'))
		},

		initialize: function() {
			this._meta = {}
		},

		url: function() {	
			return '/saved/'+ this._meta['query'];
		},

		// no idea ??
		meta: function(prop, value) {
			if (value === undefined) {
				// if value is empty, return property of key
				return this._meta[prop];
			} else {
				// if both key and value exist, set value of key
				this._meta[prop] = value;
			}
		}
	});

	window.PositionDataCollection = Backbone.Collection.extend({
		model: PositionData,

		initialize: function() {
			this._meta = {}
		},

		url: function() {
			return '/prototype/' + this._meta['query']
		},

		meta: function(prop, value) {
			if (value === undefined) {
				// if value is empty, return property of key
				return this._meta[prop];
			} else {
				// if both key and value exist, set value of key
				this._meta[prop] = value;
			}
		},
	});

	// Instantiate Collections
	window.savedPaths = new SavedPaths;
	window.positionData = new PositionDataCollection;

	//-------------//
	// ** Views ** //
	//-------------//

	// Renders the title @ the top of the page
	window.HeaderView = Backbone.View.extend({

		// Ultimately, will want to get logic out of here, but this
		// works for now
		template: _.template("<span class='blue'>Career Path: </span><%= this.model.get('title')%>"),
		model: SavedPath,
		tagName: 'span',

		render:function() {
			var content = this.template(this.model.toJSON())
			this.$el.empty();
			this.$el.html(content);
			return this;
		},
	});

	// Single Saved Path Single View
	window.SavedPathSingleView = Backbone.View.extend({
		template:_.template($('#saved-path-single-template').html()),

		events: {
			"click .saved-path-position":"positionClicked",	
			"mouseenter .saved-path-position":"hoverOn",	
			"mouseleave .saved-path-position":"hoverOut",
		},

		initialize: function() {
			this.model.on('change', this.render, this); 
			_.bindAll(this, 'render')
			this.model.bind('remove', this.remove)
		},

		render: function() {
			// for (var i = 0; i < this.model.get('positions').length; i++) {
			// 	console.log(this.model.get('positions')[i].title)
			// 	console.log(this.model.get('positions')[i].index)
			// }

			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},

		positionClicked: function(ev) {
			_gaq.push(['_trackEvent', 'savedPaths', 'positionClicked', 'single'])

		},

		hoverOn: function(ev) {
			$(ev.target).children().each(function() {
				$(this).css('visibility', 'inherit')
			});
			var elemId = $(ev.target).attr('id')
			var index = elemId.split('-')[0].split(':')[1]
			var infoId = 'description-' + elemId

			// Clear other meta
			$('.saved-path-timeline-info-item').each(function() {
				if (!$(this).hasClass('hide')) {
					$(this).toggleClass('hide')
				}
			});

			// don't know why, but jquery won't grab this
			var info_item = document.getElementById(infoId)
			$(info_item).toggleClass('hide')
		},

		hoverOut: function(ev) {
			$(ev.target).children().each(function() {
				$(this).css('visibility', 'hidden')
			});
		},
	});


	// Path list view for single path search... necessary??
	window.SavedPathListView = Backbone.View.extend ({

		el: $("#saved-paths-list"),
		tag: 'div',
		template: _.template($("#saved-path-list-template").html()),

		events: {
			"click .icon-remove-circle":"remove",
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'test');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
			this.collection.bind('remove', this.remove);
		},

		test: function() {
			console.log('A+')
		},

		render: function() {
			var $savedPaths = this.collection;

			$(this.el).html(this.template({}));
			$savedPaths = this.$(".path-list");

			var type = window.savedPaths.models[0].attributes['type']
			if (type == 'single') {
				$('#thumbnail-column-header').empty()
			} 


			// Single Path
			this.collection.each(function(savedPath) {
				var header = new HeaderView({
					model: savedPath,
				});
				$('#path-header').empty()
				$('#path-header').append(header.render().el)
			});

			this.collection.each(function(savedPath) {
				var view = new SavedPathSingleView({
					model: savedPath,
					collection:this.collection,
				});
			$savedPaths.append(view.render().el);
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

		

	});

	// Single thumbnail??
	window.SavedPathThumbnailSingleView = Backbone.View.extend({
		template:_.template($('#saved-path-thumbnail-single-template').html()),
		className: 'saved-path-thumbnail',

		initialize: function() {
			this.model.on('change', this.render, this); 
		},

		render: function() {
			var path_id = this.model.get('id')
			$(this.el).attr('id', path_id)
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},

	});

	// Thumbnail List View for empty searches
	window.SavedPathThumbnailListView = Backbone.View.extend({
		
		el: $("#saved-paths-list"),
		template: _.template($("#saved-path-thumbnail-list-template").html()),


		events: {
			"click .saved-path-thumbnail": "goToPath",
			"mouseenter .saved-path-thumbnail": "hoverIn",
			"mouseleave .saved-path-thumbnail": "hoverOut",
			"click a.delete-path": "deletePath",
		},

		initialize: function() {
			_.bindAll(this,'render', 'deletePath', 'rerender');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
		},

		render: function() {
			var $savedPaths = this.collection;

			$(this.el).html(this.template({}));
			$savedPaths = this.$(".saved-path-thumbnail-table");

			// Header
			var header = new HeaderView();
			$('#path-header').empty()
			$('#path-header').append('<span class="blue">Saved Career Paths</span>');
			
			// Admittedly, this is ghetto
			var type = window.savedPaths.models[0].attributes['type']
			if (type == 'all') {
				console.log('here')
				$('#thumbnail-column-header').empty();
				$('#thumbnail-column-header').append($('#thumbnail-column-header-template').html())
			} 

			// Single Thumbnail
			this.collection.each(function(savedPath) {
				var view = new SavedPathThumbnailSingleView({
					model:savedPath,
					collection:this.collection,
				});
				$savedPaths.append(view.render().el);

			});
		},

		goToPath: function(ev) {
			_gaq.push(['_trackEvent', 'savedPaths', 'goToPath', 'all'])

			if ($(ev.currentTarget).attr('id') === undefined) {
				// then create a new path
			} else {
				var path_id = $(ev.currentTarget).attr('id')
				window.App.navigate('id/?id=' + path_id, {trigger:true});
			}
		},

		hoverIn: function(ev) {
			$(ev.currentTarget).toggleClass('thumbnail-hover');
			// $(ev.currentTarget).children().each( function() {
			// 	if(!$(this).hasClass('thumbnail-title')) {
			// 		$(this).toggleClass('hide');
			// 	}
			// });
		},

		hoverOut: function(ev) {
			$(ev.currentTarget).toggleClass('thumbnail-hover');
			// $(ev.currentTarget).children().each( function() {
			// 	if(!$(this).hasClass('thumbnail-title')) {
			// 		$(this).toggleClass('hide');
			// 	}
			// });
		},

		deletePath: function(ev) {
			_gaq.push(['_trackEvent', 'savedPaths', 'deletePath', 'all'])
			ev.preventDefault();
			console.log('delete: ' + ev.currentTarget.id)

			$.post('/saved_paths/remove/', {type:'path', path_id:ev.currentTarget.id}, function(response) {
				console.log(response)
				window.savedPaths.fetch()
				
			});

			return false;
		},

		rerender: function() {
			this.reset()
		},
 
	});

	/* ########################## */
	/* ####### Proto Views ###### */
	/* ########################## */

	window.ProtoView = Backbone.View.extend({
		el: $('#saved-paths-list'),
		template:_.template($('#proto-template').html()),

		events: {
			'change #proto-fill':'elemSelected',
		},

		initialize: function() {
			_.bindAll(this,'render', 'elemSelected');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
		},

		render: function() {

			$(this.el).html(this.template({}));
			console.log('gets to initial list view')
			// At some point, uniqify
			// this.collection = _.uniq(this.collection, false, function(pos) {
			// 	return pos.attributes[0]['title']
			// });
			this.collection.each(function(model) {
				var view = new ProtoSingleView({
					model:model,
					collection:this.collection,
				});
				this.$('#proto-fill').append(view.render().el);
			});
		},

		elemSelected:function(ev) {
			var pos_id = $(ev.currentTarget).find(':selected').attr('id')
			window.App.navigate('pos/?pos=' + pos_id, {trigger:true});
		},

	});

	window.ProtoSingleView = Backbone.View.extend({
		tagName: 'option',
		template:_.template('<option><%=this.model.attributes[0]["title"]%></option>'),
		className: 'pos-select',

		events: {
			'click .pos-select':'posClicked',
		},

		initialize: function() {
			this.model.on('change', this.render, this); 
			_.bindAll(this, 'render', 'posClicked');
		},

		render: function() {
			var renderedContent = this.template(this.model.get('positions'));
			$(this.el).attr('id', this.model.attributes[0]['id']);
			$(this.el).html(renderedContent);
			return this;
		},

		posClicked:function(ev) {
			console.log('clicked')
			console.log(ev.currentTarget.id)
		},
	});


	window.ProtoDataView = Backbone.View.extend({
		el: $('#saved-paths-list'),
		template:_.template($('#proto-single-template').html()),


		initialize: function() {
			_.bindAll(this,'render');
			this.collection.on('reset',this.render, this, function() {
				this.render()
			});
			this.collection.on('change', this.render, this);
		},

		render: function() {
			console.log('gets to second list view')
			// console.log(this.collection.toJSON())
			//$(this.el).html(this.template(this.collection.toJSON()));
			// console.log('gets 2 here')
	
			return this;

			// this.collection.each(function(model) {
			// 	var view = new ProtoSingleView({
			// 		model:model,
			// 		collection:this.collection,
			// 	});
			// 	this.$('#proto-fill').append(view.render().el);
			// });
		},
	});

	//---------------//
	// ** Routers ** //
	//---------------//
	window.SavedPathRouter = Backbone.Router.extend({
		routes: {
			"" : "emptySavedPathSearch",
			"id/:query" : "savedPathSearch",
			"proto" : "prototype",
			"pos/:query": "getPositionData",
		},

		initialize: function() {
			this.savedPaths = window.savedPaths;
			this.savedPaths.bind('remove', this.remove)
			this.headerView = new HeaderView()
			this.proto = window.positionData;
		},

		emptySavedPathSearch: function() {
			this.savedPathsView = new SavedPathThumbnailListView({collection: this.savedPaths});
			this.savedPaths.meta('query', '');
			this.savedPaths.fetch()
		},

		savedPathSearch: function(query) {
			this.savedPathsView = new SavedPathListView({collection: this.savedPaths});
			this.savedPaths.meta('query', query);
			this.savedPaths.fetch();
		},

		prototype: function(query) {
			this.proto.meta('query', '')
			this.protoView = new ProtoView({collection: this.proto});
			this.proto.fetch()
		},

		getPositionData: function(query) {
			this.secondView = new ProtoDataView({collection: this.proto})
			this.proto.meta('query', query);
			this.proto.fetch();
			console.log('after fetch')
		},

	});


	window.App = new SavedPathRouter();
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



