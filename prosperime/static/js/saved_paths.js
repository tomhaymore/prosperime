
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

		url: function() {
			return '/prototype/';
		},

	});

	window.PositionData2 = Backbone.Collection.extend({
		model: PositionData,

		initialize: function() {
			this._meta = {}
		},

		url: function() {
			return '/prototype_data' + this.meta['query']
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


	})


	// Instantiate Collections
	window.savedPaths = new SavedPaths;
	window.proto = new PositionDataCollection;
	window.pdata = new PositionData2;

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

		},

		hoverOn: function(ev) {
			$(ev.target).children().each(function() {
				$(this).css('visibility', 'inherit')
			});
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
		},

		initialize: function() {
			_.bindAll(this,'render');
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
			if ($(ev.currentTarget).attr('id') === undefined) {
				// then create a new path
			} else {
				var path_id = $(ev.currentTarget).attr('id')
				window.App.navigate('id/?id=' + path_id, {trigger:true});
			}
		},

		hoverIn: function(ev) {
			$(ev.currentTarget).toggleClass('thumbnail-hover');
		},

		hoverOut: function(ev) {
			$(ev.currentTarget).toggleClass('thumbnail-hover');
		},
 
	});


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
			this.proto = window.proto;
			this.pdata = window.pdata;
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
			this.protoView = new ProtoView({collection: this.proto});
			this.proto.fetch()
		},

		getPositionData: function(query) {
			this.pdata.meta('query', query);
			console.log(query)
			// this.pdata.fetch();
		},

	});


	window.App = new SavedPathRouter();
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



