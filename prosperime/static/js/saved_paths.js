
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.SavedPath = Backbone.Model.extend({
		// ??
	});

	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.SavedPaths = Backbone.Collection.extend({

		// initializing the dst for the query?? 
		initialize: function() {
			this._meta = {}
		},

		model: SavedPath,
		// seems to be setting the url based off the query in the router
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/saved';
			} else {
				return '/saved/'+ this._meta['query'];
			}
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

	// Instantiate Collections
	window.savedPaths = new SavedPaths;

	//-------------//
	// ** Views ** //
	//-------------//
	window.SavedPathSingleView = Backbone.View.extend({
		tagname:"li",
		template:_.template($('#saved-path-single-template').html()),

		// no events

		initialize: function() {
			this.model.on('change', this.render, this); // no idea
		},

		render: function() {
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}
	});

	window.SavedPathListView = Backbone.View.extend ({

		el: $("#saved-paths-list"),
		tag: 'div',
		template: _.template($("#saved-path-list-template").html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			var $savedPaths,
				collection = this.collection;

			$(this.el).html(this.template({}));
			$savedPaths = this.$(".path-list");
			this.collection.each(function(savedPath) {
				var view = new SavedPathSingleView({
					model: savedPath,
					collection: collection
				});
				$savedPaths.append(view.render().el);
			});
			return this;
		},
	});

	

	//---------------//
	// ** Routers ** //
	//---------------//
	window.SavedPathRouter = Backbone.Router.extend({
		routes: {
			"" : "emptySavedPathSearch",
			"title/:query" : "savedPathSearch",
		},

		initialize: function() {
			this.savedPaths = window.savedPaths;
			this.savedPathsView = new SavedPathListView({collection: this.savedPaths});
			console.log('initalized')
		},

		emptySavedPathSearch: function() {
			console.log('in backbone, show all paths')
			// this.savedPaths.meta('query', '');
			this.savedPaths.fetch();
		},

		savedPathSearch: function(query) {
			console.log('in backbone, show single path: ' + query);
			this.savedPaths.meta('query', query);
			this.savedPaths.fetch();
		},
	});


	// Custom functions
	function generateUrl(params) {
		var fullUrl = '';
		c = 0;
		for (var key in params) {
			if (params.hasOwnProperty(key)) {
				for (i=0;i<=params[key].length;i++) {
					if(params[key][i] === undefined) {
						continue;
					} else {
						if (i == 0 && c == 0) {
							fullUrl += key + "=" + encodeURIComponent(params[key][i]);
						} else if (i == 0) {
							fullUrl += "&" + key + "=" + encodeURIComponent(params[key][i]);
						 } // else {
						// 	fullUrl += "+'" + encodeURIComponent(params[key][i]) + "'";
						// }
					}
				}
			}
			c++;
		}
		return fullUrl;
	}

	window.App = new SavedPathRouter;
	Backbone.history.start();
});



