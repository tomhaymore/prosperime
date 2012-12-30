
// kick off app once DOM is ready

$(function(){

	// Models

	// Filter: dynamically loaded search param

	window.Filter = Backbone.Model.extend({


	});

	// Org: search result form for organizations

	window.Org = Backbone.Model.extend({

	});

	// Path: search result view for career paths

	window.Path = Backbone.Model.extend({

	});

	// Collections

	// Filters: collection of filters

	window.Filters = Backbone.Collection.extend({

		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		},

		model:Filter,
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/filters';
			} else {
				console.log(this._meta['query']);
				path = '/filters/?' + this._meta['query'];
				console.log(path);
				return '/filters/' + this._meta['query'];
			}
		},

		meta: function(prop, value) {
			if (value === undefined) {
				// if value is empty, return property of key
				return this._meta[prop];
			} else {
				// if both key and value exist, set value of key
				this._meta[prop] = value;
			}
		}
	})

	// Orgs: collection of orgs

	window.Orgs = Backbone.Collection.extend({

		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		},

		model: Org,
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/companies';
			} else {
				return '/companies'+this._meta['query'];
			}
		},

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

	// Paths: collection of paths

	window.Paths = Backbone.Collection.extend({
		
		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		},

		model: Path,
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/paths';
			} else {
				return '/paths'+this._meta['query'];
			}
		},

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

	// instantiate collections

	window.orgs = new Orgs;
	window.filters = new Filters;
	window.paths = new Paths;

	// Views

	window.PathSingleView = Backbone.View.extend({

		tagName: "li",

		template:_.template($('#path-single-template').html()),

		initialize: function() {
			this.model.on('change',this.render,this);
			
		},

		render: function() {
			
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}

	});

	window.OrgSingleView = Backbone.View.extend({

		// tag: "div",

		template:_.template($('#org-single-template').html()),

		initialize: function() {
			this.model.on('change',this.render,this);
			//this.template = _.template($('#org-single-template').html())
		},

		render: function() {
			// var renderedContent = $(this.el).html(this.template(this.model.toJSON()));
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}

	});

	window.PathListView = Backbone.View.extend({

		el: $('#search-results-list'),
		tag: 'div',
		template: _.template($('#path-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			var $paths,
				collection = this.collection;

			$(this.el).html(this.template({}));
			$paths = this.$(".path-list");
			this.collection.each(function(path) {
				var view = new PathSingleView({
					model: path,
					collection: collection
				});
				$paths.append(view.render().el);
			});
			return this;
		}
	});

	window.OrgListView = Backbone.View.extend({
		
		//el: $('#org-list'),
		el: $('#search-results-list'),
		tag: "div",
		template: _.template($('#org-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
			// this.template = _.template($('#org-list-template').html());
		},

		render: function() {
			var $orgs,
				collection = this.collection;

			$(this.el).html(this.template({}));
			$orgs = this.$(".org-list");
			this.collection.each(function(org) {
				var view = new OrgSingleView({
					model: org,
					collection: collection
				});
				$orgs.append(view.render().el);
			});
			return this;
		}
	});

	window.FilterSingleView = Backbone.View.extend ({
		tagName: 'li',
		template: _.template($("#search-filters-template").html()),

		initialize: function() {
			this.model.on('change',this.render,this);
		},

		render: function() {
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},

		events: {
			"click input.input-search-filter" : "filter"
		},

		filter: function() {
			// create dict of all selected filters
			var selectedFilters = {};

			var locationFilters = $("input[name='Location-filters']:checked").map(function(filter) { return this.value });
			var sectorFilters = $("input[name='Sector-filters']:checked").map(function(filter) { return this.value });
			var sizeFilters = $("input[name='Size-filters']:checked").map(function(filter) { return this.value });
			var stageFilters = $("input[name='Stage-filters']:checked").map(function(filter) { return this.value });
			
			// construct URL

			if (locationFilters.length > 0 ) {
				selectedFilters.location = locationFilters;
			}
			if (sectorFilters.length > 0) {
				selectedFilters.sector = sectorFilters;				
			}
			if (sizeFilters.length > 0) {
				selectedFilters.size = sizeFilters;
			}
			if (stageFilters.length > 0) {
				selectedFilters.stage = stageFilters;
			}
			
			if (jQuery.isEmptyObject(selectedFilters)) {
				filterUrl = '/search/';
			} else {
				filterUrl = "/search/?" + generateUrl(selectedFilters);
			}

			// trigger router to navigate
			console.log("trying to trigger search");
			//Backbone.history.navigate(filterUrl,{trigger:true});
			App.navigate(filterUrl,{trigger:true});

		}
	});

	window.FilterListView = Backbone.View.extend ({

		el: $("#search-container"),
		tagName: 'div',
		template: _.template($("#search-module-template").html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);

		},

		events: {
			"click a.search-control-close" : "minimize",
			"click a.search-control-open" : "maximize"
		},

		render: function() {
			var $filters,
				filterCategories,
				collection = this.collection;

			$(this.el).empty();
			$(this.el).append(_.template($("#search-header-template").html()));
			
			// pull out unique list of categories
			categories = filters.map(function(model) { return model.get('category'); });
			categories = _.uniq(categories);
			for (var i = 0; i < categories.length; i++) { 
				category = categories[i];
				//console.log(category);
				// render collection view with appropriate category variable
				$(this.el).append(this.template({'category':category}));
				// assign comtainer for models to a jQuery object
				$filters = this.$(".filters-list:last");
				// loop through each model in the collection
				this.collection.each(function(filter) {
					// only render filters from this category

					if (filter.get('category') == category) {
						// console.log(filter.get('category'));
						var view = new FilterSingleView({
							model: filter,
							collection: collection
						});
						$filters.append(view.render().el);
					}
				});
			}
			return this;
		},

		// uncheck all filters

		uncheckAll: function() {
			$filters = this.$(".input-search-filter");
			$filters.prop('checked',false);
		},

		minimize: function() {
			$("div#sidebar-column").removeClass("span3").addClass("span1");
			$("div#main-column").removeClass("span6").addClass("span8");
			$("a.search-control-close").hide();
			$("a.search-control-open").show();
		},

		maximize: function() {
			$("div#sidebar-column").removeClass("span1").addClass("span3");
			$("div#main-column").removeClass("span8").addClass("span6");
			$("a.search-control-close").show();
			$("a.search-control-open").hide();
		}

	});

	window.SearchRouter = Backbone.Router.extend({

		routes: {
			"" : "home",
			"search/" : "emptySearch",
			"search/:query" : "search"
		},

		initialize: function() {
			this.orgs = window.orgs;
			this.filters = window.filters;
			this.paths = window.paths;
			this.orgsView = new OrgListView({ collection: this.orgs});
			this.filtersView = new FilterListView({ collection: this.filters});
			this.pathsView = new PathListView({ collection: this.paths});
		},

		home: function() {
			console.log("stay home");
			// this.orgs.fetch();
			this.filters.fetch();
			this.paths.fetch();
		},

		emptySearch: function() {
			console.log('empty search');
			this.orgs.meta('query','');
			this.filters.meta('query','');
			this.orgs.meta('query','');
			this.orgs.fetch();
			this.filters.fetch();
			this.paths.fetch();
		},

		search: function(query) {
			console.log("search triggered");
			console.log(query);
			// test for empty search string, make sure to uncheck all filters
			if (query === undefined) {
				this.filtersView.uncheckAll();
				this.orgs.meta('query',null);
				this.filters.meta('query',null);
			} else {
				this.orgs.meta('query',query);
				this.filters.meta('query',query);	
			}
			this.orgs.fetch();
			this.filters.fetch();
		}

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

	window.App = new SearchRouter;
	Backbone.history.start();


});



